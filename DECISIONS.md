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

## Unified offline routing architecture decision (2026-11-12)

User selected B: Python for Mac mini GTFS preparation/LAN backend and native Kotlin for offline Android routing. Step 1 adds unified selected-agency SQLite assembly with checksums and fail-closed reference validation; no new agency downloads or invented transfer links. Next choice: how to handle interagency transfers before street graph availability. This is draft code; synthetic tests are not claimed executed.

## Step 2 transfer policy (2026-11-12)

User chose B: official transfers plus clearly labeled estimated walking transfers. Explicit forbidden rules win over proximity, directed transfer rules remain directed, and published minimum transfer times and the 3-minute personal buffer must be respected. Implementation is draft Python for Mac mini testing; do not describe geometric paths as verified sidewalks. Next decision is offline pedestrian/cycling graph strategy.

## Step 3 offline street routing choice (2026-11-12)

User selected B: build walking/cycling street graphs from OpenStreetMap on the Mac mini and store in SQLite for eventual shared Python/Kotlin consumption. Implemented a limited local XML builder and Python Dijkstra router, optionally replacing proximity estimates when configured. Fail closed on missing graph paths; do not claim safe sidewalks, scooter legality, accessibility or a native offline Android routing engine. Next decision: Kotlin port versus strengthening regional graph import first.

## Step 4 native Android routing (2026-11-12)

User selected A: prioritize native Android Kotlin offline journey calculations, preserving Python as the Mac mini preparation/LAN backend. Draft Android code reads installed selected GTFS agency SQLite packs and calculates scheduled journeys without network. Tests and device validation outstanding. Next decision is validation, Kotlin OSM integration, unified pack installer, or user-facing stop/map UI.

## Native Android street graph integration (2026-11-12)

User selected B: integrate the existing OSM/SQLite street graph into Kotlin Android journey routing. A local street graph replaces geometric transfer estimates when installed; missing graph paths are rejected rather than silently approximated. No network routing, implicit agency downloads, or claims of verified sidewalks. Validation, pack delivery and scale are pending.

## Step 6 visual Android journey planner (2026-11-12)

User chose D: prioritize stop search, map-based origin/destination selection and visual itinerary presentation. Preserve all existing transit/OSM routing and LAN download functionality. Native geographic stop canvas is offline, but does not imply a street basemap or verified pedestrian route. Tests committed but not executed.

## Step 7 validation-first routing (2026-11-12)

User chose A: prioritize compilation, synthetic tests, timetable correctness and reproducible verification over feature growth. Repair existing defects in a separate stacked draft PR, configure CI, and clearly distinguish committed tests from executed/passing tests. Do not merge.

## Step 8 parity-first validation (2026-11-12)

User selected B: validate Python and Kotlin with identical golden fixtures and expected journey results. Inspect/fix blocking Step 7 CI failures first. Preserve all existing code and draft PRs; no merge. Golden parity does not replace real feed and device testing.

## Step 9 CI gate (2026-11-12)

User selected A: fix Kotlin test compilation and establish passing Android debug build and Python/Kotlin golden parity CI before expanding routing. Keep all prior work and stacked draft PRs unmerged.

## Termux development bridge (2026-11-12)

Owner selected all three workflows in stages, with separate draft PRs and no merges. Begin with local loopback server and existing consent-first offline pack installation. Keep GTFS imports explicitly initiated and source-aware; do not claim physical device testing from source-level checks. Defer Android ADB debugging bootstrap to separate Stage 3.

## Crostini Command Center increment — 2026-11-13

- Preserved working Crostini SDK/Java/Gradle and existing source. Baseline commands
  passed on host: Python 67 tests; Android debug assembly; cached JVM task followed
  by forced execution of all 22 unit-test dependencies. XML: 30 tests, no failures.
  Initial sandbox failures and timings documented in the baseline report.
- Chose existing stdlib curses approach, with separate typed command adapters and
  a headless JSON interface. No external Python dependency or forced virtualenv.
- Implemented fixed argv actions, local private logs, atomic per-run JSON records,
  commit/dirty-status provenance, Git/tool/storage dashboard and streamed APK hashes.
  Logs and generated outputs remain ignored. No pack, data or device mutations.
- Loaded upstream PR #43 Butler personality and engineering contract. Current
  feature branch includes `db18760`; uncommitted work was preserved across refresh.
- Fresh Kotlin compilation exposed nullable queue-poll warnings, recorded as a
  follow-up rather than mixing routing changes into developer infrastructure.
- Command Center mock isolation repaired after adding Git provenance. Terminal
  launch/Q and headless launcher status passed. Final full Python verification
  command: `bash crostini-dev.sh test`; acceptance totals recorded below.

