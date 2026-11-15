# Southern New England Transit Atlas — authoritative implementation plan

Read this file and relevant project instructions at the start of every work session. Record new requests here, identify dependencies, preserve priority, and verify acceptance criteria before marking complete. Explain conflicts rather than silently changing priorities. No recurring monitoring or scheduled tasks are authorized.

## Running feature backlog

This is the active list of requested product work. Status means engineering
priority, not a promise that the feature is complete.

### Next — mobile and reliability

- **Android app shell** — IN PROGRESS. Build and install the WebView shell,
  validate Termux loopback and Chromebook LAN flows, add a visible connection
  error/retry state, and document debug/release APK builds. Connection
  profiles for phone-local, Chromebook/Mac LAN and custom hosts are now added;
  device validation remains pending.
- **Android native polish** — QUEUED. Deep links, Android back/share behavior,
  accessible touch targets, dark theme parity, connection profiles and a
  deliberate offline/cache policy.
- **Safe device discovery / remote access** — PLANNING. Prefer same-LAN
  discovery (mDNS/NSD or a QR connection handoff) and an authenticated private
  overlay such as Tailscale for access away from home. Do not implement router
  UPnP port mapping while Atlas/MCP are unauthenticated HTTP services.
- **Percival red-team fixes** — QUEUED. Validate MCP argument types, cap HTTP
  request/response sizes, protect LAN mode, require confirmation for destructive
  preference operations, and delimit untrusted feed text before model context.
- **API client foundation** — IN PROGRESS. Compact/paginated metadata and
  endpoint-level option validation are landed; add explicit provenance/expiry
  fields, broader contract fixtures and authenticated persistence before native
  clients depend on the API.
- **GTFS trip-order migration** — IN PROGRESS. The importer now records each
  stop's position in the full published trip so schedule scans handle sequence
  gaps without joining across clipped stops. Rebuild from existing downloaded
  archives, validate integrity, and exercise representative real-feed queries
  before activating the new database; see `ARCHITECTURE_CORRECTNESS.md`.
- **Connecticut and Massachusetts coverage** — IN PROGRESS. Add current
  source-backed Greyhound and Metro-North schedules, enable LIRR for trips to
  friends near its stations, and expose major Connecticut city map shortcuts.
  Hartford DASH and Shore Line East appear in existing feeds. Peter Pan's
  public GTFS is historical (2024); GHTD Link and ADA paratransit require
  booking, and a CTtransit service named Flex remains unverified. Continue
  local-agency inventory, provenance and transfer-rule work before claiming
  complete CT/MA coverage. See `REGIONAL_COVERAGE.md`.

### Later — product capability

- **Installable mobile web/PWA** — DEFERRED. Add manifest, service worker only
  after offline map/data licensing and expiry behavior are designed.
- **SwiftUI iOS client** — INVESTIGATION AUTHORIZED. Build on a Mac after the
  API/security prerequisites; do not port Python routing into the phone app.
- **Departure board refinement** — QUEUED. Countdown normalization, route
  colors, freshness, alerts, stop boards and explicit unknown/stale states.
- **Route-chain exploration** — PARTIAL. Support unusual chains such as
  `905 → 30 → 24X`, show transfer legs and explain when no published timed
  connection exists.
- **Fare coverage** — PARTIAL. Expand source-backed CTtransit, CTrail, MBTA,
  PVTA and mixed-agency estimates without guessing unsupported fares.
- **Network expansion** — QUEUED. Add verified regional feeds and optional
  networks through configuration, with source provenance and coverage labels.
- **User data portability** — QUEUED. Move beyond browser-local records with
  authenticated, exportable preferences/bookmarks while preserving local-first
  operation.
- **Last-mile links** — PLANNING ONLY. User-initiated Uber/Lyft deep links;
  never invent price, ETA, availability or booking capability.

- **Percival Outings** — IN PROGRESS. Map-first scheduled round-trip planning
  now verifies an outbound, minimum meeting time, latest return, final walk and
  hard home-by deadline. Bounded candidate searches expose unevaluated overflow
  as unknown. Real-data and browser acceptance remain part of the current M0.D
  delivery work; no offline pack or background task is implied.
- **Saved commute profiles (F-009)** — FIRST SLICE BUILT (PR open, unmerged).
  A commute is a standing profile in the device-local Percival preferences:
  home/work as Atlas stop IDs, a preferred route chain per direction
  (asymmetry is the normal case), and declared rideshare legs where transit
  ends before the endpoint. `atlas_commute_evaluate` plans both directions
  for a real date through the existing planner, notes where a declared chain
  cannot run, labels rideshare legs as estimated drives (never a quote,
  never booked), and always reports the last viable return. Follow-ons:
  a web/UI surface for profiles, and address-to-stop resolution beyond the
  existing stop search (no external geocoder by default).

