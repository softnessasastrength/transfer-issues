"""Connection scan routing. No live data; geographic transfers are estimates."""
import math, functools, collections, heapq
from transfer_edges import edges, transfer_rules
from database import query,connections,coverage
INF=10**15

def distance(a,b):
 la,lb=math.radians(a['lat']),math.radians(b['lat']);dy=lb-la;dx=math.radians(b['lon']-a['lon'])
 return 6371000*2*math.asin(min(1,math.sqrt(math.sin(dy/2)**2+math.cos(la)*math.cos(lb)*math.sin(dx/2)**2)))

@functools.lru_cache(maxsize=1)
def network():
 stops={s['id']:s for s in query('SELECT * FROM stops')}
 rules=transfer_rules(stops,query('SELECT * FROM transfers'))
 return stops,None,rules

@functools.lru_cache(maxsize=24)
def transfer_graph(radius,mode):
 stops,_,_=network()
 return edges(stops,query('SELECT * FROM transfers'),radius=radius,mode=mode)

@functools.lru_cache(maxsize=50000)
def neighbors(sid,radius,mode):
 return [(e['to'],e['seconds'],e['meters']) for e in transfer_graph(radius,mode).get(sid,())]

def scan(day,origin,start,deadline,mode='walk',radius=500,buffer=300,feeds=()):
 stops,grid,rules=network()
 if origin not in stops:raise ValueError('Unknown origin stop')
 arrivals={origin:start};paths={origin:()};onboard={};ready={origin:start}
 def relax(sid,time,path,initial=False):
  # Dijkstra closure: allow consecutive walking transfers; only improve arrival.
  heap=[(time,sid,path,initial)]
  while heap:
   at,node,current,first=heapq.heappop(heap)
   if at>deadline or at>arrivals.get(node,INF):continue
   if at<arrivals.get(node,INF):
    arrivals[node]=at;paths[node]=current
   elif node not in paths:
    paths[node]=current
   ready[node]=min(ready.get(node,INF),at+(0 if first else buffer))
   for edge in transfer_graph(radius,mode).get(node,()):
    dest=edge['to'];t=at+edge['seconds']
    if t>deadline or t>=arrivals.get(dest,INF):continue
    leg=dict(kind=mode,from_stop=node,to_stop=dest,departure=at,arrival=t,
             meters=edge['meters'],estimated=True,transfer_source=edge['source'])
    arrivals[dest]=t;paths[dest]=current+(leg,)
    heapq.heappush(heap,(t,dest,paths[dest],False))
 relax(origin,start,(),True)
 for dep,arr,a,b,trip,route,head,pu,do,seq in connections(day):
  if dep<start:continue
  if dep>deadline:break
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
 arr,paths=scan(day,origin,start,deadline,**opts)
 if destination not in arr:return {'found':False,'message':'No itinerary found in the loaded feeds and selected time window. Missing feeds or estimated transfer limits may hide valid journeys.','coverage':coverage(day)}
 legs=list(paths[destination]);return {'found':True,'departure':legs[0]['departure'] if legs else start,'arrival':arr[destination],'legs':legs,'estimated_ground_meters':sum(l.get('meters',0) for l in legs),'coverage':coverage(day),'status':'Scheduled feasibility only; transfers are estimates, not guarantees.'}

def latest(day,origin,destination,start,deadline,**opts):
 first=plan(day,origin,destination,start,deadline,**opts)
 if not first['found']:return first
 lo=start//60;hi=deadline//60
 while lo<hi:
  mid=(lo+hi+1)//2
  if plan(day,origin,destination,mid*60,deadline,**opts)['found']:lo=mid
  else:hi=mid-1
 result=plan(day,origin,destination,lo*60,deadline,**opts);result['latest_start_minute']=lo*60;result['precision']='One minute; selected deadline and loaded feeds only';return result
