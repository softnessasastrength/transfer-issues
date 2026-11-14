# Southern New England Transit Atlas — authoritative implementation plan

Read this file and relevant project instructions at the start of every work session. Record new requests here, identify dependencies, preserve priority, and verify acceptance criteria before marking complete. Explain conflicts rather than silently changing priorities. No recurring monitoring or scheduled tasks are authorized.

## M0 — Core atlas (IN PROGRESS; current priority)

Deliver a maintainable working application derived from `prototype.html`, official GTFS import and validation, geographic routes/stops, date-specific calendars and exceptions, timetables, transfers, last-trip and return feasibility, multi-agency reachability, explicitly estimated walking/scooter connections, bookmarks, discovery journal, source dates, missing-feed documentation, tests and run instructions.

Priority geography: Hartford, Springfield, Enfield, Windsor Locks, Manchester, Holyoke, Chicopee, Westfield, New Haven, Worcester.

Acceptance: import available official archives and report failures honestly; exercise planner calendar, overnight, transfer and return behavior; test API and browser interactions; document limitations and reproducible setup; deliver source and data. Missing PVTA data is a substantive coverage gap, not proof that service does not exist. Do not mark full requested coverage complete until it is obtained.

## M1 — macOS / Apache self-hosting (DEFERRED; explicit authorization required)

Depends on stable and validated M0. Target Mac mini M4 16 GB and MacBook Air M4, Apple Silicon, Apache HTTP Server 2.4+. Apache is the web-facing reverse proxy; SQLite remains primary unless measured technical limitations justify reconsideration. Provide macOS installation/configuration, LAN/iPhone access, persistent GTFS/data/bookmarks/preferences, start/stop/restart/backup/update scripts, optional launchd startup, example virtual hosts, HTTPS/authentication/safe remote-access guidance. Must work without cloud infrastructure or paid hosting. Preserve existing data throughout migration.

Acceptance: test installation, restart persistence, backup/restore, LAN access, proxy headers and secure access on macOS before completion. No Apache configuration or deployment implementation authorized yet.

## M2 — Mobile web / PWA (DEFERRED; explicit authorization required)

Depends on successful M1 local deployment. Baseline responsive core UI is in M0; this phase adds iPhone/desktop optimization, touch map improvements, installable PWA where supported, offline selected maps and downloaded transit data, persistent bookmarks/history, small-screen discovery and timetables. Respect map-provider offline caching terms. No service worker or PWA conversion yet.

Acceptance: iPhone Safari/browser tests, install/offline behavior, selected data expiry visibility and persistence tests. Device-browser storage export must remain recoverable.

## M3 — Native iPhone client investigation (DEFERRED; explicit authorization required)

Depends on stable versioned API and secure M1 deployment. Evaluate SwiftUI or justify alternatives. Reuse backend routing and GTFS engine. Maps/routes/stops/schedules, opt-in location, saved trips/favorites, feasible offline data, secure Mac mini connection and minimal third-party cloud dependence. Do not add iOS dependencies to the backend.

Acceptance for investigation: architecture proposal, API gap analysis, offline/security plan and justified implementation estimate. Implementation requires separate authorization.

## Architecture decisions and future friction

- Python standard library + SQLite; no platform-specific core dependencies. GTFS ingestion, database access, routing, HTTP API and browser UI are separate modules.
- Versioned `/api/v1/` JSON endpoints let Apache proxy and future clients reuse the engine.
- Runtime paths are configurable. Static files and the backend can be hosted separately later with no routing rewrite.
- Core bookmarks/preferences/journal use browser localStorage with JSON export/import. This is device-local persistence, not server sync. M1 must add authenticated per-user persistence plus import migration; do not silently discard browser records.
- Core HTTP server is a loopback development server. M1 must select a production serving arrangement, authentication and trusted-proxy handling before exposing it remotely.
- Basemap tiles require network; transit data and vector layers are local. M2 must choose offline map licensing and storage deliberately.
- No automated feed refresh, launchd jobs, Apache setup, PWA or native app work has begun.