### Explicitly not promised

- Live-arrival guarantees, ticketing, reservations, payments, autonomous
  messages/bookings, guaranteed connections, accessibility/slope guarantees,
  or recurring background tasks.

## M0 — Core atlas (IN PROGRESS; current priority)

Deliver a maintainable working application derived from `prototype.html`, official GTFS import and validation, geographic routes/stops, date-specific calendars and exceptions, timetables, transfers, last-trip and return feasibility, multi-agency reachability, explicitly estimated walking/scooter connections, bookmarks, discovery journal, source dates, missing-feed documentation, tests and run instructions.

Priority geography: Hartford, Springfield, Enfield, Windsor Locks, Manchester, Holyoke, Chicopee, Westfield, New Haven, Worcester.

Acceptance: import available official archives and report failures honestly; exercise planner calendar, overnight, transfer and return behavior; test API and browser interactions; document limitations and reproducible setup; deliver source and data. Missing PVTA data is a substantive coverage gap, not proof that service does not exist. Do not mark full requested coverage complete until it is obtained. (Update 2026-11-14: PVTA GTFS has been obtained and imported — the block proved to be a User-Agent artifact in the downloader, not feed unavailability; see DECISIONS.md. Other agency gaps, e.g. RIPTA, remain open.)

## M1 — macOS / Apache self-hosting (DEFERRED; explicit authorization required)

Depends on stable and validated M0. Target Mac mini M4 16 GB and MacBook Air M4, Apple Silicon, Apache HTTP Server 2.4+. Apache is the web-facing reverse proxy; SQLite remains primary unless measured technical limitations justify reconsideration. Provide macOS installation/configuration, LAN/iPhone access, persistent GTFS/data/bookmarks/preferences, start/stop/restart/backup/update scripts, optional launchd startup, example virtual hosts, HTTPS/authentication/safe remote-access guidance. Must work without cloud infrastructure or paid hosting. Preserve existing data throughout migration.

Acceptance: test installation, restart persistence, backup/restore, LAN access, proxy headers and secure access on macOS before completion. No Apache configuration or deployment implementation authorized yet.

## M2 — Mobile web / PWA (DEFERRED; explicit authorization required)

Depends on successful M1 local deployment. Baseline responsive core UI is in M0; this phase adds iPhone/desktop optimization, touch map improvements, installable PWA where supported, offline selected maps and downloaded transit data, persistent bookmarks/history, small-screen discovery and timetables. Respect map-provider offline caching terms. No service worker or PWA conversion yet.

Acceptance: iPhone Safari/browser tests, install/offline behavior, selected data expiry visibility and persistence tests. Device-browser storage export must remain recoverable.

## M3 — Native iPhone client investigation (AUTHORIZED; implementation gated)

Depends on stable versioned API and secure M1 deployment. Evaluate SwiftUI or justify alternatives. Reuse backend routing and GTFS engine. Maps/routes/stops/schedules, opt-in location, saved trips/favorites, feasible offline data, secure Mac mini connection and minimal third-party cloud dependence. Do not add iOS dependencies to the backend.

Acceptance for investigation: architecture proposal, API gap analysis, offline/security plan and justified implementation estimate. Implementation requires separate authorization.

Status update (2026-11-15, iOS build-path request): investigation is authorized. No Xcode project or iOS binary exists yet. The current practical first target is a SwiftUI client consuming `/api/v1/` over a Mac mini or other explicitly secured host; the Python/SQLite backend remains platform-neutral. This Linux/Chromebook environment cannot run Xcode, the iOS Simulator, code signing, or App Store/TestFlight packaging. Before native implementation, close the API gaps listed in `API.md` (pagination/compact payloads, complete validation, provenance/expiry semantics, and authenticated persistence) and define secure LAN/TLS access. A PWA remains the fastest installable phone experience while M3 is implemented.

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

MBTA full-mode coverage was authorized and implemented as a core regional-feed improvement on 2026-11-15: the importer now uses a checked-in coverage policy and loads selected MBTA bus, subway/light-rail and commuter-rail routes. M0.R remains queued; this does not implement its intercity ticketing, New Hampshire, station-constraint or reservation requirements.

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

Status update (2026-11-14, Ember session; see DECISIONS.md): 29 Python tests pass, including 12 Mobility Bubble fixture tests for the new `/api/v1/bubble` endpoint. The browser smoke test PASSED in the Ember environment (Playwright + Chromium; the earlier socket blocker does not occur there), and a fresh five-feed import was completed with PVTA still unavailable (HTTP 403). macOS/Safari acceptance remains unperformed, so M0.D is still not marked complete.

