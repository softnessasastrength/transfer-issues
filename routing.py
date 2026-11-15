"""Connection scan routing. No live data; geographic transfers are estimates."""
import math, functools, collections
from database import query,connections,coverage
INF=10**15

def distance(a,b):
 la,lb=math.radians(a['lat']),math.radians(b['lat']);dy=lb-la;dx=math.radians(b['lon']-a['lon'])
 return 6371000*2*math.asin(min(1,math.sqrt(math.sin(dy/2)**2+math.cos(la)*math.cos(lb)*math.sin(dx/2)**2)))

@functools.lru_cache(maxsize=1)
def network():
 stops={s['id']:s for s in query('SELECT * FROM stops')};grid=collections.defaultdict(list)
 for sid,s in stops.items():grid[(int(s['lat']*100),int(s['lon']*100))].append(sid)
 rules={}
 for r in query('SELECT * FROM transfers'):
  # Parent-station rules apply to child platforms too.
  aa=[r['a']]+[k for k,s in stops.items() if s['parent']==r['a']];bb=[r['b']]+[k for k,s in stops.items() if s['parent']==r['b']]
  for a in aa:
   for b in bb:rules[(a,b)]=(r['type'],r['seconds'])
 return stops,grid,rules

@functools.lru_cache(maxsize=50000)
def neighbors(sid,radius,mode):
 stops,grid,rules=network();s=stops[sid];y,x=int(s['lat']*100),int(s['lon']*100);n=math.ceil(radius/750)+1;out=[]
 candidates=set()
 for yy in range(y-n,y+n+1):
  for xx in range(x-n,x+n+1):candidates.update(grid.get((yy,xx),[]))
 for t in candidates:
  if t==sid:continue
  d=distance(s,stops[t]);rule=rules.get((sid,t))
  if rule and rule[0]==3:continue
  if d>radius:continue
  # Straight-line × 1.3 is a planning estimate, not a traversable path.
  seconds=max(60,math.ceil(d*1.3/(4.5/3.6 if mode=='walk' else 12/3.6)))
  if rule and rule[0]==2:seconds=max(seconds,rule[1])
  out.append((t,seconds,round(d*1.3)))
 return out

def _scan_route_chain(day,origin,start,deadline,mode,radius,buffer,feeds,destination,route_chain):
 """Keep partial chains separate until every requested route has been used."""
 stops,grid,rules=network()
 if origin not in stops:raise ValueError('Unknown origin stop')
 # A label is (stop, index of the last route used); -1 means no transit yet.
 arrivals={(origin,-1):start};paths={(origin,-1):()};ready={(origin,-1):start}
 onboard={}
 complete=len(route_chain)-1

 def relax(sid,stage,time,path,initial=False):
  key=(sid,stage)
  if time<arrivals.get(key,INF):
   arrivals[key]=time;paths[key]=path;ready[key]=time+(0 if initial else buffer)
  for dest,seconds,meters in neighbors(sid,radius,mode):
   t=time+seconds;key=(dest,stage)
   if t>deadline or t>=arrivals.get(key,INF):continue
   leg=dict(kind=mode,from_stop=sid,to_stop=dest,departure=time,arrival=t,meters=meters,estimated=True)
   arrivals[key]=t;paths[key]=path+(leg,);ready[key]=t+(0 if initial else buffer)

 relax(origin,-1,start,(),True)
 for dep,arr,a,b,trip,route,head,pu,do,seq in connections(day):
  if dep<start:continue
  if dep>deadline:break
  if destination is not None and dep>arrivals.get((destination,complete),INF):break
  if arr>deadline or (feeds and route.split(':')[0] not in feeds):continue
  for stage in range(-1,len(route_chain)):
   if stage==-1:
    if route!=route_chain[0]:continue
    next_stage=0
   elif route==route_chain[stage]:next_stage=stage
   elif stage<complete and route==route_chain[stage+1]:next_stage=stage+1
   else:continue

   prev=onboard.get((trip,stage));path=None
   if prev and prev[0]==seq-1:path=prev[1]
   key=(a,stage);rule=rules.get((a,a));minready=ready.get(key,INF)
   if rule and rule[0]==2 and paths.get(key):minready=max(minready,arrivals[key]+rule[1])
   canboard=pu==0 and minready<=dep and not (rule and rule[0]==3 and paths.get(key))
   if path is None and canboard:path=paths[key]
   if path is None:continue
   leg=dict(kind='transit',from_stop=a,to_stop=b,departure=dep,arrival=arr,trip=trip,route=route,headsign=head,source=route.split(':')[0],estimated=False)
   if path and path[-1].get('trip')==trip:
    leg={**path[-1],'to_stop':b,'arrival':arr};newpath=path[:-1]+(leg,)
   else:newpath=path+(leg,)
   onboard[(trip,next_stage)]=(seq,newpath)
   if do==0:relax(b,next_stage,arr,newpath)
 return ({sid:time for (sid,stage),time in arrivals.items() if stage==complete},
         {sid:path for (sid,stage),path in paths.items() if stage==complete})

