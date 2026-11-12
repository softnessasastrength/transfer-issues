"""Read-only database boundary and date-aware schedule queries."""
import sqlite3, pathlib, os, datetime, functools, json
ROOT=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(os.environ.get('ATLAS_DATA_DIR',ROOT/'data'))
def connect():
 d=sqlite3.connect(f'file:{DATA / "atlas.sqlite"}?mode=ro',uri=True);d.row_factory=sqlite3.Row;return d

def query(sql,args=()):
 with connect() as d:return [dict(r) for r in d.execute(sql,args)]

def active_services(day):
 date=datetime.date.fromisoformat(day);key=date.strftime('%Y%m%d')
 services={r['service'] for r in query('SELECT * FROM calendar WHERE start<=? AND end>=?',(key,key)) if r['days'][date.weekday()]=='1'}
 for r in query('SELECT * FROM exceptions WHERE date=?',(key,)):
  if r['type']==1:services.add(r['service'])
  else:services.discard(r['service'])
 return services

@functools.lru_cache(maxsize=12)
def connections(day):
 """Service-day seconds, including previous-day 24+ hours and next-day departures."""
 result=[];date=datetime.date.fromisoformat(day)
 with connect() as d:
  for offset in [-1,0,1]:
   sd=(date+datetime.timedelta(days=offset)).isoformat();services=active_services(sd)
   for service in services:
    for r in d.execute('''SELECT a.stop,b.stop,a.dep,b.arr,t.id,t.route,t.headsign,a.pickup,b.dropoff,a.seq
      FROM trips t JOIN times a ON a.trip=t.id JOIN times b ON b.trip=t.id AND b.seq=a.seq+1
      WHERE t.service=?''',(service,)):
     a,b,dep,arr,trip,route,head,pu,do,seq=r;dep+=offset*86400;arr+=offset*86400
     if arr>=0 and dep<=172800:result.append((dep,arr,a,b,sd+'|'+trip,route,head,pu,do,seq))
 result.sort(key=lambda x:(x[0],x[9]));return result

def sources():return json.loads((DATA/'sources.json').read_text())

def coverage(day):
 key=day.replace('-','');return [{'feed':s['id'],'status':s['status'],'in_service_period':s.get('service_start','99999999')<=key<=s.get('service_end','00000000'),'start':s.get('service_start'),'end':s.get('service_end')} for s in sources()]

def departures(stop,day,route=''):
 seen=set();out=[]
 for dep,arr,a,b,trip,r,head,pu,do,seq in connections(day):
  if a!=stop or pu!=0 or dep<0 or dep>=86400 or (route and r!=route) or (trip,seq) in seen:continue
  seen.add((trip,seq));out.append(dict(departure=dep,trip=trip,route=r,headsign=head,source=r.split(':')[0]))
 return out
