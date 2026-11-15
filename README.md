# Southern New England Transit Atlas

An independent, local-first transit exploration project for Connecticut, Massachusetts and Rhode Island, with priority attention to Hartford, Springfield, Enfield, Windsor Locks, Manchester, Holyoke, Chicopee, Westfield, New Haven and Worcester.

**Status: desktop proof of concept implemented; browser acceptance is blocked in the build environment. Not a completed or travel-ready atlas.** This repository preserves the work already underway. Read [ROADMAP.md](ROADMAP.md) for authoritative priorities and acceptance criteria, and [DECISIONS.md](DECISIONS.md) for implementation evidence and unresolved issues.

## What exists

- Original `prototype.html`: a standalone interactive **schematic**, not geographic routing or a timetable.
- Python standard-library GTFS importer and a generated local SQLite database, with feed metadata, checksums and basic validation reports.
- Separate database queries, an initial connection-scan router, and `/api/v1/` HTTP endpoints.
- Desktop controller for geographic route/stop browsing, timetables, outbound/return/latest/reachability searches, source cards, browser-local bookmarks/journal and JSON backups; Leaflet 1.9.4 is vendored.
- Authoritative roadmap and persistent agent/workflow instructions.

**Not yet implemented or accepted:** reviewed PDF fallback, unified PDF/GTFS provenance tables, safe versioned refresh/rollback, complete source discovery, comprehensive validation, browser acceptance and macOS hardware checks. Apache/macOS production hosting, PWA, native iOS and the New Hampshire/intercity expansion remain later milestones.

For same-phone Android hosting in Termux, see [TERMUX.md](TERMUX.md). Device validation remains pending.

## Try the desktop proof of concept

On your Mac mini, use a checkout of the `feature/browser-proof-of-concept` branch and Python 3.11 or newer. In Terminal, inside this repository:

```bash
python3 --version
# First run only: downloads official feeds and creates the local database.
python3 scripts/prepare_data.py
# Subsequent launches reuse your existing database without downloads.
python3 scripts/run_local.py
```

Open **http://127.0.0.1:8000** in your desktop browser. Stop the server with Control-C. No Apache, Node, paid hosting or cloud backend is required to run it. This is a portable local launch procedure, not a verified macOS deployment package.

Start with **Browse routes → 905**, select a trip for its timetable, or click **Hartford** to zoom to published stops. For a rail example, choose **HARTFORD [hartford:6]** to **SPRINGFIELD [hartford:9]**. Pick a date within the downloaded feed's service period (see Data & sources); expired feeds may correctly yield no trips. The `2026-11-12` example was checked directly against the development database, not as a live service guarantee. Network access is needed for street tiles, but official shape/stop layers are local. Missing tiles show a visible notice.

Bookmarks and journal entries are device/browser/origin-local; use **My discoveries → Export my data** before clearing browser storage or moving machines. Import appends entries to preserve existing records. No personal records are committed to Git.

A failed agency download can leave coverage incomplete. An empty result is not proof that no real journey exists. Reservation/seat availability and fares are not checked.

## Feed coverage at the checkpoint

| Feed | Local import | Scope / caveat |
|---|---|---|
| CTtransit | Successful | 184 routes; loaded service periods vary by division |
| CTrail / Hartford Line | Successful | 2 feed routes; planned schedule, not live arrivals |
| WRTA | Successful | 24 routes; exception-date calendars |
| Amtrak | Successful | 13 routes intersecting regional geographic scope |
| MBTA | Successful | 14 commuter-rail routes only; bus/subway excluded |
| PVTA | Successful | 62 routes; service period 2026-11-02 to 2026-12-19 in the 2026-11-14 import. Earlier HTTP 403s were a User-Agent artifact in the downloader, fixed 2026-11-14 |
| RIPTA / other CT, MA, RI agencies | **Not imported** | Required expanded coverage remains pending |

These are initial import counts, not proof of full correctness or current service. Downloaded GTFS, generated SQLite and validation reports are **not committed**. Re-run ingestion to produce local data. No schedules from unofficial or historical sources have been substituted for missing current feeds.

## Architecture

```text
Official GTFS ZIP -> import_gtfs.py -> local SQLite
                                    |
                              database.py
                                    |
                               routing.py
                                    |
                          server.py /api/v1/
                                    |
                        web/ (desktop controller)
```

