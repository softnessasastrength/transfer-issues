# Releasing the Transit Atlas Debian package

Releases are **tag-driven**. Nobody edits a version number by hand and
nobody builds the release `.deb` on a workstation.

## Cut a release

1. Make sure `main` is green (the release workflow re-runs the suite,
   but don't tag a known-bad commit).
2. Tag the commit and push the tag:

   ```sh
   git tag v0.0.2
   git push origin v0.0.2
   ```

3. The `Release Debian package` workflow
   (`.github/workflows/release.yml`) does the rest:
   - compiles the Python sources and runs the full test suite
     (`python -m unittest discover -s tests -p 'test_*.py'`) — **if
     the tests fail, the release fails** and nothing is published;
   - runs `packaging/build_deb.sh` with the tag's version (`v0.0.2`
     becomes `0.0.2`);
   - creates (or updates) the GitHub release for the tag and attaches
     `transit-atlas_<version>_all.deb`.

The first release under this numbering, **0.0.1**, was built and
published by hand on 2026-11-15, before this machinery existed. The
build script's output was reconciled path-by-path against that
hand-built package; the layout below is the contract both follow.

## Building locally

```sh
packaging/build_deb.sh 0.0.2        # or: VERSION=0.0.2 packaging/build_deb.sh
# -> dist/transit-atlas_0.0.2_all.deb
```

With no argument, the nearest git tag supplies the version. Requires
`dpkg-deb` (Debian/Ubuntu: `dpkg-dev`). The version is stamped into
`DEBIAN/control` and into the launcher, so `transit-atlas version`
reports the release it came from.

## What the package contains

| Path | Contents |
| --- | --- |
| `/usr/lib/transit-atlas/` | The whole repository checkout: `server.py`, routing, `scripts/`, `web/`, `config/`, `tests/`, docs. |
| `/usr/lib/transit-atlas/data` | Symlink to `/var/lib/transit-atlas/data` (bridges the importer's `./data` lookup with `ATLAS_DATA_DIR`). |
| `/usr/bin/transit-atlas` | Launcher: `serve`, `lan`, `prepare`, `mcp-http`, `tui`, `setup-ollama`, `version`. |
| `/etc/transit-atlas/percival.conf` | Percival companion config (`OLLAMA_MODEL=qwen3:1.7b`, `ATLAS_PORT=8000`). |
| `/lib/systemd/system/transit-atlas.service` | Runs the Atlas as the `transit-atlas` system user. |
| `/var/lib/transit-atlas/data/` | State directory, created by the maintainer scripts (2775, owned by `transit-atlas`). |

The maintainer scripts create the `transit-atlas` system user and the
state directory and run `systemctl daemon-reload` when systemd is
present. They do **no network I/O**: the GTFS database is not bundled
in the package and nothing is downloaded at install time.

## First run on a target machine

```sh
sudo apt install ./transit-atlas_0.0.2_all.deb
transit-atlas prepare     # downloads the GTFS feeds, builds the database (~850 MB)
transit-atlas serve       # http://127.0.0.1:8000
sudo transit-atlas setup-ollama   # optional: Ollama + the Percival local model
```

Removing the package leaves the database and user in place;
`apt purge transit-atlas` removes `/var/lib/transit-atlas` and the
system user as well.