Status update (2026-11-14, Ember PVTA fix session; see DECISIONS.md): the PVTA 403 was a User-Agent artifact — pvta.com rejects the default urllib UA. The downloader now sends an explicit descriptive User-Agent and PVTA imports fully: 62 routes / 13,381 trips / 1,973 stops, service 20261102–20261219. Springfield local journeys and Hartford -> Springfield journeys continuing onto PVTA legs verify against the API, and the Mobility Bubble's unknown classification for the Springfield area is resolved (PVTA stops now classify on evidence). 30 Python tests pass, including a stubbed regression test for the download header. macOS/Safari acceptance remains unperformed, so M0.D is still not marked complete.

Status update (2026-11-15, local MCP connector): `scripts/atlas_mcp.py` exposes the versioned Atlas API over dependency-free MCP stdio for MCP-capable local agents, including Ollama hosts. It is intentionally local-only and requires the Atlas HTTP server to be running; no live-arrival or remote-service guarantee is added. Protocol and argument-mapping tests are included.

Status update (2026-11-15, Percival continuation): evidence-first route reports and protected draft-only visit planning are implemented in the MCP layer. The Open WebUI path has a loopback Streamable HTTP adapter with initialize/tool-discovery/notification tests and a manual validation checklist; actual Open WebUI execution remains unverified in this environment.

Status update (2026-11-15, Percival local memory): explicit device-local preference tools are implemented for home/origin/host stops, time windows, ground mode and radius. Preferences are never inferred, synced or treated as transit evidence.

Status update (2026-11-15, separated live overlay): added an opt-in provider-neutral `/api/v1/live` contract and an official MBTA V3 JSON adapter for predictions/alerts. Live failures produce `unknown`; scheduled routing does not call the adapter. CTtransit/PVTA live support remains unimplemented pending verified official realtime contracts.

Status update (2026-11-15, live board slice): added a browser Live board view backed by `/api/v1/live`, with provider/route/stop filters and explicit live/unknown messaging. This is a read-only status surface; a compact departure-board presentation with countdowns, route colors and freshness is the next UI refinement. CTtransit/PVTA remain unverified.

Status update (2026-11-15, API contract slice): added opt-in compact metadata
and pagination for large route/stop, reachability and Mobility Bubble arrays,
with total/has-next metadata and no default response-shape change. Added strict
validation for boolean flags, plan kind, and namespaced route chains. Remaining
API prerequisites are unified PDF confidence/validation statuses, per-trip
provenance/expiry gates and authenticated persistence; this does not authorize
remote exposure or native-client implementation.

Status update (2026-11-15, CTtransit verification): the official CTtransit developer page exposes statewide JSON realtime trip updates, vehicle positions and alerts. Added a dependency-free JSON adapter and fixtures for route/stop filtering. PVTA remains schedule-only: its official realtime page confirms beta GPS/departure data and a usage agreement but does not expose a stable feed URL/schema in the accessible developer material.

Status update (2026-11-15, Percival UI/UX pass): began the ordered visual pass with a departure-board treatment for live rows, explicit empty states for route/stop search, mono typography stacks (IBM Plex Mono primary, Ubuntu Mono technical), and responsive live controls. Backend semantics are unchanged; browser-device visual acceptance remains pending.

Status update (2026-11-15, route chaining): added optional ordered route constraints to scheduled planning and the UI chain builder. Users can express sequences such as 905 → 30 or 905 → 24X; the planner still requires actual loaded stops, calendars, transfer buffers and published timetable feasibility. Automatic planning remains unchanged when no chain is selected.

Status update (2026-11-15, Amtrak expansion): enabled `whole_network` coverage policy for the official Amtrak GTFS archive and rebuilt locally with 64 routes, 645 stops and 2,461 trips, with no importer errors. Added a generic feed-page fallback so future configured networks do not require a Python hard-coded page-map edit. This is full coverage of the current downloaded Amtrak archive, not a live-service, ticketing, reservation or guaranteed-connection claim.

## M0.L — Optional rideshare last-mile links (QUEUED; planning only)

A future last-mile layer may offer Uber/Lyft deep links from a selected stop or itinerary endpoint. The first version must be link-only and user-initiated: no booking, payment, account-token storage, or autonomous ride requests. It may show a provider's own app handoff, but must not invent price, ETA, availability, accessibility, or coverage.

Uber's official rider documentation says deep links pass parameters to the app but do not fetch time or price estimates; price estimates require API access and current policy approval. Lyft's current developer access is not sufficiently verified in this environment for an implementation claim. If pursued, use a provider-neutral `last_mile_options` contract with explicit `available`, `unknown`, and `deep_link_only` states, coordinate privacy controls, and tests that prove no booking path exists.

Dependencies: stable stop coordinates, user confirmation UX, credential/terms review, and a clear distinction between transit schedule feasibility and rideshare availability. This does not authorize production credentials or paid API usage.

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

## M0.T — Phone-only Termux bridge (AUTHORIZED; staged drafts)