## M0.1 — Source-aware ingestion (AUTHORIZED; integrated with core)

Scope expanded to Connecticut, Massachusetts and Rhode Island plus relevant connecting services. Priority: stabilize GTFS first, then incrementally implement official PDF fallback. This does not authorize M1–M3.

Source hierarchy: current official GTFS → official structured API/timetables → current official PDF → official HTML → archived official sources for historical reference only. Discover official websites/developer resources and record publisher, URL, retrieval/effective dates, service period and supersession evidence. Upload date alone is not effective date.

Requirements: source registry and raw/normalized/derived separation; coexisting GTFS and reviewed PDF schedules in SQLite; route/direction/timepoints/times/calendars/notes/confidence/ambiguity; explicit OCR provenance; chronology, stop ordering, duplicates, times, calendar conflicts, missing connections and conflicting-publication checks. Unreviewed, ambiguous, expired or historical records must not enter routing silently. No invented stops, time values or geometry. Official source links on every schedule; map distinguishes completeness and source types.

On-demand refresh only: preserve versions, validate before activation, report additions/removals/conflicts/issues, permit rollback. Automated discovery can identify candidates but cannot automatically certify applicability or resolve ambiguous footnotes.

Acceptance: (1) valid GTFS import/query, (2) an agency without usable GTFS represented by a verified official PDF, (3) both coexist in SQLite, (4) map communicates completeness, (5) every schedule traceable, (6) uncertainty/expiry gated from routing, (7) GTFS and PDF fixture tests. Track any unmet acceptance explicitly.

## M0.G — GitHub initialization (COMPLETE; CLI authentication remains an environment issue)

Connect existing work to private `softnessasastrength/transfer-issues`; preserve local implementation and data. Depends on inventory, authenticated repository access and clean remote-history inspection. Acceptance: staged review, secret/generated-file exclusions, tests reported honestly, descriptive initial checkpoint published, local origin/main configured, commit SHA confirmed. No force-push or history rewrite.

Core priority order remains: GTFS ingestion/normalization → SQLite persistence → official PDF fallback → multi-agency exploration → maps/schedules → schedule verification/provenance (provenance is foundational throughout). Significant follow-on changes use feature branches and PRs; no automatic merging.

### Checkpoint status correction

Architecture entries above describe some **intended** behavior. As of repository initialization, browser localStorage/export/import and map interactions are not implemented: `web/app.js` is absent. API documentation now exists. The GTFS pipeline and initial SQLite/router/API modules exist; full routing acceptance tests, current-PDF normalization, source conflict/expiry gates and versioned refresh are incomplete. Raw and normalized data currently share the ignored `data/` directory; logical storage separation is not yet a full versioned provenance architecture. M0 and M0.1 remain IN PROGRESS.

Publication verified on private origin/main. Initial full-source checkpoint: `35543dd5cd98ed33015b4a90db45baef8294dea0` (preceded by README bootstrap commit `35dd98683d1e037f589b67c554cdb0763262103c`). Remote and local tree hashes match. 21 files published; downloaded/generated data excluded and retained locally. 14 tests and compilation/SQLite/API checks passed; no browser-completion claim. No history was rewritten. Ordinary CLI Git still needs authentication. GitHub reports main unprotected; rulesets query is unavailable on the current private-repository plan (HTTP 403). Do not change billing or visibility to resolve this. Enforce the feature-branch/PR policy operationally.

## M0.D — Desktop browser proof of concept (CURRENT DELIVERY PRIORITY)

User clarification on 2026-11-12: first deliver something runnable on the Mac mini and usable in a desktop browser to prove the idea. This explicitly prioritizes connecting the existing UI/backend before deeper ingestion work. Preserve the existing architecture and data; no mobile polish, Apache deployment, PWA, or iOS implementation. A local Python loopback server is sufficient for this proof of concept. The broader M0/M0.1 acceptance criteria remain required and incomplete.

