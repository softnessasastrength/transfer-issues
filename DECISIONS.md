# Implementation record — 2026-11-12

- Baseline prototype inspected: schematic corridors, no GTFS or timetable engine. Preserved as prototype.html.
- Chosen portable Python standard-library backend, SQLite, local Leaflet/vanilla JavaScript UI. No build-system dependency for runtime. Versioned API and separate ingestion/database/routing/presentation modules.
- Official downloads succeeded: CTtransit, Hartford Line, WRTA, Amtrak, MBTA. MBTA limited to regional rail; national Amtrak geographically clipped. Source SHA-256, retrieval, last-modified, service range and validation counts retained.
- PVTA official GTFS endpoints at pvta.com/pvta.us returned HTTP 403; published link resolved under /bus_service/ and returned 404 in research. Missing data remains visible. Do not substitute an old aggregator archive as current service.
- GTFS first pass accepted 184 CTtransit routes, 2 Hartford Line routes, 24 WRTA routes, 13 regional Amtrak routes, 14 MBTA commuter rail routes. Counts are initial, subject to validation refinements.
- Calendar-only and calendar_dates-only feeds supported. >24-hour times and prior service day included. Excluded invalid trip records rather than guessing missing times.
- Transfers use configurable geometric estimates (distance ×1.3, walk 4.5 km/h, scooter 12 km/h), not street routing. No accessibility, slope, crossing or scooter-carry guarantee.
- Earliest-arrival connection scan and minute-resolution latest-start search chosen. No real-time cancellation/delay inference.
- ROADMAP.md is authoritative. Apache/macOS, PWA and native iOS remain deferred. Source-aware ingestion is authorized as M0.1.
- Model settings cannot be changed within this active session. Recommended high reasoning for routing/reconciliation; routine edits and processing do not justify additional model orchestration. No subagents or billing changes used.

## Git initialization checkpoint

- Repository resolved through authenticated GitHub connection: private softnessasastrength/transfer-issues, default main, owner/admin/push access. Branch discovery returned no branches; no conflicting history found.
- No pre-existing local Git repository or remote. Existing source, SQLite and downloaded archives preserved in place.
- CLI authentication unavailable: gh reports no logged-in hosts; direct HTTPS Git cannot read a username with prompts disabled. Use connected GitHub operations for publication; ordinary CLI fetch/push still requires authentication.
- Added reproducible source URL seed, non-overwriting registry bootstrap, README/API documentation, ignores and 14 focused synthetic regression tests. No core application restart or deferred feature implementation.
- Tests: 14 passed; Python compilation, SQLite integrity and metadata/service query smoke checks passed. UI/controller, PDF normalization and comprehensive integration remain unfinished.

- Publication completed via authenticated GitHub Git Data operations because CLI auth is unavailable. README bootstrap followed by full-source checkpoint `35543dd5cd98ed33015b4a90db45baef8294dea0`; both preserved in history. Local Git objects were reconstructed from authoritative remote metadata and verified by SHA before setting local refs; remote dates use -0500 offsets, not UTC offsets. Local tracked tree matches published tree.
- No branch protection is enabled. Rulesets query returned HTTP 403 requiring GitHub Pro or public visibility; neither billing nor repository visibility was changed. Feature branches and PR review remain mandatory project policy.

## Desktop proof-of-concept session

- Re-read project instructions, roadmap, local status and remote main. Clean starting tree at bf479477; main unchanged remotely. Branch protection remains disabled and rulesets returns the existing plan restriction. Working on feature/browser-proof-of-concept; no automatic merge.
- User explicitly reprioritized a usable desktop browser proof of concept. Implement the missing controller against the existing API before comprehensive ingestion changes. Deferred deployment/mobile/native work remains untouched.
- Amtrak/New Hampshire expansion recorded as M0.R. Feed-namespaced generic route/trip tables can be reused; configurable geographic selection, optional reservation/boarding provenance and state-qualified discovery are future changes. No NH coverage claim or invented interchange.
- Implemented vanilla JS controller with safe text rendering, Leaflet route shapes/published stops, date-specific route trips, stop departures, journey/return/latest/reachability, source cards, local bookmarks/journal and JSON backups. Transit legs are not represented by invented straight route lines; only estimated ground links are dashed.
- Initial automated browser launch failed because Playwright's bundled executable was absent. System Chromium exists at /usr/bin/chromium; use that for local verification.

## Termux local launch

