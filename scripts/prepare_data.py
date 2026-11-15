"""Seed a new checkout without overwriting any existing local data."""
import argparse,json,pathlib,shutil,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--include-optional',action='store_true');args=parser.parse_args()
(root/'data').mkdir(exist_ok=True)
registry=root/'data/sources.json'
if not registry.exists():shutil.copyfile(root/'config/feeds.json',registry)
else:
 sources=json.loads(registry.read_text());known={s['id'] for s in sources}
 for source in json.loads((root/'config/feeds.json').read_text()):
  if source['id'] not in known:sources.append(source)
  elif source['id']=='lirr':
   existing=next(s for s in sources if s['id']=='lirr')
   existing.update(url=source['url'],official_page=source['official_page'],optional=source['optional'])
 registry.write_text(json.dumps(sources,indent=2)+'\n')
command=[sys.executable,str(root/'import_gtfs.py'),'--refresh']
if args.include_optional:command.append('--include-optional')
subprocess.run(command,check=True,cwd=root)
