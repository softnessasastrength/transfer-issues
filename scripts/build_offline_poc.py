#!/usr/bin/env python3
"""Export a reproducible CT + PVTA offline SQLite subset without changing live data."""
import argparse, datetime, hashlib, json, pathlib, shutil, sqlite3, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
FEEDS=('cttransit','hartford','pvta')
TABLES=('stops','routes','trips','times','calendar','exceptions','shapes','transfers')
def export(source,output,allow_missing):
    if not source.is_file():raise SystemExit('Missing '+str(source)+'. Run the importer first.')
    output.mkdir(parents=True,exist_ok=True)
    destination=output/'atlas.sqlite'
    if destination.exists():raise SystemExit('Refusing to overwrite '+str(destination))
    source_db=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
    source_db.row_factory=sqlite3.Row
    feeds={r[0]:r[1] for r in source_db.execute('SELECT feed,COUNT(*) FROM routes GROUP BY feed')}
    missing=[f for f in FEEDS if not feeds.get(f)]
    if missing and not allow_missing:raise SystemExit('Missing route data for '+', '.join(missing)+'. Use --allow-partial for a clearly labeled incomplete pack.')
    tmp=output/'atlas.build.sqlite'
    if tmp.exists():raise SystemExit('Temporary database exists: '+str(tmp))
    try:
        target=sqlite3.connect(tmp)
        # Backup first to retain schema, indexes, and any future core tables.
        source_db.backup(target)
        target.execute('PRAGMA foreign_keys=OFF')
        for table in TABLES:
            if table in ('stops','routes'):
                target.execute(f"DELETE FROM {table} WHERE feed NOT IN ({','.join('?' for _ in FEEDS)})",FEEDS)
            elif table=='trips':
                target.execute("DELETE FROM trips WHERE route NOT IN (SELECT id FROM routes)")
            elif table=='times':
                target.execute("DELETE FROM times WHERE trip NOT IN (SELECT id FROM trips)")
            elif table=='calendar':
                target.execute("DELETE FROM calendar WHERE service NOT IN (SELECT DISTINCT service FROM trips)")
            elif table=='exceptions':
                target.execute("DELETE FROM exceptions WHERE service NOT IN (SELECT DISTINCT service FROM trips)")
            elif table=='shapes':
                target.execute("DELETE FROM shapes WHERE id NOT IN (SELECT DISTINCT shape FROM trips)")
            elif table=='transfers':
                target.execute("DELETE FROM transfers WHERE a NOT IN (SELECT id FROM stops) OR b NOT IN (SELECT id FROM stops)")
        target.commit()
        integrity=target.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity!='ok':raise RuntimeError('SQLite integrity failed: '+integrity)
        counts={table:target.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in TABLES}
        target.execute('VACUUM')
        target.close()
        tmp.replace(destination)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    finally:source_db.close()
    original=ROOT/'data/sources.json'
    sources=json.loads(original.read_text()) if original.exists() else []
    selected=[s for s in sources if s.get('id') in FEEDS]
    (output/'sources.json').write_text(json.dumps(selected,indent=2))
    digest=hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest={'format':'transit-atlas-offline-poc-v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'requested_feeds':list(FEEDS),'present_feeds':{k:feeds[k] for k in FEEDS if feeds.get(k)},
              'missing_feeds':missing,'complete':False,'scope':'CTtransit + Hartford Line + PVTA where imported; not all Connecticut operators',
              'sqlite_bytes':destination.stat().st_size,'sqlite_sha256':digest,'counts':counts,
              'limitations':['No street basemap or pedestrian graph included','No native iOS routing engine','No real-time arrivals','Feed freshness and geographic completeness not certified']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--database',type=pathlib.Path,default=ROOT/'data/atlas.sqlite')
    parser.add_argument('--output',type=pathlib.Path,default=ROOT/'build/offline-ct-pvta')
    parser.add_argument('--allow-partial',action='store_true')
    a=parser.parse_args();export(a.database.resolve(),a.output.resolve(),a.allow_partial)
if __name__=='__main__':main()
