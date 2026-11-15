# Southern New England Transit Atlas — authoritative implementation plan

Read this file and relevant project instructions at the start of every work session. Record new requests here, identify dependencies, preserve priority, and verify acceptance criteria before marking complete. Explain conflicts rather than silently changing priorities. No recurring monitoring or scheduled tasks are authorized.

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

Status update (2026-11-15, CTtransit verification): the official CTtransit developer page exposes statewide JSON realtime trip updates, vehicle positions and alerts. Added a dependency-free JSON adapter and fixtures for route/stop filtering. PVTA remains schedule-only: its official realtime page confirms beta GPS/departure data and a usage agreement but does not expose a stable feed URL/schema in the accessible developer material.

## M0.L — Optional rideshare last-mile links (QUEUED; planning only)

A future last-mile layer may offer Uber/Lyft deep links from a selected stop or itinerary endpoint. The first version must be link-only and user-initiated: no booking, payment, account-token storage, or autonomous ride requests. It may show a provider's own app handoff, but must not invent price, ETA, availability, accessibility, or coverage.

Uber's official rider documentation says deep links pass parameters to the app but do not fetch time or price estimates; price estimates require API access and current policy approval. Lyft's current developer access is not sufficiently verified in this environment for an implementation claim. If pursued, use a provider-neutral `last_mile_options` contract with explicit `available`, `unknown`, and `deep_link_only` states, coordinate privacy controls, and tests that prove no booking path exists.

Dependencies: stable stop coordinates, user confirmation UX, credential/terms review, and a clear distinction between transit schedule feasibility and rideshare availability. This does not authorize production credentials or paid API usage.

## M0.T — Same-phone Termux launch (AUTHORIZED; device validation pending)

User requested Android/Termux execution of the current proof of concept. Scope: reuse Python/SQLite in Termux with Chrome on the same phone through loopback; document package setup, private repository authentication, first import, subsequent launches, stopping and browser-local data. `TERMUX.md` supplies the runbook. This does not authorize the deferred PWA/native-app/Apache milestones or mobile design overhaul. No backend restructuring is necessary for this launch path.

Acceptance pending: successful first import on Android, HTTP page and map interaction on that phone, timetable and return-trip query, journal persistence across restart. No Android device is attached here, so instructions are not a claim of successful phone execution. Preserve the current M0.D/core work and queued M0.R expansion.