- User authorized a same-phone Termux proof of concept. Inspected the current launcher and pure-standard-library backend: no platform-specific runtime dependency or architecture rewrite is required.
- Added TERMUX.md for official package setup, GitHub browser authentication for the private repository, feature-branch checkout, one-time ingestion, loopback browser access, restart/stop and Android process limits. Verified the gh package exists in the official Termux repository and consulted official Termux/GitHub CLI documentation.
- No phone access is available; Termux/Android acceptance remains pending. This is a documented execution path, not a tested device deployment. No PWA/native app, background tasks or feed refresh was implemented.

## Ember (_muse) session — 2026-11-14

- Working branch: `mobility-bubble_muse`, based on `feature/browser-proof-of-concept`. Session run under Branden's MUSE ENGINEERING HANDOFF (2026-11-14): Priority A, Percival Mobility Bubble; merge authority per handoff §6 as confirmed by the owner.
- Groundwork re-verified in a fresh environment: tree reconstructed from the private repo via the GitHub connector; `python3 scripts/prepare_data.py` downloaded and imported five official feeds on 2026-11-14 (CTtransit 184 routes / 20,645 trips, service 20260830–20270109; Hartford Line 2 / 73, 20261005–20271004; WRTA 24 / 7,898, 20261114–20270212; Amtrak regional clip 13 / 683, 20261108–20271108; MBTA commuter rail 14 / 2,036, 20261106–20261212). PVTA download failed again with HTTP 403 from the official endpoint; the gap remains visible in `sources.json`, coverage responses and the UI. Nothing about PVTA service was inferred.
- Baseline before changes: 17 Python tests passed; Python compilation passed.
- Implemented `/api/v1/bubble` (new `bubble.py`): Percival Mobility Bubble. 60-minute default budget; walking first/last mile via the existing estimated ground links; a stop counts as reachable only with a feasible return home by the end of the window (optional `visit` seconds consume the window). Return feasibility is computed by one reverse connection scan (`latest_return_departures`) iterated to a fixpoint over walk/transit chains. Three-way classification: reachable / unreachable (with reasons `no_outbound_within_budget`, `no_feasible_return`) / unknown (feeds missing, failed or out of service period — never counted as unreachable). Responses expose per-source provenance (status, retrieved_at, service period, SHA-256) and the loaded coverage rows.
- Defect found and fixed during verification: the first reverse-scan version missed returns that chain walk -> transit -> walk -> transit (single-pass ordering). Cross-validation against brute-force `routing.plan` caught 1 miss in 12; after the fixpoint fix, 20/20 sampled brute-force checks agree, and the Hartford-station 60-minute bubble corrected from 672 to 1,034 reachable stops. The reverse scan remains an approximation of scan semantics (bounded walk-propagation passes); sampled agreement is the evidence, not a proof.
- Real-data verification, Tuesday 2026-11-17 (inside every loaded feed's service period): Hartford -> Springfield rail plan with return; route 905 (`cttransit:16545`) 31 weekday trips / 40 stops / 6 shapes; trip timetable for `hartford:54020`; departures from `hartford:6`; plans Hartford -> New Haven, Hartford -> Worcester (Amtrak), Hartford -> Enfield, Hartford -> Manchester CT, Worcester -> Hartford all found. Windsor (hartford:7) is correctly NOT in the 08:00 60-minute bubble: earliest return arrives Hartford 09:24.
- Browser acceptance (previously blocked in the old build environment) PASSED here: Playwright + Chromium installed as dev-only tooling in /tmp; `tests/browser_smoke.cjs` passed end-to-end (905 browse/timetable, rail return journey, bookmark/journal persistence, literal-text rendering, backup export/import, source cards, zero page errors) with ATLAS_DATE=2026-11-17. A bubble-button smoke also passed: UI reported exactly the API's 1,034 stops with PVTA named as not evaluable. No macOS/Safari claim; M0.D's Mac-hardware acceptance remains open.
- UI increment (bounded): "Mobility bubble · 60 min, with a way home" button wired to the new endpoint with visit=0 semantics stated in the result text (pure travel window); the endpoint itself accepts a `visit` parameter for API callers.
- Small wins: removed a dead `functools` import from server.py; API.md gained the `bubble` contract row; TESTING.md updated. Everything else identified as large (M0.1 PDF ingestion build, bubble performance work, Metro UI build-out, M0.R) is scoped in CODEX_HANDOFF.md, not built here.
- Tests after changes: 29 Python tests pass (12 new bubble tests with synthetic fixtures, including a reverse-scan-vs-plan agreement test); `node --check web/app.js` passes; Python compilation passes. Bubble endpoint latency on the full Hartford dataset is ~15 s locally; recorded as a known limitation in CODEX_HANDOFF.md.