Stage 1: explicit loopback-only Termux Python pack server using existing validated GTFS exporter and Android debug pack installer. Stage 2: source-aware official GTFS import and deterministic catalog integration tests. Stage 3: optional Termux development and wireless ADB debugging. All stages use separate draft PRs; no merges. Device acceptance requires verified stop installation and airplane-mode planner operation. See `docs/architecture/termux-phone-only-stages.md`.

## Crostini Developer Command Center (AUTHORIZED; first increment)

Owner mandate 2026-11-13: inspect repository/toolchain, verify existing Chromebook
build, then implement a modular developer dashboard and safe command adapters.
First increment: curses + headless JSON, Git/tool/disk telemetry, fixed Python and
Android validation commands, local logs/history and APK SHA-256. Acceptance:
adapter tests, full Python suite, Android task evidence, APK metadata inspection,
and terminal launch/quit smoke. See `docs/development/developer-command-center.md`
and `docs/development/baseline-20261113.md` for evidence and limitations.

Future authorised stages remain queued: pack provenance/integrity UI; explicitly
confirmed clean builds and APK installation; ADB diagnostics; on-demand PR/CI
inspection; optional artifact transfer. Preserve existing core/ingestion priorities
and consent rules. No geographic expansion or architectural replacement included.

### Command Center result evidence and feature blitz — 2026-11-13

Owner requested the next task, then a Command Center feature blitz. First focused
slice: read-only Python/unittest summaries, Android JUnit XML counters and adjacent
APK metadata, with explicit historical provenance and source timestamps. Acceptance:
malformed/missing/failed/empty evidence cannot appear as current-tree success;
synthetic regressions, full Python suite, headless and terminal reports-view smoke.
Depends on draft #44; use a separate stacked draft, no merge.

Next focused slice: read-only Git branch/history view, saved-log browsing, keyboard
help and richer environment information. Downloads, pack mutations, device installs,
clean builds and transit-engine changes retain their existing approval/consent gates.

### Inspection-panel acceptance — first blitz slice

Read-only Git and environment panels, help, safe saved-log tail browsing and JSON
inspection modes are implemented on `feature/crostini-inspection-panels`, stacked
on result-summary draft #45 (which depends on #44). Acceptance: deterministic
traversal/symlink/FIFO/terminal-control/size-bound and environment-presence tests;
full Python regressions; headless inspection and manual terminal navigation.
No build/source/device mutation is available from inspection pages. No geographic
or transit-runtime expansion is part of this slice.

### CI coverage and engineering audit — feature blitz continuation

Add verification triggers for Python modules, launchers, scripts and the Command
Center; compile Python, validate Bash syntax and retain failure diagnostics without
weakening exit status. Acceptance: path/security/failure-propagation contracts,
full Python suite and exact-head hosted CI; successful-build-only APK upload remains.
No release automation or permission expansion. See
`docs/development/engineering-audit-20261113.md` for observed offline-pack gaps and
prioritised installer recovery, pack-contract parity, accessibility and offline
acceptance follow-ups. These preserve existing M0/core and consent priorities.

## Agency-pack relational validation (AUTHORIZED; synthetic acceptance verified)

Continuation of the standing engineering directive: strengthen the existing local
Termux/Crostini catalogue gate with normalized schema/key/reference/calendar/time
checks and expose the same read-only result in Command Center P/--inspect packs.
Acceptance: reject malformed/NULL/dangling/duplicate/checksum-correct invalid packs;
preserve exception-only overnight service and sequence gaps without changing bytes;
verify actual exporter compatibility, CLI failure diagnostics and 100-test regression
suite. See `docs/development/agency-pack-validation.md` for exact rules/evidence.
Real-feed/device/scale acceptance remains pending. No new downloads, agency installs,
pack repair, geometry synthesis, storage cap or activation architecture change.

Next: compatible Android validation and interrupted-activation recovery; retain
current source integrity and consent priorities. Unified assembler/Android parity
must not be inferred from this Python export-gate implementation.

## Android per-agency activation recovery (AUTHORIZED; local JVM/build acceptance)

Next reliability slice after #48: replace the active-name gap with a synced backup
copy and atomic replacement, serialize existing download staging across Activity
instances, and recover a legacy previous pack when active is absent. Recovery checks
a copy using SQLite integrity, preserves previous bytes and never promotes partial
downloads or fetches data. Existing consent and per-agency filenames are unchanged.

Acceptance observed locally: 14 new failure/recovery/concurrency JVM tests; 44 total
Android tests without failures/errors/skips; successful debug assembly; 100 Python
regressions. See `docs/architecture/android-pack-activation-recovery.md`. Exact-head
CI and physical Android/process-death/power-loss tests remain separate gates. No
multi-agency transaction, trusted manifest or complete-offline guarantee is claimed.
