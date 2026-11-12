"""Start the loopback desktop proof of concept without refreshing existing data."""
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
data = pathlib.Path(os.environ.get('ATLAS_DATA_DIR', root / 'data'))
if not (data / 'atlas.sqlite').exists():
    print('No imported database found. Run python3 scripts/prepare_data.py first.', file=sys.stderr)
    raise SystemExit(1)
print('Open http://127.0.0.1:8000 in your browser. Stop with Control-C.', flush=True)
raise SystemExit(subprocess.call([sys.executable, str(root / 'server.py')], cwd=root))
