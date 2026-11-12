"""Build the atlas database from official GTFS archives. Python 3.11+, stdlib only."""
import csv, io, zipfile, sqlite3, json, hashlib, datetime, pathlib, collections, argparse, urllib.request, urllib.error, time
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'data'
DAYS=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
PAGES={'cttransit':'https://www.cttransit.com/about/developers','hartford':'https://www.cttransit.com/about/developers','pvta':'https://pvta.com/bus_service/real_time_data.php','wrta':'https://therta.com/','amtrak':'https://www.cttransit.com/about/developers','mbta':'https://www.mbta.com/developers/gtfs'}
def seconds(s):
 p=s.split(':')
 if len(p)!=3: raise ValueError('Missing or invalid time')
 h,m,s=map(int,p)
 if h<0 or not 0<=m<60 or not 0<=s<60:raise ValueError('Invalid time')
 return h*3600+m*60+s

def rows(z,name):
 names=[n for n in z.namelist() if n.rsplit('/',1)[-1]==name+'.txt']
 if not names:return iter(())
 return csv.DictReader(io.TextIOWrapper(z.open(names[0]),encoding='utf-8-sig',newline=''))

def build():
 sources=json.loads((DATA/'sources.json').read_text());tmp=DATA/'atlas.build.sqlite';tmp.unlink(missing_ok=True)
 db=sqlite3.connect(tmp);db.executescript('''
 PRAGMA journal_mode=OFF;
 CREATE TABLE stops(id TEXT PRIMARY KEY,feed TEXT,name TEXT,lat REAL,lon REAL,parent TEXT,wheelchair TEXT);
 CREATE TABLE routes(id TEXT PRIMARY KEY,feed TEXT,short TEXT,name TEXT,type TEXT,color TEXT,agency TEXT);
 CREATE TABLE trips(id TEXT PRIMARY KEY,route TEXT,service TEXT,headsign TEXT,direction TEXT,shape TEXT);
 CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER);
 CREATE TABLE calendar(service TEXT PRIMARY KEY,start TEXT,end TEXT,days TEXT);
 CREATE TABLE exceptions(service TEXT,date TEXT,type INTEGER);
 CREATE TABLE shapes(id TEXT,seq INTEGER,lat REAL,lon REAL);
 CREATE TABLE transfers(a TEXT,b TEXT,type INTEGER,seconds INTEGER);
 ''');reports=[]
 for source in sources:
  feed=source['id'];source['official_page']=PAGES[feed];path=DATA/(feed+'.zip');r={'feed':feed,'errors':{},'warnings':{},'counts':{}}; reports.append(r)
  if not path.exists():continue
  print('Importing',feed,flush=True);source['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();z=zipfile.ZipFile(path);prefix=lambda x:feed+':'+x
  required={'agency.txt','stops.txt','routes.txt','trips.txt','stop_times.txt'}
  if required-set(n.rsplit('/',1)[-1] for n in z.namelist()):raise ValueError(feed+' missing required files')
  agents={a['agency_id']:a for a in rows(z,'agency')}; source['agencies']=list(agents.values());source['feed_info']=list(rows(z,'feed_info'))
  if any(a['agency_timezone']!='America/New_York' for a in agents.values()):r['warnings']['non_eastern_agencies']=1
  stops={s['stop_id']:s for s in rows(z,'stops')}; valid={}
  for k,s in stops.items():
   try:
    lat,lon=float(s['stop_lat']),float(s['stop_lon'])
    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError()
    # Geographic scope: CT and southern/central New England. National rail is clipped.
    if not (40.9<=lat<=43.1 and -73.8<=lon<=-70.5):continue
    valid[k]=s;db.execute('INSERT INTO stops VALUES(?,?,?,?,?,?,?)',(prefix(k),feed,s['stop_name'],lat,lon,prefix(s.get('parent_station','')) if s.get('parent_station') else '',s.get('wheelchair_boarding','0')))
   except (ValueError,KeyError):r['errors']['invalid_stop_coordinate']=r['errors'].get('invalid_stop_coordinate',0)+1
  routes={x['route_id']:x for x in rows(z,'routes')};trips={x['trip_id']:x for x in rows(z,'trips')}
  # MBTA: retain regional rail only; Worcester and onward Boston connections, not subway/bus.
  if feed=='mbta':trips={k:t for k,t in trips.items() if routes[t['route_id']]['route_type']=='2'}
  freq={x['trip_id'] for x in rows(z,'frequencies')};r['warnings']['frequency_trips_excluded']=len(freq)
  grouped=collections.defaultdict(list)
  for t in rows(z,'stop_times'):
   if t['trip_id'] not in trips or t['trip_id'] in freq:continue
   try:
    arr,dep=seconds(t['arrival_time']),seconds(t['departure_time']);seq=int(t['stop_sequence'])
    if dep<arr:raise ValueError()
    grouped[t['trip_id']].append((seq,t['stop_id'],arr,dep,int(t.get('pickup_type') or 0),int(t.get('drop_off_type') or 0)))
   except (ValueError,KeyError):r['errors']['invalid_or_missing_time']=r['errors'].get('invalid_or_missing_time',0)+1;freq.add(t['trip_id'])
  used_routes=set(); used_shapes=set();used_stops=set();n=0
  for k,ts in grouped.items():
   if k in freq:continue
   ts.sort();t=trips[k]
   if t['route_id'] not in routes or any(s[1] not in stops for s in ts):r['errors']['broken_reference']=r['errors'].get('broken_reference',0)+1;continue
   if len({s[0] for s in ts})!=len(ts) or any(b[2]<a[3] for a,b in zip(ts,ts[1:])):r['errors']['non_monotonic_trip']=r['errors'].get('non_monotonic_trip',0)+1;continue
   if sum(s[1] in valid for s in ts)<2:continue
   used_routes.add(t['route_id']);shape=t.get('shape_id','');used_shapes.add(shape)
   db.execute('INSERT INTO trips VALUES(?,?,?,?,?,?)',(prefix(k),prefix(t['route_id']),prefix(t['service_id']),t.get('trip_headsign',''),t.get('direction_id',''),prefix(shape)))
   # Keep sequence gaps so the router never invents a connection over an omitted stop.
   db.executemany('INSERT INTO times VALUES(?,?,?,?,?,?,?)',[(prefix(k),i,prefix(s),arr,dep,pu,do) for i,(seq,s,arr,dep,pu,do) in enumerate(ts) if s in valid]);used_stops.update(s[1] for s in ts if s[1] in valid);n+=1
  for k in used_routes:
   t=routes[k];db.execute('INSERT INTO routes VALUES(?,?,?,?,?,?,?)',(prefix(k),feed,t.get('route_short_name',''),t.get('route_long_name',''),t['route_type'],t.get('route_color',''),agents.get(t.get('agency_id',''),{}).get('agency_name',feed)))
  for s in rows(z,'shapes'):
   if s['shape_id'] in used_shapes:
    lat,lon=float(s['shape_pt_lat']),float(s['shape_pt_lon'])
    db.execute('INSERT INTO shapes VALUES(?,?,?,?)',(prefix(s['shape_id']),int(s['shape_pt_sequence']),lat,lon))
  cal=list(rows(z,'calendar'));exc=list(rows(z,'calendar_dates'))
  if not cal and not exc:raise ValueError(feed+' missing service calendar')
  for c in cal:db.execute('INSERT INTO calendar VALUES(?,?,?,?)',(prefix(c['service_id']),c['start_date'],c['end_date'],''.join(c[d] for d in DAYS)))
  for e in exc:db.execute('INSERT INTO exceptions VALUES(?,?,?)',(prefix(e['service_id']),e['date'],int(e['exception_type'])))
  for t in rows(z,'transfers'):
   if t.get('from_trip_id') or t.get('to_trip_id') or t.get('from_route_id') or t.get('to_route_id'):
    r['warnings']['scoped_transfer_rules_not_supported']=r['warnings'].get('scoped_transfer_rules_not_supported',0)+1;continue
   db.execute('INSERT INTO transfers VALUES(?,?,?,?)',(prefix(t['from_stop_id']),prefix(t['to_stop_id']),int(t.get('transfer_type') or 0),int(t.get('min_transfer_time') or 0)))
  dates=[c['start_date'] for c in cal]+[c['end_date'] for c in cal]+[e['date'] for e in exc]
  source.update(status='imported',service_start=min(dates),service_end=max(dates),scope='Regional rail only' if feed=='mbta' else 'Regional geographic clip' if feed=='amtrak' else 'All valid trips in geographic scope')
  r['counts']={'stops':len(used_stops),'routes':len(used_routes),'trips':n};db.commit()
 db.executescript('''CREATE INDEX times_trip ON times(trip,seq);CREATE INDEX times_stop ON times(stop,dep);CREATE INDEX trips_service ON trips(service);CREATE INDEX shapes_id ON shapes(id,seq);CREATE INDEX exceptions_date ON exceptions(date);DELETE FROM stops WHERE id NOT IN (SELECT stop FROM times);''');db.commit()
 for source in sources:
  r=next(x for x in reports if x['feed']==source['id']);source['validation']=r
 db.close();tmp.replace(DATA/'atlas.sqlite');(DATA/'sources.json').write_text(json.dumps(sources,indent=2));(DATA/'validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))

def download_gtfs(source):
 """Try the publisher's known static GTFS URLs; never substitute unverified schedules."""
 urls=[source['url']]
 if source['id']=='pvta':
  # PVTA publishes the same feed on HTTP and HTTPS; some hosts reject one scheme.
  urls=['https://www.pvta.com/g_trans/google_transit.zip',
        'http://www.pvta.com/g_trans/google_transit.zip']
 errors=[]
 for url in dict.fromkeys(urls):
  try:
   req=urllib.request.Request(url,headers={
    'User-Agent':'Mozilla/5.0 (compatible; SouthernNewEnglandTransitAtlas/0.1; GTFS download)',
    'Accept':'application/zip, application/octet-stream, */*'})
   with urllib.request.urlopen(req,timeout=90) as response:
    content=response.read(60*1024*1024+1)
    last_modified=response.headers.get('Last-Modified')
    final_url=response.geturl()
   if len(content)>60*1024*1024:raise ValueError('GTFS archive exceeds 60 MiB safety limit')
   with zipfile.ZipFile(io.BytesIO(content)) as archive:
    bad=archive.testzip()
    if bad:raise ValueError('Corrupt GTFS member: '+bad)
    names={name.rsplit('/',1)[-1] for name in archive.namelist()}
    required={'agency.txt','stops.txt','routes.txt','trips.txt','stop_times.txt'}
    if not required.issubset(names):raise ValueError('GTFS missing required files: '+str(sorted(required-names)))
   return content,last_modified,final_url
  except (OSError,ValueError,zipfile.BadZipFile) as exc:
   errors.append(url+': '+str(exc))
 raise RuntimeError('All official GTFS download attempts failed: '+'; '.join(errors))

def refresh():
 sources=json.loads((DATA/'sources.json').read_text())
 for source in sources:
  try:
   content,last_modified,final_url=download_gtfs(source)
   # Write only after successful archive validation. Keep the prior ZIP on failure.
   target=DATA/(source['id']+'.zip')
   temporary=target.with_suffix('.download')
   temporary.write_bytes(content)
   temporary.replace(target)
   source.update(status='downloaded',retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 last_modified=last_modified,bytes=len(content),download_url=final_url)
   source.pop('refresh_error',None)
   source.pop('error',None)
  except Exception as exc:
   source['refresh_error']=str(exc)
   print(source['id'],exc)
 (DATA/'sources.json').write_text(json.dumps(sources,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');a=p.parse_args()
 if a.refresh:refresh()
 build()
