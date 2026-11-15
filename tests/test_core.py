"""Synthetic checkpoint tests; not evidence of live transit correctness."""
import unittest
from unittest.mock import patch
import import_gtfs,database,routing,server
class TimeTests(unittest.TestCase):
 def test_whole_network_policy_bypasses_default_bounds(self):
  with patch.object(import_gtfs,'POLICY',{'default':{'bounds':[40,41,-74,-73]},'feeds':{'amtrak':{'whole_network':True}}}):
   self.assertTrue(import_gtfs.in_scope('amtrak',47.6,-122.3))
   self.assertFalse(import_gtfs.in_scope('unknown',47.6,-122.3))
 def test_extended_day(self):self.assertEqual(import_gtfs.seconds('25:10:00'),90600)
 def test_invalid_times(self):
  for s in ['12:61:00','-1:00:00','','12:00']:
   with self.subTest(s=s),self.assertRaises(ValueError):import_gtfs.seconds(s)
 def test_mbta_policy_selects_all_modes_for_mbta_agency(self):
  for route_type in range(8):
   self.assertTrue(import_gtfs.route_is_selected('mbta', {'agency_id':'1','route_type':str(route_type)}))
  self.assertFalse(import_gtfs.route_is_selected('mbta', {'agency_id':'3','route_type':'2'}))
class CalendarTests(unittest.TestCase):
 def test_holiday_override(self):
  def query(sql,args=()):return [{'service':'weekday','days':'1111100'}] if 'calendar WHERE' in sql else [{'service':'weekday','type':2},{'service':'holiday','type':1}]
  with patch.object(database,'query',side_effect=query):self.assertEqual(database.active_services('2026-11-26'),{'holiday'})
 def test_weekend(self):
  with patch.object(database,'query',side_effect=lambda sql,args=():[{'service':'weekday','days':'1111100'}] if 'calendar WHERE' in sql else []):self.assertEqual(database.active_services('2026-11-14'),set())
class RoutingTests(unittest.TestCase):
 def setUp(self):
  self.stops={k:dict(id=k,lat=42.,lon=-72.,parent='') for k in ['a','b','c']}
  for p in [patch.object(routing,'network',return_value=(self.stops,{},{})),patch.object(routing,'neighbors',return_value=[]),patch.object(routing,'coverage',return_value=[])]:p.start();self.addCleanup(p.stop)
 def c(self,dep,arr,a,b,trip,seq=0,pu=0,do=0,route='test:route'):return (dep,arr,a,b,trip,route,'Test',pu,do,seq)
 def test_route_chain_requires_ordered_routes(self):
  journey=[self.c(100,200,'a','b','t',route='cttransit:905'),self.c(600,700,'b','c','u',route='cttransit:82')]
  with patch.object(routing,'connections',return_value=journey):
   self.assertTrue(routing.plan('2026-11-12','a','c',0,800,route_chain=('cttransit:905','cttransit:82'))['found'])
   self.assertFalse(routing.plan('2026-11-12','a','c',0,800,route_chain=('cttransit:82','cttransit:905'))['found'])
 def test_through_ride(self):
  with patch.object(routing,'connections',return_value=[self.c(100,200,'a','b','t'),self.c(200,300,'b','c','t',1)]):
   r=routing.plan('2026-11-12','a','c',0,400,buffer=300);self.assertTrue(r['found']);self.assertEqual(len(r['legs']),1);self.assertEqual(r['arrival'],300)
 def test_tight_transfer_rejected(self):
  with patch.object(routing,'connections',return_value=[self.c(100,200,'a','b','t'),self.c(250,300,'b','c','u')]):self.assertFalse(routing.plan('2026-11-12','a','c',0,400,buffer=100)['found'])
 def test_pickup_prohibited(self):
  with patch.object(routing,'connections',return_value=[self.c(100,200,'a','b','t',pu=1)]):self.assertFalse(routing.plan('2026-11-12','a','b',0,400)['found'])
 def test_dropoff_prohibited_but_through_allowed(self):
  with patch.object(routing,'connections',return_value=[self.c(100,200,'a','b','t',do=1),self.c(200,300,'b','c','t',1)]):
   self.assertFalse(routing.plan('2026-11-12','a','b',0,400)['found']);self.assertTrue(routing.plan('2026-11-12','a','c',0,400)['found'])
 def test_overnight(self):
  with patch.object(routing,'connections',return_value=[self.c(87000,88000,'a','b','t')]):self.assertEqual(routing.plan('2026-11-12','a','b',86000,90000)['arrival'],88000)
 def test_latest(self):
  with patch.object(routing,'connections',return_value=[self.c(600,700,'a','b','t'),self.c(1200,1300,'a','b','u')]):self.assertEqual(routing.latest('2026-11-12','a','b',0,1400)['latest_start_minute'],1200)
 def test_ground_estimate(self):
  with patch.object(routing,'connections',return_value=[]),patch.object(routing,'neighbors',side_effect=lambda s,r,m:[('b',120,150)] if s=='a' else []):
   r=routing.plan('2026-11-12','a','b',0,400);self.assertTrue(r['legs'][0]['estimated']);self.assertEqual(r['estimated_ground_meters'],150)
 def test_destination_exit_preserves_local_and_intercity_itineraries(self):
  class Counted(list):
   consumed=0
   def __iter__(self):
    for item in super().__iter__():
     self.consumed+=1
     yield item
  cases=[
   ('a','b',[self.c(100,200,'a','b','local')]),
   ('a','c',[self.c(100,200,'a','b','rail',0),self.c(200,300,'b','c','rail',1)]),
  ]
  for origin,dest,journey in cases:
   with self.subTest(destination=dest):
    conns=Counted(journey+[self.c(t,t+20,'b','a','noise'+str(t)) for t in range(301,1001,10)])
    with patch.object(routing,'connections',return_value=conns):
     full_arr,full_paths=routing.scan('2026-11-12',origin,0,2000)
    full_consumed=conns.consumed
    conns.consumed=0
    with patch.object(routing,'connections',return_value=conns):
     early_arr,early_paths=routing.scan('2026-11-12',origin,0,2000,destination=dest)
    self.assertEqual(early_arr[dest],full_arr[dest])
    self.assertEqual(early_paths[dest],full_paths[dest])
    self.assertLess(conns.consumed,full_consumed)
