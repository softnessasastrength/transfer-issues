# CODEX_HANDOFF — Southern New England Transit Atlas (transfer-issues)

AUTHOR: Ember (_muse)
AUTHORITY: Branden's MUSE ENGINEERING HANDOFF (2026-11-14) and his operating
split of the same evening: Ember implements small verifiable things; Codex is
reserved for the big stuff. Merge authority per handoff §6.
EVIDENCE: DECISIONS.md session entries 2026-11-14 (Mobility Bubble; PVTA
User-Agent fix); TESTING.md 2026-11-14 sections; 30 passing Python tests;
browser smoke passed in the Ember environment; PVTA imported and verified
against the API on real data.
REQUESTED_ACTION: Pick up the scoped big items below in ROADMAP priority
order. Do not treat any of them as started. M1/M2/M3 remain deferred and are
NOT part of this handoff.

## COOK LIST — start here (added 2026-11-14 evening, for the Codex TUI session)

The owner is opening this repo in the Codex TUI and starting immediately.
Begin at task 1 and work in order. A task is done when its tests pass and
DECISIONS.md records it. Owner's model note (2026-11-14): he is running the
Luna-tier model at medium reasoning for most of this work — keep tasks
bounded and verification explicit, as this list already does.

1. **Stop lookup endpoint (NEW — unblocks Percival).** Percival's F-001
   "come to me" slice is merged in the `percival` repo and must currently
   hard-code raw stop IDs (`pvta:5101`, `hartford:6`): the Atlas API has no
   way to resolve a place name to stops. Add `GET /api/v1/stops?q=<text>`
   (and/or by-feed listing) returning matching stops with id, name, feed,
   and coordinates from loaded data only. Document it in API.md; add tests.
   Percival's friend registry (Codex work in that repo) consumes this next.
2. **Plan/bubble latency.** Measured from Percival's live integration:
   ~15–25 s per `/api/v1/plan` call on the full six-feed network; bubble
   ~15 s. This is scoped item 2 below — it moves up because Percival now
   depends on plan calls at interactive timescales.
3. **Then the scoped items below in their numbered order** (M0.1 PDF
   fallback, Metro map UI, API v1 contract, M0.R), skipping item 2, which
   task 2 above already covers.

COORDINATION: Ember is concurrently building Vercel deployability for the
`percival` repo, then for THIS repo, on `*_muse` branches. Do not build
deployment scaffolding here; Ember's work lands it, and this file will be
updated when it does.

## State of the repo after the 2026-11-14 Ember session

- Branch `mobility-bubble_muse` (from `feature/browser-proof-of-concept`)
  adds `/api/v1/bubble` (Percival Mobility Bubble), 12 fixture tests, a
  bounded UI button, and documentation. See DECISIONS.md for the full record.
- The atlas runs end-to-end: `python3 scripts/prepare_data.py` (first run),
  `python3 scripts/run_local.py`, http://127.0.0.1:8000. Feeds imported
  2026-11-14; service periods are listed in DECISIONS.md.
- Branch `pvta-user-agent-fix_muse` (from `feature/browser-proof-of-concept`)
  fixes the feed downloader's missing User-Agent header. PVTA now downloads
  and imports (62 routes / 13,381 trips / 1,973 stops, service
  20261102–20261219); the earlier "PVTA feed unavailable" conclusion was a
  UA artifact and is corrected in DECISIONS.md.

## Scoped big items for Codex

### 1. M0.1 PDF fallback ingestion build (ROADMAP M0.1 acceptance 2, 3, 6, 7)
Build the reviewed-PDF pipeline: source registry entries for agencies
without usable GTFS, PDF extraction with explicit OCR provenance, normalized
route/direction/timepoint/calendar tables coexisting with GTFS in SQLite,
confidence/ambiguity gating so unreviewed or ambiguous records never enter
routing, and GTFS+PDF fixture tests. No invented stops, times or geometry.
STATUS CHANGE (2026-11-14): PVTA is no longer the motivating case — its
official GTFS downloads and imports since the User-Agent fix, so Springfield /
Holyoke / Chicopee / Westfield bus journeys already evaluate from GTFS. This
build is now resilience work (a UA filter or endpoint change could cut a
feed off again) and the route for agencies that genuinely publish no GTFS —
still required by M0.1 acceptance, but no longer a Springfield blocker and
no longer the single largest M0 gap.

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

### 6. PVTA source discovery — RESOLVED 2026-11-14, do not re-run as a blocker
Closed by the User-Agent fix: the official endpoint
`https://www.pvta.com/g_trans/google_transit.zip` serves the current feed
(HTTP 200) to any client sending an explicit User-Agent; the 403s were
UA filtering of the default urllib/curl agents, not feed unavailability.
The feed imports fully and Springfield-area coverage now evaluates from
GTFS. Remaining value in alternate sources (state DOT mirror, official PDF
timetables) is resilience only, under item 1 — worth having if a future
endpoint change recurs, not a prerequisite for anything.

## Reproducible commands

```bash
python3 -m unittest discover -s tests -v     # 30 tests, all passing
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

- 30 Python unit/HTTP tests pass (`python3 -m unittest discover -s tests`),
  including 12 Mobility Bubble fixture tests and a stubbed regression test
  asserting feed downloads send the project's User-Agent header.
- Python compilation of all modules; `node --check web/app.js`.
- Fresh `scripts/prepare_data.py`: all six official feeds imported with no
  refresh errors, including PVTA (62 routes / 13,381 trips / 1,973 stops,
  service 20261102–20261219). Springfield evidence on real data for Tuesday
  2026-11-17: 167 departures from Court Square (`pvta:1495`); Springfield
  local plan Union Station -> Court Square on the G2; Hartford ->
  Court Square plan chaining Hartford Line rail + a PVTA P11 leg; bubble
  from hartford:6 now reports zero unknown feeds (PVTA's 1,973 stops moved
  from unknown to evidence-based classification), and a Springfield Union
  Station bubble finds 580 reachable PVTA stops.
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
