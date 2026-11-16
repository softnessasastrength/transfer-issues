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
   - checks out Percival Core at the ref pinned in
     `packaging/PERCIVAL_PIN` (see *Bundled Percival Core* below);
   - compiles the Python sources and runs **both** full test suites —
     the Atlas suite and the Percival Core suite, each with
     `python -m unittest discover -s tests -p 'test_*.py'` — **if
     either suite fails, the release fails** and nothing is published;
   - runs `packaging/build_deb.sh` with the tag's version (`v0.0.2`
     becomes `0.0.2`) and the Percival checkout as `PERCIVAL_DIR`;
   - creates (or updates) the GitHub release for the tag and attaches
     `transit-atlas_<version>_all.deb`.

The first release under this numbering, **0.0.1**, was built and
published by hand on 2026-11-15, before this machinery existed. The
build script's output was reconciled path-by-path against that
hand-built package; the layout below is the contract both follow.

## Dev builds

Every push to `dev` also builds a package, so the current state of
`dev` is installable and testable without waiting for a promotion to
`main` and a tagged release. The `Build dev Debian package` workflow
(`.github/workflows/build-dev.yml`) mirrors the release workflow's
gates — it checks out Percival Core at the pinned ref and runs
**both** test suites; a red suite fails the build and nothing is
packaged — then builds the `.deb` and uploads it as an **Actions
artifact** (no GitHub Release, no tag). It can also be run manually
from the Actions tab against any ref.

To get one: open the repository's **Actions** tab, pick the
`Build dev Debian package` run for the commit you want, and download
the `transit-atlas-dev_<version>_<short-sha>` artifact from the run
page. Artifacts are kept for 14 days.

Dev builds are **unsigned test builds**. Their version stamp is the
latest released version plus a fourth, run-number component (for
example `0.0.3.42`): releases always carry exactly three components,
so a dev build can never be mistaken for one, and the stamp sorts
after the release it follows and before the next one. The commit a
dev build came from is in the artifact name. Releases still come
only from `v*` tags on `main`, as above.

## Building locally

```sh
git clone https://github.com/softnessasastrength/percival /tmp/percival
git -C /tmp/percival checkout "$(grep -v '^#' packaging/PERCIVAL_PIN | tr -d '[:space:]')"
PERCIVAL_DIR=/tmp/percival packaging/build_deb.sh 0.0.2
# -> dist/transit-atlas_0.0.2_all.deb
```

With no version argument, the nearest git tag supplies the version.
Requires `dpkg-deb` (Debian/Ubuntu: `dpkg-dev`). The version is stamped
into `DEBIAN/control` and into the launcher, so `transit-atlas version`
reports the release it came from — and the Percival pin it bundles.

`PERCIVAL_DIR` is **required**: a build without the Percival tree
would silently produce the pre-bundle artifact, so the script refuses
and says what is missing.

## Bundled Percival Core

Since 0.0.2 the package carries **two services from two repositories**:
the Atlas (this repo) and Percival Core
(`softnessasastrength/percival`). The repos stay separate; Percival
enters the package only as a build input, staged whole under
`/usr/lib/percival-core` with a `BUILD_INFO` file recording the exact
ref it came from.

Which Percival ships is decided by **`packaging/PERCIVAL_PIN`** — the
commit SHA of `percival`'s `main` to bundle. To bump it:

1. Note the new `percival` main head and replace the SHA in
   `packaging/PERCIVAL_PIN`.
2. Record the bump (old → new SHA, why) in `DECISIONS.md`.
3. Open the usual PR into `dev`; the release workflow will check out
   exactly that ref and gate on the Percival suite before building.

Never point the pin at a branch name or a tag that can move: the pin
is the provenance record for every shipped package.

## What the package contains

| Path | Contents |
| --- | --- |
| `/usr/lib/transit-atlas/` | The whole repository checkout: `server.py`, routing, `scripts/`, `web/`, `config/`, `tests/`, docs. |
| `/usr/lib/transit-atlas/data` | Symlink to `/var/lib/transit-atlas/data` (bridges the importer's `./data` lookup with `ATLAS_DATA_DIR`). |
| `/usr/lib/percival-core/` | The whole pinned Percival Core checkout: `src/percival_core/`, `api/`, `public/`, `scripts/run_local.py`, `tests/`, plus `BUILD_INFO` (repo + pinned ref + build stamp). |
| `/usr/bin/transit-atlas` | Launcher: `serve`, `lan`, `prepare`, `mcp-http`, `tui`, `setup-ollama`, `percival`, `setup`, `version`. |
| `/etc/transit-atlas/percival.conf` | Percival companion config (`OLLAMA_MODEL=qwen3:1.7b`, `ATLAS_PORT=8000`). |
| `/lib/systemd/system/transit-atlas.service` | Runs the Atlas as the `transit-atlas` system user. |
| `/lib/systemd/system/percival.service` | Runs Percival Core's front door (127.0.0.1:8123) as the `transit-atlas` system user; `Wants` the Atlas but starts standalone. |
| `/var/lib/transit-atlas/data/` | State directory, created by the maintainer scripts (2775, owned by `transit-atlas`). |
| `/var/lib/transit-atlas/percival/` | Reserved state directory for Percival Core, created by the maintainer scripts (owned by `transit-atlas`). |

The maintainer scripts create the `transit-atlas` system user and the
state directory and run `systemctl daemon-reload` when systemd is
present. They do **no network I/O**: the GTFS database is not bundled
in the package and nothing is downloaded at install time.

## First run on a target machine

Install, then one command:

```sh
sudo apt install ./transit-atlas_0.0.2_all.deb
sudo transit-atlas setup
```

`transit-atlas setup` is install-and-setup in one, and it is safe to
re-run:

- If the Atlas database is absent from the data directory, it runs
  data preparation first — as the `transit-atlas` service user where
  the system layout requires it, so the database belongs to the user
  the services run as. An existing database is left untouched.
- Under systemd it enables and starts both units
  (`transit-atlas.service`, `percival.service`). Without systemd
  (WSL, containers) it starts both servers in the background with
  `nohup`, logging next to the data directory, and skips any service
  that is already answering.
- Either way it prints both URLs — Atlas
  <http://127.0.0.1:8000>, Percival <http://127.0.0.1:8123> — and how
  to stop the services.

The pieces are still available individually:

```sh
sudo -u transit-atlas transit-atlas prepare   # downloads the GTFS feeds, builds the database (~850 MB)
sudo systemctl start transit-atlas percival   # Atlas http://127.0.0.1:8000, Percival http://127.0.0.1:8123
transit-atlas serve       # foreground Atlas against your own data dir
transit-atlas percival    # Percival Core front door: http://127.0.0.1:8123
sudo transit-atlas setup-ollama   # optional: Ollama + the Percival local model
```

**Prepare runs as the service user.** The seed registry and the
database live in `/var/lib/transit-atlas/data`, owned by the
`transit-atlas` user and not readable by anyone else, so a bare
`transit-atlas prepare` from a personal account fails with
`Permission denied` on `data/sources.json`. Either let
`transit-atlas setup` handle it (it prepares as the service user) or
run prepare in the `sudo -u transit-atlas` form above. The printed
instructions are kept honest on this point deliberately: a command
that cannot work for the person reading it is a bug, not a shortcut.

Removing the package leaves the database and user in place;
`apt purge transit-atlas` removes `/var/lib/transit-atlas` and the
system user as well.