Acceptance: browse real loaded routes on a geographic map; open date-specific timetables; select stops and run outbound/return/latest/reachability queries; save browser-local searches and journal entries with backup export/import; show source dates, coverage gaps and experimental routing limits; provide reproducible local launch instructions and browser tests. Mac hardware validation is not available in this environment and must not be claimed.

## M0.R — Regional/intercity rail and New Hampshire (QUEUED; after current core work)

Core states remain CT, MA and RI. Extended scope adds New Hampshire passenger rail and practical connections for destinations without rail. Preserve GTFS-first / official structured data / reviewed official PDF priority. Do not implement this expansion ahead of M0.D and ingestion reliability.

Relevant services to investigate and verify: Northeast Regional, Acela, Hartford Line / Amtrak Valley Flyer, Vermonter, Lake Shore Limited, Downeaster, and other Amtrak connections within or into the region. Prioritize Downeaster stations in NH, Boston/northern Massachusetts rail connections, relevant intercity buses, then necessary local last-mile transit. Target Exeter, Durham, Dover, Manchester NH, Nashua, Concord and relevant connecting destinations. Clearly distinguish Manchester CT and Manchester NH and direct-rail cities from bus-connected cities using verified sources. Do not infer station service or interchange opportunities from proximity alone.

Dependencies: validated GTFS/calendar normalization; source provenance/activation; reviewed PDF fallback; reliable transfer and return calculations. Additional states/agencies must be configuration additions rather than schema rewrites. Permit verified connecting service outside core boundaries where a complete journey needs it.

Required architectural accommodations (planned, not yet implemented):
- Replace the importer’s hard-coded geographic rectangle and MBTA rail-only filter with a documented configurable coverage policy. Preserve complete selected trip sequences and necessary out-of-area interchanges; do not draw synthetic rail links over clipped stops.
- Retain feed-namespaced IDs and mode-neutral trips, times, calendar and transfer tables. Add optional structured operator/ticketing metadata: reservation requirement (including unknown), booking/source URL, boarding restrictions, verified source and applicability. Keep seat availability and fares unknown unless authoritative data explicitly supplies them.
- Add city/state labels to place discovery; distinguish similarly named destinations. Direct-rail vs bus-required classification needs source evidence.
- Extend routing results with intercity/ticketing notices, station-specific boarding and transfer constraints, transfer risks and overnight gaps. Timetable feasibility never implies an available reservation, through ticket, guaranteed connection or scooter permission.
- Preserve every schedule’s source and verification status; no iOS-specific or cloud dependencies.

Acceptance: representative verified interstate/local-bus/commuter-rail/Amtrak/intercity-bus journeys and last returns; fixture tests for restrictions, calendar exceptions, overnight gaps and missing availability; source-linked station/service patterns; clearly labeled direct rail vs required bus connections; no invented fares, seat availability, stops or geometry. Expansion remains unimplemented at this checkpoint.


### M0.D status — implemented, acceptance blocked

Desktop controller and loopback launcher are implemented. 17 Python regressions/HTTP tests pass; JS syntax and compilation pass. Real-data Hartford–Springfield outbound/return queries pass. Browser acceptance is blocked by Chromium's denied Unix-domain socket in this executor; the repeatable browser smoke test is supplied but unverified. No macOS execution claim. Do not mark this milestone complete until browser interactions are exercised successfully. No source feeds or existing database were modified during this work.

## M0.T — Same-phone Termux launch (AUTHORIZED; device validation pending)

User requested Android/Termux execution of the current proof of concept. Scope: reuse Python/SQLite in Termux with Chrome on the same phone through loopback; document package setup, private repository authentication, first import, subsequent launches, stopping and browser-local data. `TERMUX.md` supplies the runbook. This does not authorize the deferred PWA/native-app/Apache milestones or mobile design overhaul. No backend restructuring is necessary for this launch path.

