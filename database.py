"""Read-only database boundary and date-aware schedule queries."""
import sqlite3, pathlib, os, datetime, functools, json
from contextlib import closing
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
DATA=pathlib.Path(os.environ.get('ATLAS_DATA_DIR',ROOT/'data'))
STATION_CODES=json.loads((ROOT/'config'/'station_codes.json').read_text())
def connect():
 d=sqlite3.connect(f'file:{DATA / "atlas.sqlite"}?mode=ro',uri=True);d.row_factory=sqlite3.Row;return d

def query(sql,args=()):
 with closing(connect()) as d:return [dict(r) for r in d.execute(sql,args)]

def active_services(day):
 date=datetime.date.fromisoformat(day);key=date.strftime('%Y%m%d')
 services={r['service'] for r in query('SELECT * FROM calendar WHERE start<=? AND end>=?',(key,key)) if r['days'][date.weekday()]=='1'}
 for r in query('SELECT * FROM exceptions WHERE date=?',(key,)):
  if r['type']==1:services.add(r['service'])
  else:services.discard(r['service'])
 return services

@functools.lru_cache(maxsize=64)
def service_anchor(day, timezone):
 """GTFS seconds start at agency-local noon minus 12 elapsed hours."""
 noon=datetime.datetime.combine(datetime.date.fromisoformat(day),datetime.time(12),ZoneInfo(timezone))
 return int(noon.timestamp())-43200

@functools.lru_cache(maxsize=12)
def connections(day):
 """Service-day seconds, including previous-day 24+ hours and next-day departures."""
 result=[];date=datetime.date.fromisoformat(day);query_anchor=service_anchor(day,'America/New_York')
 with closing(connect()) as d:
  if 'ordinal' not in {row['name'] for row in d.execute('PRAGMA table_info(times)')}:
   raise RuntimeError('Atlas database uses the old stop adjacency format; rebuild from downloaded GTFS archives before routing.')
  timezone_column='timezone' in {row['name'] for row in d.execute('PRAGMA table_info(trips)')}
  timezone_sql='t.timezone' if timezone_column else "'America/New_York'"
  for offset in [-1,0,1]:
   sd=(date+datetime.timedelta(days=offset)).isoformat();services=active_services(sd)
   for service in services:
    for r in d.execute(f'''SELECT a.stop,b.stop,a.dep,b.arr,t.id,t.route,t.headsign,a.pickup,b.dropoff,a.ordinal,{timezone_sql}
      FROM trips t JOIN times a ON a.trip=t.id JOIN times b ON b.trip=t.id AND b.ordinal=a.ordinal+1
      WHERE t.service=?''',(service,)):
     a,b,dep,arr,trip,route,head,pu,do,seq,timezone=r
     shift=service_anchor(sd,timezone)-query_anchor;dep+=shift;arr+=shift
     if arr>=0 and dep<=172800:result.append((dep,arr,a,b,sd+'|'+trip,route,head,pu,do,seq))
 result.sort(key=lambda x:(x[0],x[9]));return result

def sources():return json.loads((DATA/'sources.json').read_text())

def annotate_stop(stop):
 code=STATION_CODES.get(stop.get('id'))
 if code:return {**stop,'station_code':code['code'],'station_state':code['state'],'station_label':code['label']}
 return stop

def stops():return [annotate_stop(s) for s in query('SELECT * FROM stops')]

def coverage(day):
 key=day.replace('-','');return [{'feed':s['id'],'status':s['status'],'in_service_period':s.get('service_start','99999999')<=key<=s.get('service_end','00000000'),'start':s.get('service_start'),'end':s.get('service_end')} for s in sources()]

def search_stops(text,feed='',limit=50):
 """Case-insensitive substring search over loaded stop names.

 Only rows present in the stops table can match; nothing is invented.
 An empty query returns an honest empty result rather than every stop.
 LIKE wildcards in the query are escaped so they match literally.
 Results list prefix matches first, then alphabetical order.
 """
 text=(text or '').strip()
 if not text:return dict(query=text,feed=feed or None,match_count=0,limit=limit,truncated=False,stops=[])
 esc=text.lower().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
 where="LOWER(name) LIKE ? ESCAPE '\\'";args=['%'+esc+'%']
 if feed:where+=' AND feed=?';args.append(feed)
 total=query('SELECT COUNT(*) n FROM stops WHERE '+where,tuple(args))[0]['n']
 rows=query('SELECT id,feed,name,lat,lon FROM stops WHERE '+where+" ORDER BY CASE WHEN LOWER(name) LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END,name,id LIMIT ?",tuple(args+[esc+'%',limit]))
 return dict(query=text,feed=feed or None,match_count=total,limit=limit,truncated=total>len(rows),stops=[annotate_stop(s) for s in rows])

def pdf_schedules(document=''):
 """Return reviewed-PDF rows separately from GTFS; absent tables mean none loaded."""
 try:
  args=();where=''
  if document:where=' WHERE d.document_id=?';args=(document,)
  docs=query('SELECT d.*, COUNT(s.schedule_id) AS schedule_count FROM pdf_documents d LEFT JOIN pdf_schedules s ON s.document_id=d.document_id'+where+' GROUP BY d.document_id ORDER BY d.feed,d.effective_start',args)
  schedules=query('SELECT s.*, d.source_url, d.pdf_sha256, d.effective_start, d.effective_end, d.review_status, d.extraction_method, d.extractor FROM pdf_schedules s JOIN pdf_documents d ON d.document_id=s.document_id'+(' WHERE d.document_id=?' if document else '')+' ORDER BY s.route,s.direction,s.schedule_id',args)
  for schedule in schedules:
   schedule['stops']=query('SELECT seq,stop_id,stop_name,arrival,departure,timepoint,note FROM pdf_schedule_stops WHERE schedule_id=? ORDER BY seq',(schedule['schedule_id'],))
  return {'documents':docs,'schedules':schedules,'routing_note':'PDF schedules are not consumed by routing; only reviewed, unambiguous, high-confidence rows are marked eligible.'}
 except sqlite3.OperationalError as exc:
  if 'no such table' in str(exc):return {'documents':[],'schedules':[],'routing_note':'No reviewed PDF schedules loaded.'}
  raise

def departures(stop,day,route=''):
 seen=set();out=[]
 for dep,arr,a,b,trip,r,head,pu,do,seq in connections(day):
  if a!=stop or pu!=0 or dep<0 or dep>=86400 or (route and r!=route) or (trip,seq) in seen:continue
  seen.add((trip,seq));out.append(dict(departure=dep,trip=trip,route=r,headsign=head,source=r.split(':')[0]))
 return out
