# CODEX_HANDOFF — Southern New England Transit Atlas (transfer-issues)

AUTHOR: Ember (_muse)
AUTHORITY: Branden's MUSE ENGINEERING HANDOFF (2026-11-14) and his operating
split of the same evening: Ember implements small verifiable things; Codex is
reserved for the big stuff. Merge authority per handoff §6.
EVIDENCE: DECISIONS.md session entry 2026-11-14; TESTING.md 2026-11-14 section;
29 passing Python tests; browser smoke passed in the Ember environment.
REQUESTED_ACTION: Pick up the scoped big items below in ROADMAP priority
order. Do not treat any of them as started. M1/M2/M3 remain deferred and are
NOT part of this handoff.

## State of the repo after the 2026-11-14 Ember session

- Branch `mobility-bubble_muse` (from `feature/browser-proof-of-concept`)
  adds `/api/v1/bubble` (Percival Mobility Bubble), 12 fixture tests, a
  bounded UI button, and documentation. See DECISIONS.md for the full record.
- The atlas runs end-to-end: `python3 scripts/prepare_data.py` (first run),
  `python3 scripts/run_local.py`, http://127.0.0.1:8000. Feeds imported
  2026-11-14; service periods are listed in DECISIONS.md. PVTA still 403.

## Scoped big items for Codex

### 1. M0.1 PDF fallback ingestion build (ROADMAP M0.1 acceptance 2, 3, 6, 7)
Build the reviewed-PDF pipeline: source registry entries for agencies
without usable GTFS (PVTA first, if an official PDF timetable source can be
verified), PDF extraction with explicit OCR provenance, normalized
route/direction/timepoint/calendar tables coexisting with GTFS in SQLite,
confidence/ambiguity gating so unreviewed or ambiguous records never enter
routing, and GTFS+PDF fixture tests. No invented stops, times or geometry.
This is the single largest remaining M0 gap: it is the only route to
evaluating Holyoke / Chicopee / Westfield / Springfield bus journeys.

### 2. Mobility Bubble performance + correctness hardening
`/api/v1/bubble` takes ~15 s on the full Hartford dataset (forward scan +
fixpoint reverse scan over ~100k connections, per-request). Options: cache
per-(date, feeds) connection-derived structures, index connections by trip
for the reverse pass, or precompute latest-return tables per service day.
Also replace the sampled cross-validation with an exhaustive
reverse-scan-vs-plan agreement check on a reduced fixture region, and
characterize the remaining approximation (bounded walk-propagation passes).
Keep the three-way classification semantics unchanged.

### 3. Metro-inspired map UI build-out (beyond the bounded bubble button)
The owner wants a map-first, Metro-inspired interface. Ember wired only a
single bubble button + result text into the existing controller. The full
build-out (bubble visualization as a geographic layer with reachable /
unreachable / unknown rendering, city-level summaries, time scrubbing) is a
design + implementation project: scope it against ROADMAP M0.D acceptance,
keep unknown visibly distinct from unreachable, and keep all rendering on
published stop coordinates only.

### 4. API v1 contract completion (API.md "Known contract gaps")
Unified PDF confidence/validation statuses, per-trip provenance/expiry
gates, pagination for meta/reachability-class responses, and full parameter
validation. Required before M0/M0.1 acceptance and before any native client
depends on v1. Coordinate with item 1 (statuses originate in ingestion).

### 5. M0.R regional/intercity rail + New Hampshire (QUEUED in ROADMAP)
Configurable coverage policy replacing the importer's hard-coded geographic
rectangle and MBTA rail-only filter; operator/ticketing metadata;
state-qualified place discovery; Downeaster/NH investigation with verified
sources only. Do not start before items 1–2 stabilize ingestion and routing.

### 6. PVTA source discovery (research task, feeds item 1)
The official GTFS endpoints returned 403/404 in repeated checks (latest:
2026-11-14, HTTP 403 recorded in data/sources.json). Find whether PVTA
publishes GTFS through another official channel (state DOT feed, developer
page change), recording publisher, URL, retrieval/effective dates per the
M0.1 source hierarchy. An old aggregator archive is not acceptable as
current service.

## Reproducible commands

```bash
python3 -m unittest discover -s tests -v     # 29 tests, all passing
python3 scripts/prepare_data.py              # first run only; downloads feeds
python3 scripts/run_local.py                 # http://127.0.0.1:8000
# Browser smoke (needs Playwright + Chromium as dev-only tooling):
#   ATLAS_DATE=2026-11-17 node tests/browser_smoke.cjs
# Bubble smoke:
#   curl 'http://127.0.0.1:8000/api/v1/bubble?from=hartford:6&date=2026-11-17&time=28800&budget=3600'
```

## Verification status — two lists, never blurred

Owner protocol (2026-11-14): "Test as far as your environment lets; ping if
the Mac mini is needed."

### VERIFIED in Ember's environment (Linux sandbox, 2026-11-14)

- 29 Python unit/HTTP tests pass (`python3 -m unittest discover -s tests`),
  including 12 new Mobility Bubble fixture tests.
- Python compilation of all modules; `node --check web/app.js`.
- Fresh `scripts/prepare_data.py`: five official feeds imported; PVTA
  failed with HTTP 403 (recorded, not filled).
- `scripts/run_local.py` served the atlas; every `/api/v1/` endpoint
  exercised with curl on real data for Tuesday 2026-11-17 (inside all
  loaded service periods), including Hartford <-> Springfield with return
  and the new `/api/v1/bubble` (1,034 reachable stops from hartford:6,
  cross-validated against brute-force plan() on 20 sampled stops, zero
  mismatches after the fixpoint fix).
- Browser acceptance: `tests/browser_smoke.cjs` PASSED (Playwright +
  Chromium installed as dev-only tooling in /tmp), plus a bubble-button
  smoke: UI count matched the API exactly, zero page errors.

### NEEDS THE MAC MINI — ping items for Branden (not verified anywhere)

1. README launch procedure on the mini itself: checkout
   `feature/browser-proof-of-concept` (after the mobility-bubble merge),
   `python3 scripts/prepare_data.py`, `python3 scripts/run_local.py`,
   open http://127.0.0.1:8000 in the desktop browser.
2. macOS browser acceptance: the full smoke flow in Safari/Chrome on
   macOS, including map tiles, route 905 browsing and a rail return query.
3. M0.T Termux/Android acceptance (phone, not mini): first import, page
   and map interaction, timetable + return query, journal persistence
   across restart.
4. Any Apple Silicon performance sanity check of the ~15 s bubble call on
   the M4 mini.

## Known limitations (honest list)

- Bubble reverse scan is an approximation verified by sampling (20/20
  brute-force agreement after the fixpoint fix), not exhaustively proven.
- Bubble latency ~15 s on full data (item 2).
- Hartford Line headsigns in the published feed are sometimes misleading
  (e.g. a Hartford-bound departure labelled "Northbound to Hartford" from
  Windsor); the atlas displays feed data as published and does not correct
  it. Worth a validation-report note, not a silent rewrite.
- MBTA import reports 605 invalid stop coordinates and 6,218 scoped
  transfer rules not supported (in data/validation.json); both pre-date
  this session and are unaddressed.
- macOS/Safari and Android/Termux acceptance remain unperformed.