class ApiTests(unittest.TestCase):
 def test_optional_planning_feeds_are_excluded_by_default(self):
  with patch.object(server.db,'sources',return_value=[{'id':'cttransit'},{'id':'lirr','optional':True}]):
   self.assertEqual(server.planning_feeds({}),('cttransit',))
   self.assertEqual(server.planning_feeds({'include_optional':['1']}),())
 def test_invalid_date(self):
  with self.assertRaises(ValueError):server.dated({'date':['bad']})
 def test_unknown_endpoint(self):
  with self.assertRaises(LookupError):server.handle('/api/v1/unknown',{})
 def test_invalid_range(self):
  with self.assertRaises(ValueError):server.number({'time':['999999']},'time',0,0,86399)
 def test_boolean_and_enum_options_are_strict(self):
  with self.assertRaises(ValueError):server.flag({'return':['2']},'return')
  with self.assertRaises(ValueError):server.handle('/api/v1/plan',{'kind':['soon']})
 def test_pagination_is_opt_in_and_has_totals(self):
  rows=list(range(5))
  self.assertEqual(server.page_options({}),None)
  self.assertEqual(server.page_slice(rows,2,2),([2,3],{'page':2,'page_size':2,'total':5,'has_next':True}))
 def test_compact_meta_omits_large_arrays(self):
  with patch.object(server.db,'sources',return_value=[]), patch.object(server.db,'query',return_value=[]), patch.object(server,'CITIES',[('Hartford',0,0)]):
   result=server.handle('/api/v1/meta',{'compact':['1']})
  self.assertNotIn('routes',result);self.assertNotIn('stops',result);self.assertEqual(result['api_version'],'1.0')
 def test_warm_caches_builds_selected_date(self):
  with patch.object(server.routing,'network') as network,patch.object(server.db,'connections') as connections:
   self.assertEqual(server.warm_caches('2026-11-17'),'2026-11-17')
  network.assert_called_once_with()
  connections.assert_called_once_with('2026-11-17')
class DownloadTests(unittest.TestCase):
 # Regression: pvta.com returns HTTP 403 to the default urllib User-Agent.
 # refresh() must send the project's explicit descriptive User-Agent on every
 # feed download. Uses a local stub; never touches the live network.
 def test_refresh_sends_user_agent(self):
  import io,json,pathlib,tempfile,urllib.request,zipfile
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,'w') as z:z.writestr('agency.txt','x')
  seen={}
  class Resp:
   headers={'Last-Modified':'Mon, 02 Nov 2026 19:12:54 GMT'}
   def read(self):return buf.getvalue()
   def __enter__(self):return self
   def __exit__(self,*a):return False
  def fake_urlopen(req,timeout=0):seen['req']=req;return Resp()
  with tempfile.TemporaryDirectory() as td:
   data=pathlib.Path(td);(data/'sources.json').write_text(json.dumps([{'id':'stub','url':'https://example.invalid/feed.zip','refresh_error':'HTTP Error 403: Forbidden'}]))
   with patch.object(import_gtfs,'DATA',data),patch('urllib.request.urlopen',side_effect=fake_urlopen):import_gtfs.refresh()
   req=seen['req'];self.assertIsInstance(req,urllib.request.Request);self.assertEqual(req.get_header('User-agent'),import_gtfs.USER_AGENT);self.assertNotIn('Python-urllib',req.get_header('User-agent'))
   saved=json.loads((data/'sources.json').read_text());self.assertEqual(saved[0]['status'],'downloaded');self.assertNotIn('refresh_error',saved[0])
if __name__=='__main__':unittest.main()