def scan(day,origin,start,deadline,mode='walk',radius=500,buffer=300,feeds=(),destination=None,route_chain=()):
 if route_chain:
  return _scan_route_chain(day,origin,start,deadline,mode,radius,buffer,feeds,destination,route_chain)
 stops,grid,rules=network()
 if origin not in stops:raise ValueError('Unknown origin stop')
 arrivals={origin:start};paths={origin:()};onboard={};ready={origin:start}
 def relax(sid,time,path,initial=False):
  if time<arrivals.get(sid,INF):arrivals[sid]=time;paths[sid]=path;ready[sid]=time+(0 if initial else buffer)
  for dest,seconds,meters in neighbors(sid,radius,mode):
   t=time+seconds
   if t>deadline or t>=arrivals.get(dest,INF):continue
   leg=dict(kind=mode,from_stop=sid,to_stop=dest,departure=time,arrival=t,meters=meters,estimated=True)
   arrivals[dest]=t;paths[dest]=path+(leg,);ready[dest]=t+(0 if initial else buffer)
 relax(origin,start,(),True)
 for dep,arr,a,b,trip,route,head,pu,do,seq in connections(day):
  if dep<start:continue
  if dep>deadline:break
  # Connections are departure-sorted and arrivals cannot precede departures.
  # Once every later connection departs after the best destination arrival,
  # neither transit nor a nonnegative walk can improve that result.
  if destination is not None and dep>arrivals.get(destination,INF):break
  if arr>deadline or (feeds and route.split(':')[0] not in feeds):continue
  prev=onboard.get(trip);path=None
  if prev and prev[0]==seq-1:path=prev[1]
  rule=rules.get((a,a));minready=ready.get(a,INF)
  if rule and rule[0]==2 and paths.get(a):minready=max(minready,arrivals[a]+rule[1])
  canboard=pu==0 and minready<=dep and not (rule and rule[0]==3 and paths.get(a))
  if path is None and canboard:path=paths[a]
  if path is None:continue
  leg=dict(kind='transit',from_stop=a,to_stop=b,departure=dep,arrival=arr,trip=trip,route=route,headsign=head,source=route.split(':')[0],estimated=False)
  # Preserve one leg per vehicle, not one leg per stop.
  if path and path[-1].get('trip')==trip:
   leg={**path[-1],'to_stop':b,'arrival':arr};newpath=path[:-1]+(leg,)
  else:newpath=path+(leg,)
  onboard[trip]=(seq,newpath)
  if do==0:relax(b,arr,newpath)
 return arrivals,paths

def plan(day,origin,destination,start,deadline,**opts):
 if destination not in network()[0]:raise ValueError('Unknown destination stop')
 arr,paths=scan(day,origin,start,deadline,destination=destination,**opts)
 if destination not in arr:return {'found':False,'message':'No itinerary found in the loaded feeds and selected time window. Missing feeds or estimated transfer limits may hide valid journeys.','coverage':coverage(day)}
 legs=list(paths[destination]);return {'found':True,'departure':legs[0]['departure'] if legs else start,'arrival':arr[destination],'legs':legs,'estimated_ground_meters':sum(l.get('meters',0) for l in legs),'coverage':coverage(day),'status':'Scheduled feasibility only; transfers are estimates, not guarantees.'}

def _latest_binary(day,origin,destination,start,deadline,opts,first):
 """Exact fallback for reverse candidates that fail forward certification."""
 if not first['found']:return first
 lo=start//60;hi=deadline//60
 while lo<hi:
  mid=(lo+hi+1)//2
  if plan(day,origin,destination,mid*60,deadline,**opts)['found']:lo=mid
  else:hi=mid-1
 result=plan(day,origin,destination,lo*60,deadline,**opts);result['latest_start_minute']=lo*60;result['precision']='One minute; selected deadline and loaded feeds only';return result

def latest(day,origin,destination,start,deadline,**opts):
 first=plan(day,origin,destination,start,deadline,**opts)
 if not first['found']:return first

 # The reverse bubble pass proposes the latest feasible ready-time. Certify
 # the minute boundary with forward plans: this catches approximation gaps
 # (including drop-off and station-transfer constraints) before returning it.
 from bubble import latest_return_departures
 best=latest_return_departures(
  day,destination,deadline,mode=opts.get('mode','walk'),
  radius=opts.get('radius',500),buffer=opts.get('buffer',300),
  feeds=opts.get('feeds',()),stop_at=origin)
 lo=start//60;hi=deadline//60
 candidate=min(hi,best.get(origin,-1)//60)
 if candidate<lo:
  return _latest_binary(day,origin,destination,start,deadline,opts,first)
 result=plan(day,origin,destination,candidate*60,deadline,**opts)
 certified=result['found'] and (
  candidate==hi or not plan(day,origin,destination,(candidate+1)*60,
                             deadline,**opts)['found'])
 if not certified:
  return _latest_binary(day,origin,destination,start,deadline,opts,first)
 result['latest_start_minute']=candidate*60
 result['precision']='One minute; selected deadline and loaded feeds only'
 return result
