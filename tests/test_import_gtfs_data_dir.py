"""import_gtfs must honour ATLAS_DATA_DIR exactly like database.py.

The data dir is resolved at import time, so each case runs in a subprocess
with a controlled environment (hermetic: no feeds are read or written).
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def resolved_data(env_extra):
    env = dict(os.environ)
    env.pop('ATLAS_DATA_DIR', None)
    env.update(env_extra)
    out = subprocess.run(
        [sys.executable, '-c', 'import import_gtfs; print(import_gtfs.DATA)'],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


class ImportGtfsDataDirTests(unittest.TestCase):
    def test_env_override_is_honoured(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(resolved_data({'ATLAS_DATA_DIR': tmp}), tmp)

    def test_default_is_repo_data_dir(self):
        self.assertEqual(resolved_data({}), str(ROOT / 'data'))


if __name__ == '__main__':
    unittest.main()
