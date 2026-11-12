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