Acceptance pending: successful first import on Android, HTTP page and map interaction on that phone, timetable and return-trip query, journal persistence across restart. No Android device is attached here, so instructions are not a claim of successful phone execution. Preserve the current M0.D/core work and queued M0.R expansion.

## Authorized iOS offline proof of concept: Connecticut + PVTA (IN PROGRESS)

User selected regional offline architecture B, with the first proof of concept scoped to Connecticut transit and PVTA. Preserve M0 source-validation priorities and existing Termux/web functionality. Initial deliverable: non-destructive SQLite subset exporter with manifest, provenance, and missing-feed reporting. Next: verified PVTA acquisition, complete Connecticut operator inventory, native SQLite/routing and offline vector maps/paths, native GPS, airplane-mode acceptance. **Do not describe the iOS app as fully offline until all tests pass.** See `ios/OFFLINE_POC.md`.


## Authorized Android offline client proof of concept (IN PROGRESS)

Build a Kotlin Android Studio project that starts without a network connection, reads the shared CT/PVTA SQLite pack, and supports an exploration-first roadmap. Initial shell reads route inventory from local SQLite and needs Android Studio/device acceptance testing. Subsequent milestones: secure pack import and hash verification, native timetable/routing, offline vector map and paths, native GPS, optional live feeds, airplane-mode route-planning tests. Preserve web/Termux and iOS work; no claim of completed offline journey planning.

## M0.P — User-controlled offline package manager POC (IMPLEMENTATION IN PROGRESS)

Authorized on 2026-11-12: a Python standard-library backend proof of concept for the Choose Your Transit Network flow. `offline_packages.py` and synthetic tests cover explicit consent, agency/dependency planning, local payload checksums, staged content-addressed installation and update eligibility. Initial owner-selected agencies are CTtransit, CTrail Hartford Line, PVTA and Amtrak; actual data availability must be verified separately. Auto-update policy never authorizes new agencies. See `docs/architecture/offline-pack-manager-poc.md`. No native Android UI, downloader, catalog authentication, verified offline maps/graphs, or device tests yet. Preserve M0 core atlas priorities; this is a parallel scoped proof of concept, not a claim of finished offline support.

## M0.L — Mac mini ↔ Android LAN backend and offline preview (DRAFT POC)

Explicitly authorized: one-command local Python server, per-agency local GTFS SQLite exports and HTTP catalog/download, native Android agency picker with approval and SHA-256 verification, LAN WebView for the existing server planner, and native offline GTFS route-shape preview. See `docs/architecture/lan-android-poc.md`. No live source availability or device testing is claimed. Full native offline routing, licensed street basemap, and pedestrian graph remain missing; this work must not displace M0 core validation.

## M0.U — Unified offline transit network (STEP 1, DRAFT)

Architecture B selected: Python Mac mini backend and native Kotlin Android routing in later steps. Implemented `scripts/assemble_offline_network.py` to combine explicitly selected agency SQLite packs into one validated, atomically replaced offline routing dataset, plus six synthetic tests. See `docs/architecture/unified-offline-network.md`. No fabricated interagency transfers, native Android journey planner, or real-device validation. Step 2 requires explicit transfer policy and then connection-scan routing against the combined network.

## M0.T — Step 2 interagency transfer routing (DRAFT)

Owner selected official GTFS transfers plus explicitly estimated proximity transfers, respecting forbidden links and the existing boarding buffer. Added `transfer_edges.py`, integrated priority-queue walking relaxation into the Python connection scan, and synthetic tests. See `docs/architecture/interagency-transfer-routing.md`. No pedestrian street verification, real-feed validation, or native Android Kotlin journey planner yet. Step 3 requires a street-network data source/format decision.

## M0.S — Step 3 offline street graph (DRAFT)

