"""Offline pack filtering regression using a minimal synthetic SQLite fixture."""
import importlib.util, json, pathlib, sqlite3, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('offline_pack',ROOT/'scripts/build_offline_poc.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class OfflinePackTests(unittest.TestCase):
 def test_partial_pack_and_preserves_source(self):
  with tempfile.TemporaryDirectory() as temp:
   p=pathlib.Path(temp);source=p/'source.sqlite';out=p/'pack'
   with sqlite3.connect(source) as db:
    db.executescript("""CREATE TABLE stops(id TEXT,feed TEXT);
CREATE TABLE routes(id TEXT,feed TEXT);
CREATE TABLE trips(id TEXT,route TEXT,service TEXT,shape TEXT);
CREATE TABLE times(trip TEXT,stop TEXT);
CREATE TABLE calendar(service TEXT);
CREATE TABLE exceptions(service TEXT);
CREATE TABLE shapes(id TEXT);
CREATE TABLE transfers(a TEXT,b TEXT);
INSERT INTO stops VALUES('cttransit:s','cttransit'),('mbta:s','mbta');
INSERT INTO routes VALUES('cttransit:r','cttransit'),('mbta:r','mbta');
INSERT INTO trips VALUES('cttransit:t','cttransit:r','cttransit:c','cttransit:sh'),('mbta:t','mbta:r','mbta:c','mbta:sh');
INSERT INTO times VALUES('cttransit:t','cttransit:s'),('mbta:t','mbta:s');
INSERT INTO calendar VALUES('cttransit:c'),('mbta:c');
INSERT INTO shapes VALUES('cttransit:sh'),('mbta:sh');""")
   with self.assertRaises(SystemExit):mod.export(source,out,False)
   mod.export(source,out,True)
   manifest=json.loads((out/'manifest.json').read_text())
   self.assertIn('pvta',manifest['missing_feeds'])
   with sqlite3.connect(out/'atlas.sqlite') as db:
    self.assertEqual(db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],1)
    self.assertEqual(db.execute('SELECT COUNT(*) FROM times').fetchone()[0],1)
   with sqlite3.connect(source) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],2)
if __name__=='__main__':unittest.main()