- Final full Python suite: **72 tests passed in 0.685s** (including five new adapter
  tests). `python3 -m developer_center --run doctor` returned 0 and recorded current
  commit/dirty status. `git diff --check` passed. No physical device, real-feed,
  browser, APK installation, or full offline acceptance claimed.

### Agent handoff — 2026-11-13
- Branch / PR: `feature/crostini-command-center`; publication remains a separate step.
- Scope and authorisation: owner-requested local Crostini baseline and first developer dashboard.
- Files changed: `developer_center/`, launcher, adapter tests, baseline/runbook, roadmap,
  decisions and architecture handoff summary.
- Tests run: 72 Python tests; 30 fresh Android JVM tests; debug assemble; aapt metadata;
  headless dashboard; curses launch/Q; diff whitespace check.
- Tests NOT run: physical device, emulator, airplane-mode, current real-feed coverage.
- Data sources / freshness / coverage: no feed downloads or changes; synthetic tests only.
- Remaining blockers: optional ADB absent; Kotlin nullable queue warnings; remote CI
  for new code not observed; broader developer tooling is not yet implemented.
- Next smallest safe step: review/publish the focused draft, then add read-only test
  report summaries without conflating historical results with current-tree verification.

- Local commit attempt was blocked by missing Git author identity. Requested a
  repository-specific name/email; no global settings changed. Reviewed files remain
  staged and preserved. No push or merge performed during the refresh milestone.
- Recent-run menu rows now show action/exit/duration/time rather than raw JSON that
  hid the result beyond normal terminal width. Detailed provenance remains in JSON.

- Git identity setup: owner authorised repository-local configuration using the
  existing commit author identity, confirmed against the authenticated GitHub name.
  Global Git configuration was left unchanged; local commit workflow is unblocked.

## Command Center historical result summaries — 2026-11-13

- Draft #44 is published at `29c7141`; exact-head CI run `43433186472` passed both
  Python and Android jobs and uploaded the debug APK artifact. No merge performed.
- New branch `feature/crostini-result-summaries` is stacked on #44 (still open).
  Owner requested next task and then a scoped Command Center feature blitz.
- Added read-only unittest-log parsing, JUnit XML aggregation and adjacent Gradle
  APK metadata with source timestamps and explicit unverified-current-tree labels.
  Terminal reports view scrolls and disables build execution while open.
- Nine new deterministic regressions cover false-green hazards: nonzero command
  exit, later failures, missing newest logs, empty/incomplete output, skipped suites,
  malformed/invalid XML and mismatched/duplicate APK metadata.
- `python3 -m unittest discover -s tests -p 'test_developer*.py' -v`: 14 passed.
  `python3 -m developer_center --run test`: exit 0; full suite 81 tests passed.
  Headless status read real saved evidence: Python 81; historical Android XML 30;
  metadata application ID matched the known debug artifact. No Android rerun was
  needed for these Python-only read/report changes; no device test claimed.
- Deferred direct attribution of XML/APK to a source tree: existing outputs have no
  reliable cryptographic source binding. File age is evidence age, not certification.

## Command Center inspection panels — 2026-11-13

- Result-summary slice published as draft #45, head `59ef868`, base #44 branch.
  Its Python CI passed; Android CI was still running at initial inspection.
- Added `inspection.py` for on-demand local Git/SDK/tool presence and regular-log
  tail reads. D/T/G/E/L/H navigation and exclusive headless inspection/log modes.
- Log previews refuse traversal, symlinks and special files using no-follow,
  nonblocking open plus regular-file validation; read at most the last 64 KiB,
  neutralise control characters and preserve the full source file. No network,
  device/pack mutation, setup changes, branch checkout or cleanup action added.
- Six new deterministic tests passed after correcting a fixture's mistaken byte
  count; final test checks actual source bytes remain unchanged. All 20 developer
  tests passed. Full suite via `python3 -m developer_center --run test`: 87 passed.
- Python compilation, diff whitespace and headless Git/environment/help inspection
  passed. Actual environment presence matches the existing Android 35 installation;
  tool presence does not replace build execution. No Android/device rerun claimed.
- User-authorised blitz is delivered as focused stacked PRs, not an architectural
  rewrite. Larger pack/device/clean-build features retain existing consent gates.
- Terminal smoke exercised G Git, E environment, L saved-log view (including Enter
  without launching a build), H help and Q exit. Invalid headless traversal input
  exited 2. No local source/pack/device changes were performed by inspection.
- Result-summary draft #45 exact-head CI run `43434668047` subsequently passed both
  Python and Android jobs for `59ef868`.