Owner selected OpenStreetMap + SQLite routing graph (architecture B). Added local OSM XML to SQLite graph builder, Python walk/cycle Dijkstra pathfinder, optional Mac mini transit-transfer graph integration, and six synthetic tests. See `docs/architecture/offline-street-routing.md`. No automatic data downloads, full OSM/PBF import, street basemap, Kotlin Android pathfinder, or device validation. Real graph paths remain estimates and do not establish safe/legal/accessibility-compliant passage.

## M0.A — Step 4 Android offline routing (DRAFT)

Owner selected A: Kotlin native offline journey computation. Added a Kotlin SQLite GTFS timetable reader, service calendar and exception logic, interagency walking transfer estimates, connection scan, standalone Android planner screen, and seven synthetic JUnit tests. See `docs/architecture/android-native-offline-routing.md`. Not yet compiled/tested on device; no Kotlin OSM street graph routing or unified pack installer. Must validate correctness, scale, and airplane-mode operation before completion.

## M0.AS — Native Android street routing (DRAFT)

Owner selected B from the next-stage choices: Kotlin native street graph integration. Added `OfflineStreetGraph.kt` for Step 3's SQLite format, directed walk/cycle shortest paths, graph-derived interagency transfer times, and seven synthetic Kotlin JUnit tests. Planner optionally loads app-private `streets.sqlite`; without it, proximity estimates remain. See `docs/architecture/android-native-street-routing.md`. No build/device tests executed, in-app street pack installation, or regional performance validation yet.

## M0.V — Step 6 visual Android journey planner (DRAFT)

User selected D: searchable stop names/IDs, touch-selectable offline geographic stop map, and named leg-by-leg itinerary presentation. Added `JourneyUiModel.kt`, `StopPickerMap.kt`, updated `OfflinePlannerActivity.kt`, and nine synthetic JUnit tests. See `docs/architecture/android-visual-journey-planner.md`. No offline street basemap, zoom/pan, Gradle compilation, device testing or routing correctness verification yet.

## M0.Q — Step 7 routing verification (DRAFT)

Owner selected A. Fixed LAN Python pack builder syntax, debug Android manifest override, and Kotlin GTFS pickup/dropoff restrictions; added six synthetic Kotlin regression tests and GitHub Actions Python + Android debug build/JUnit verification. See `docs/architecture/routing-verification-step7.md`. CI configured but not observed running; no Gradle compilation, device test, real-feed validation or Python/Kotlin parity claim yet. Preserve previous features and stacked draft PRs.

## M0.P — Step 8 Python/Kotlin routing parity (DRAFT)

User selected B. Inspected failed Step 7 CI: seven Python test fixture errors due to unmocked transfer_graph; Android SDK action attempted obsolete tools package before compilation. Fixed both CI blockers and added 13 language-neutral synthetic golden routing scenarios consumed by Python and Kotlin tests, comparing arrivals and leg sequences. See `docs/architecture/python-kotlin-routing-parity.md`. CI results still required before claiming parity/build success.

## M0.R — Step 9 Android build and parity CI verification (DRAFT)

User selected A. Step 8 CI successfully built the Android debug APK and passed Python tests, but Kotlin unit-test compilation failed on ten-element list destructuring. Replaced with explicit indices in shared golden fixture reader. Step 9 acceptance requires both Python and Android Gradle JUnit jobs green; device, real-feed and airplane-mode tests remain outstanding. See `docs/architecture/android-parity-ci-verification-step9.md`.

## M0.S — Private experimental APK Releases (DRAFT)

Owner authorized automatic experimental GitHub Releases for successfully tested Android APKs. Workflow publishes a prerelease only after Python routing and Android debug build/JUnit jobs both succeed, with SHA-specific APK and checksums; feature branch pushes and manual dispatch only. See `docs/architecture/experimental-android-releases.md`. CI/release verification pending; stable APK signing and updateable version codes are deferred follow-ups, and device launch/offline tests remain unverified.