- `import_gtfs.py`: CSV/ZIP parsing, calendar and exception normalization, basic validation.
- `database.py`: read-only SQLite access, active service calculation, connections and timetables.
- `routing.py`: earliest arrival, geographic transfer estimates, latest-start search.
- `server.py`: development HTTP server and versioned JSON endpoints; see [API.md](API.md).
- `config/feeds.json`: checked-in official source URLs; no generated feed content or secrets.
- `data/`: ignored raw archives, source metadata, validation output and normalized SQLite.
- `tests/`: isolated synthetic unit tests; these do not establish full transit correctness.

The server defaults to loopback. Apache/macOS production deployment, launchd, PWA/offline support and native iOS remain deferred until explicitly authorized. The core uses no cloud runtime or paid services.

## Local development

Requires Python 3.11+ and an internet connection for initial official feed downloads. The backend uses only the standard library. Work from the repository root:

```bash
python3 scripts/prepare_data.py
python3 -m unittest discover -s tests -v
python3 server.py
```

The server warms its stop network and selected service-day connection list
before accepting requests. Set `ATLAS_DATE=YYYY-MM-DD` to select a date;
otherwise startup uses today's date. Both remain cached in the server process.

The first command seeds `data/sources.json` only if missing, downloads feeds and rebuilds `data/atlas.sqlite`. Downloads may be blocked by agency websites. It does not create recurring jobs. **The current refresh implementation overwrites local archives and database rather than retaining audit versions. Back up `data/` before refreshing an existing installation; versioned refresh/rollback is an open core requirement.** Stop the server before rebuilding because its connection cache is process-local.

Open `http://127.0.0.1:8000/api/v1/meta` to inspect the API. The page at `/` is the desktop proof of concept. Open `prototype.html` directly for the original schematic only.

For an existing database, the server accepts `ATLAS_DATA_DIR=/absolute/data/path`; the importer currently writes to the repository's `data/` folder. Do not expose this development server on an unsecured remote interface.

## Important calculation limits

- Scheduled feasibility only; no real-time cancellations, alerts or delays.
- Ground links are straight-line distance × 1.3 at 4.5 km/h walking or 12 km/h scooter. They are not verified street paths, safe crossings, slopes, accessibility or scooter-carry permissions.
- The transfer radius applies per link, not to total journey distance or battery range.
- GTFS route/trip-scoped transfer constraints are not yet modeled. Parent-station handling, zero-duration connections and other edge cases require broader testing.
- Frequency trips and trips with invalid/missing times are excluded, not interpolated.
- Prior-day 24+ hour service and next-day connections are modeled, but midnight/DST and multi-agency correctness require further acceptance tests.
- Latest-start search has one-minute resolution and is bounded by the selected deadline and loaded feeds.
- The current importer is **not** a full GTFS specification validator. Unified provenance, conflicting publications, version rollback and reviewed PDF activation gates are still pending.

## Development workflow

Read [AGENTS.md](AGENTS.md), [ROADMAP.md](ROADMAP.md) and repository rules before starting. For substantial changes:

```bash
git fetch origin
git switch main
git pull --ff-only
git switch -c feature/descriptive-name
# implement and validate focused changes
git add <specific-files>
git diff --cached
git commit -m "Describe the verified change"
git push -u origin feature/descriptive-name
```

Open a pull request with tests and known limitations. Do not merge significant PRs automatically. Never force-push main or rewrite remote history. Keep the roadmap synchronized; deferred work requires explicit authorization. Small documentation fixes may be committed directly if repository rules permit.

Local CLI authentication is separate from the ChatGPT GitHub connection. At initialization the connector had repository write access, while `gh auth status` reported no authenticated hosts and direct Git HTTPS access could not obtain a username. Use your approved GitHub authentication method locally; never put credentials in source, remote URLs or chat.

## Third-party assets

Leaflet 1.9.4 is Copyright (c) 2010–2023 Volodymyr Agafonkin and 2010–2011 CloudMade, distributed under BSD-2-Clause; see `web/vendor/LEAFLET-LICENSE`. Transit data remains subject to the respective publishers' terms and is not relicensed by this project.
