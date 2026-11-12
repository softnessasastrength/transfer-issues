"""Seed a new checkout without overwriting any existing local data."""
import pathlib,shutil,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
(root/'data').mkdir(exist_ok=True)
registry=root/'data/sources.json'
if not registry.exists():shutil.copyfile(root/'config/feeds.json',registry)
subprocess.run([sys.executable,str(root/'import_gtfs.py'),'--refresh'],check=True,cwd=root)
