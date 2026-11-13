"""Small normalized agency database for offline validation regression tests."""
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE stops(id TEXT,feed TEXT,name TEXT,lat REAL,lon REAL,parent TEXT,wheelchair TEXT);
CREATE TABLE routes(id TEXT,feed TEXT,short TEXT,name TEXT,type TEXT,color TEXT,agency TEXT);
CREATE TABLE trips(id TEXT,route TEXT,service TEXT,headsign TEXT,direction TEXT,shape TEXT);
CREATE TABLE times(trip TEXT,seq INTEGER,stop TEXT,arr INTEGER,dep INTEGER,pickup INTEGER,dropoff INTEGER);
CREATE TABLE calendar(service TEXT,start TEXT,end TEXT,days TEXT);
CREATE TABLE exceptions(service TEXT,date TEXT,type INTEGER);
CREATE TABLE shapes(id TEXT,seq INTEGER,lat REAL,lon REAL);
CREATE TABLE transfers(a TEXT,b TEXT,type INTEGER,seconds INTEGER);
INSERT INTO stops VALUES ('ct:a','cttransit','A',41.7,-72.6,'','0');
INSERT INTO stops VALUES ('ct:b','cttransit','B',41.8,-72.7,'','0');
INSERT INTO routes VALUES ('ct:r','cttransit','1','Fixture','3','','Fixture agency');
INSERT INTO trips VALUES ('ct:t','ct:r','ct:svc','Fixture','0','');
INSERT INTO times VALUES ('ct:t',0,'ct:a',85800,85800,0,0);
INSERT INTO times VALUES ('ct:t',2,'ct:b',87000,87000,0,0);
INSERT INTO calendar VALUES ('ct:svc','20260101','20261231','1111111');
"""


def agency_database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript(SCHEMA)
