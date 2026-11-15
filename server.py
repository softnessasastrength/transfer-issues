"""Loopback HTTP development server; API contract in API.md."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import argparse,datetime,json,pathlib,os
import database as db
import routing
import bubble as bubble_mod
import fares
ROOT=pathlib.Path(__file__).resolve().parent
CITIES=[('Hartford',41.7658,-72.6734),('Springfield',42.106,-72.593),('Enfield',41.998,-72.585),('Windsor Locks',41.929,-72.627),('Manchester',41.776,-72.521),('Holyoke',42.204,-72.617),('Chicopee',42.148,-72.608),('Westfield',42.125,-72.750),('New Haven',41.298,-72.925),('Worcester',42.261,-71.795),('Providence',41.824,-71.413)]

def arg(q,k,default=''):return q.get(k,[default])[0]
def number(q,k,default,lo,hi):
 n=int(arg(q,k,str(default)))
 if not lo<=n<=hi:raise ValueError(k+' out of range')
 return n

def planning_feeds(q):
 requested=tuple(filter(None,arg(q,'feeds').split(',')))
 if requested or arg(q,'include_optional','0')=='1':return requested
 return tuple(s['id'] for s in db.sources() if not s.get('optional'))

def dated(q):
 d=arg(q,'date',datetime.date.today().isoformat());datetime.date.fromisoformat(d);return d

def warm_caches(day=None):
 """Build the network and selected service-day cache before listening."""
 day=day or os.environ.get('ATLAS_DATE',datetime.date.today().isoformat())
 datetime.date.fromisoformat(day)
 routing.network()
 db.connections(day)
 return day

def handle(path,q):
 if path=='/api/v1/meta':return dict(api_version='1.0',sources=db.sources(),cities=CITIES,routes=db.query('SELECT * FROM routes ORDER BY feed,short'),stops=db.stops(),station_codes='Amtrak CT/MA codes from config/station_codes.json',limitations=['Scheduled service, not live arrivals','Estimated geographic transfers; no street, slope or scooter-carry verification','Incomplete three-state agency coverage; not every agency is loaded','Amtrak regional clip; selected MBTA coverage follows config/coverage.json','Scoped GTFS transfer rules not modeled; verify station transfers'])
 if path=='/api/v1/coverage':return db.coverage(dated(q))
 if path=='/api/v1/departures':return dict(date=dated(q),departures=db.departures(arg(q,'stop'),dated(q),arg(q,'route')),coverage=db.coverage(dated(q)))
 if path=='/api/v1/stops':return db.search_stops(arg(q,'q'),arg(q,'feed'),number(q,'limit',50,1,500))
 if path=='/api/v1/pdf-schedules':return db.pdf_schedules(arg(q,'document'))
 if path=='/api/v1/fares':
  origin=arg(q,'from');destination=arg(q,'to');names=db.query('SELECT id,name FROM stops WHERE id IN (?,?)',(origin,destination));name_map={x['id']:x['name'] for x in names}
  if arg(q,'route','') not in ('','hartford:HART'):return {'status':'unknown','reason':'Only direct CTrail Hartford Line fares are currently supported.'}
  return fares.hartford_line_fare(name_map.get(origin,''),name_map.get(destination,''))
 if path=='/api/v1/route':
  route=arg(q,'id');trips=db.query('SELECT * FROM trips WHERE route=?',(route,));active=db.active_services(dated(q));trips=[t for t in trips if t['service'] in active]
  shapes={};
  for t in trips:
   if t['shape'] not in shapes:
    pts=db.query('SELECT lat,lon FROM shapes WHERE id=? ORDER BY seq',(t['shape'],));shapes[t['shape']]=[[p['lat'],p['lon']] for p in pts]
  stops=db.query('SELECT DISTINCT s.* FROM stops s JOIN times st ON st.stop=s.id JOIN trips t ON t.id=st.trip WHERE t.route=?',(route,))
  patterns={}
  for t in trips:
   key=(t['direction'],t['headsign']);patterns.setdefault(key,[]).append(t)
  comparison=[];base=datetime.date.fromisoformat(dated(q))
  for label,weekday in [('Weekday',0),('Saturday',5),('Sunday',6)]:
   dt=base+datetime.timedelta(days=(weekday-base.weekday())%7);sv=db.active_services(dt.isoformat());count=db.query('SELECT service,COUNT(*) n FROM trips WHERE route=? GROUP BY service',(route,));comparison.append(dict(label=label,date=dt.isoformat(),trips=sum(x['n'] for x in count if x['service'] in sv)))
  return dict(shapes=list(shapes.values()),stops=stops,trips=trips,comparison=comparison,source=route.split(':')[0],geometry='Official GTFS shape where present; no line invented when absent')
 if path=='/api/v1/trip':
  tid=arg(q,'id');tid=tid.split('|')[-1];return db.query('SELECT st.*,s.name,s.lat,s.lon FROM times st JOIN stops s ON s.id=st.stop WHERE trip=? ORDER BY seq',(tid,))
 if path=='/api/v1/bubble':
  day=dated(q);origin=arg(q,'from');start=number(q,'time',28800,0,86399)
  mode=arg(q,'mode','walk')
  if mode not in ['walk','scooter']:raise ValueError('Unknown ground mode')
  return bubble_mod.classify(day,origin,start,budget=number(q,'budget',3600,60,14400),visit=number(q,'visit',0,0,86400),mode=mode,radius=number(q,'radius',500,0,3000),buffer=number(q,'buffer',300,0,3600),feeds=planning_feeds(q),coverage_rows=db.coverage(day),source_rows=db.sources())
 if path in ['/api/v1/plan','/api/v1/reachability']:
  day=dated(q);origin=arg(q,'from');start=number(q,'time',28800,0,86399);deadline=number(q,'deadline',86399,start,172799)
  mode=arg(q,'mode','walk')
  if mode not in ['walk','scooter']:raise ValueError('Unknown ground mode')
  opts=dict(mode=mode,radius=number(q,'radius',500,0,3000),buffer=number(q,'buffer',300,0,3600),feeds=planning_feeds(q))
  if path.endswith('reachability'):
   arr,paths=routing.scan(day,origin,start,deadline,**opts);stops=routing.network()[0]
   return dict(stops=[dict(id=k,arrival=v,lat=stops[k]['lat'],lon=stops[k]['lon']) for k,v in arr.items()],coverage=db.coverage(day))
  dest=arg(q,'to');kind=arg(q,'kind','depart');fn=routing.latest if kind=='latest' else routing.plan
  result=fn(day,origin,dest,start,deadline,**opts)
  if result.get('found'):
   ids={leg[k] for leg in result.get('legs',[]) for k in ('from_stop','to_stop') if k in leg};names={x['id']:x['name'] for x in db.query('SELECT id,name FROM stops WHERE id IN ('+','.join('?' for _ in ids)+')',tuple(ids))} if ids else {};route_ids={leg.get('route') for leg in result.get('legs',[]) if leg.get('route')};route_rows=db.query('SELECT id,short,type,agency FROM routes WHERE id IN ('+','.join('?' for _ in route_ids)+')',tuple(route_ids)) if route_ids else [];result['fare']=fares.for_plan(result,names,{x['id']:x for x in route_rows})
  if arg(q,'return')=='1' and result['found']:
   ready=result['arrival']+number(q,'visit',3600,0,86400)
   if ready<=deadline:
    result['return']=routing.plan(day,dest,origin,ready,deadline,**opts);result['return']['fare']=fares.for_plan(result['return'],names,{x['id']:x for x in route_rows});result['latest_return']=routing.latest(day,dest,origin,ready,deadline,**opts)
   else:result['return']={'found':False,'message':'Visit ends after the selected return deadline.'}
  return result
 raise LookupError('Unknown API endpoint')

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
 def do_GET(self):
  parsed=urlparse(self.path)
  if parsed.path.startswith('/api/'):
   try:result=handle(parsed.path,parse_qs(parsed.query));status=200
   except (ValueError,KeyError) as e:result={'error':str(e)};status=400
   except LookupError as e:result={'error':str(e)};status=404
   except Exception as e:
    import traceback;traceback.print_exc();result={'error':'Server error; see local server log'};status=500
   data=json.dumps(result,separators=(',',':')).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  else:super().do_GET()
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=int(os.environ.get('PORT','8000')));a=p.parse_args()
 day=os.environ.get('ATLAS_DATE',datetime.date.today().isoformat())
 print(f'Transit Atlas: warming caches for {day}...',flush=True)
 warm_caches(day)
 print(f'Transit Atlas: http://{a.host}:{a.port}',flush=True);ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
