"""Synthetic checkpoint tests; not evidence of live transit correctness."""
import unittest
from unittest.mock import patch
import import_gtfs,database,routing,server
class TimeTests(unittest.TestCase):
 def test_extended_day(self):self.assertEqual(import_gtfs.seconds('25:10:00'),90600)
 def test_invalid_times(self):
  for s in ['12:61:00','-1:00:00','','12:00']:
   with self.subTest(s=s),self.assertRaises(ValueError):import_gtfs.seconds(s)
class CalendarTests(unittest.TestCase):
 def test_holiday_override(self):
  def query(sql,args=()):return [{'service':'weekday','days':'1111100'}] if 'calendar WHERE' in sql else [{'service':'weekday','type':2},{'service':'holiday','type':1}]
  with patch.object(database,'query',side_effect=query):self.assertEqual(database.active_services('2026-11-26'),{'holiday'})
 def test_weekend(self):
  with patch.object(database,'query',side_effect=lambda sql,args=():[{'service':'weekday','days':'1111100'}] if 'calendar WHERE' in sql else []):self.assertEqual(database.active_services('2026-11-14'),set())
class RoutingTests(unittest.TestCase):
 def setUp(self):
  self.stops={k:dict(id=k,lat=42.,lon=-72.,parent='') for k in ['a','b','c']}
  for p in [patch.object(routing,'network',return_value=(self.stops,{},{})),patch.object(routing,'neighbors',return_value=[]),patch.object(routing,'transfer_graph',return_value={}),patch.object(routing,'coverage',return_value=[])]:p.start();self.addCleanup(p.stop)
 def c(self,dep,arr,a,b,trip,seq=0,pu=0,do=0):return (dep,arr,a,b,trip,'test:route','Test',pu,do,seq)
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
  with patch.object(routing,'connections',return_value=[]),patch.object(routing,'transfer_graph',return_value={'a':[{'to':'b','seconds':120,'meters':150,'estimated':True,'source':'synthetic'}]}):
   r=routing.plan('2026-11-12','a','b',0,400);self.assertTrue(r['legs'][0]['estimated']);self.assertEqual(r['estimated_ground_meters'],150)
class ApiTests(unittest.TestCase):
 def test_invalid_date(self):
  with self.assertRaises(ValueError):server.dated({'date':['bad']})
 def test_unknown_endpoint(self):
  with self.assertRaises(LookupError):server.handle('/api/v1/unknown',{})
 def test_invalid_range(self):
  with self.assertRaises(ValueError):server.number({'time':['999999']},'time',0,0,86399)
if __name__=='__main__':unittest.main()
