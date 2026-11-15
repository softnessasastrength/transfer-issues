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

## Ember (_muse) session — 2026-11-14, PVTA User-Agent fix

- Working branch: `pvta-user-agent-fix_muse`, based on `feature/browser-proof-of-concept`. Trigger: the owner reported firsthand that in his own running instance the PVTA feed ingested fine — he can browse downtown Springfield and see routes G1–G5 and their full extent. His report was right; the "PVTA feed unavailable" conclusion recorded earlier (2026-11-12 entry above and the 2026-11-14 session entry) was wrong, and this entry corrects it.
- Diagnosis, verified directly: pvta.com rejects non-browser/default user agents. From this environment on 2026-11-14: `curl` with its default UA -> HTTP 403; Python urllib with its default UA -> HTTP 403; Safari UA -> HTTP 200; a descriptive project UA -> HTTP 200. `import_gtfs.py:refresh()` called `urllib.request.urlopen(url)` with no headers, so every PVTA download attempt inherited the default `Python-urllib` UA and got 403. The gap was a missing header, not missing data. The earlier research note (endpoints 403, nested link 404) was accurate observation of UA-filtered responses, misread as feed unavailability.
- Fix: `refresh()` now sends an explicit, honest `User-Agent: TransitAtlas/0.1 (+https://github.com/softnessasastrength/transfer-issues)` on ALL feed downloads (single shared code path; the server accepts the descriptive UA, so no browser-UA impersonation is used). The reason is recorded in a code comment at the constant. Companion fix in the same function: a successful download now also clears a stale `refresh_error` (previously only `error` was popped, so a recovered feed kept reporting its old failure in `sources.json` and bubble unknown-reasons). Also corrected the stale "PVTA unavailable" string in the `/api/v1/meta` limitations list.
- Regression test: `tests/test_core.py` `DownloadTests.test_refresh_sends_user_agent` stubs `urllib.request.urlopen` locally (no live network), asserts the request carries `import_gtfs.USER_AGENT`, and asserts a stale `refresh_error` is cleared on success. Suite: 30 tests, all passing.
- PVTA ingestion, verified: fresh `scripts/prepare_data.py` imported all six feeds with no refresh errors. PVTA: 62 routes / 13,381 trips / 1,973 stops, zero import errors; service period 2026-11-02 to 2026-12-19; feed Last-Modified Mon, 02 Nov 2026 19:12:54 GMT; 5,456,432 bytes. Springfield routes present in the database include G1 (both Union Station variants), G2, G3, G5, G19, G47 and G73E, plus the B/P/R/T-series network.
- API smoke on real data (Tuesday 2026-11-17, inside PVTA's service period): departures from Court Square, Springfield (`pvta:1495`) = 167 for the day; Springfield local plan Union Station Bay 1 (`pvta:5101`) -> Court Square found, single G2 leg 08:00 -> 08:02:56; Hartford (`hartford:6`) -> Court Square found with a rail leg to Springfield, an estimated walk transfer, and a PVTA P11 local leg (dep 08:35, arr 09:28:46).
- Mobility Bubble reclassification (Hartford station, 2026-11-17 08:00, 60-minute budget, visit=0): before the fix, reachable 1,034 / unreachable 10,068 / unknown feeds [pvta] — the entire PVTA network was unevaluable. After the fix, reachable 1,034 / unreachable 12,041 / unknown feeds [] — exactly +1,973 stops (the PVTA stop count) moved from unknown into evidence-based unreachable (`no_outbound_within_budget` 7,718 -> 9,691; `no_feasible_return` unchanged at 2,350; zero PVTA stops are within a 60-minute out-and-back bubble from Hartford, which matches the ~40-minute each-way rail time). From Springfield Union Station the same bubble now finds 582 reachable stops, 580 of them PVTA.
- Consequence for the roadmap: PVTA GTFS coverage is obtained; the M0.1 PDF-fallback build is no longer the route to Springfield/Holyoke/Chicopee/Westfield bus evaluation. It remains worthwhile as resilience (a UA filter or endpoint change could recur) and for agencies that genuinely publish no GTFS, but it is not a Springfield blocker. CODEX_HANDOFF.md items 1 and 6 revised accordingly.

## Ember (_muse) session — 2026-11-14, Codex front-load: stop lookup + latency profile

- Owner instruction (2026-11-14 evening): Ember front-loads the bounded coding so the Codex window is spent on judgment work. This session delivers cook list task 1 (stop lookup endpoint) outright and the measured latency profile that cook list task 2 (plan/bubble latency) starts from. Working branch: `frontload-stops-and-latency_muse`, based on `feature/browser-proof-of-concept`.
- Implemented `GET /api/v1/stops?q=<text>` (cook list task 1; Percival's F-001 friend registry is the first consumer — it previously had to hard-code raw stop IDs such as `pvta:5101`). `database.search_stops` performs a case-insensitive substring match over the loaded stops table only, returning id, name, feed, lat/lon, a total `match_count`, the applied `limit` (default 50, range 1–500) and a `truncated` flag; prefix matches sort first. An empty query returns an honest empty result rather than the whole stop list; a no-match query returns zero results. LIKE wildcards in the query are escaped so they match literally (a query of `%` finds only names containing a literal percent sign). Optional `feed=<id>` restricts to one feed. Nothing is invented: only rows present in the stops table can match.
- Tests: `tests/test_stops.py` adds 10 tests against a synthetic fixture SQLite (substring match, case-insensitivity, result fields, feed filter, honest empty results for no-match and empty queries, limit/total-count/truncation, literal wildcard matching, endpoint contract and limit validation). Full suite: 40 tests, all passing (30 pre-existing + 10 new).
- Live verification on real data (Tuesday 2026-11-17 data loaded): `q=Union Station` resolves Springfield's `pvta:5101` (Union Station Bay 1) among the matches; `q=Court Square` resolves `pvta:1495`; a nonsense query returns zero results. See the session's PR for the captured responses.
- Latency profile for cook list task 2: measured phase timings for `/api/v1/plan` and `/api/v1/bubble` on the full six-feed dataset are recorded in CODEX_HANDOFF.md under "Latency profile (Ember, 2026-11-14)", with the profiler kept at `scripts/profile_latency.py` so Codex can re-run the same baseline after changes. Headline: a cold first plan request costs ~19.5 s end-to-end, of which the per-day connection-list build (~6.2 s) and the stop-network build (~5.0 s) are the largest single pieces; warm, a single plan costs ~2.1 s regardless of distance because every plan runs a full-day scan over all 832,735 connections, and a warm `return=1` plan costs ~7.8 s (outbound plan + return plan + `routing.latest`'s binary search of ~a dozen further scans). The bubble's warm cost (~3.3 s) sits mostly in its fixpoint reverse scan, whose repeated walk-propagation passes are its single most expensive function. Numbers and ranking are in the handoff, not here, to keep one authoritative copy.

## Ember (_muse) session — 2026-11-14, Vercel deployment form (owner-directed)

- Owner instruction (2026-11-14 evening): "make my Atlas also a Vercel app so that it's accessible from Vercel." Working branch: `vercel-deployable_muse`, based on `feature/browser-proof-of-concept`. The LIVE deploy remains the owner's tap; nothing was deployed in this session. This is the deployment form of the existing M0.D desktop web app — it is NOT M2: no service worker, offline support, installability or mobile work was done, and M2 remains deferred in ROADMAP.md.
- Measurements first (this sandbox, full six-feed data): `data/atlas.sqlite` is 266,338,304 bytes (254.0 MiB) — times 75.1 MiB + its two indexes 79.0 MiB, shapes 55.6 MiB + index 34.5 MiB, trips ~7.3 MiB, stops ~1.3 MiB. `web/` static footprint is 212 KB total. Derived in-memory structures: one service day's connection list plus the stop network peaks at ~520 MiB RSS; the observed worst case (two service days cached + a `return=1` composite) peaked at ~969 MiB.
- Vercel limits, from Vercel's own documentation (functions limitations page, read 2026-11-14): Python functions allow 500 MB uncompressed bundle size (Node is 250 MB); Hobby maximum duration is 300 s (default and maximum, Fluid compute); Hobby maximum memory is 2 GB. Against those: the full six-feed bundle by construction is ~268.2 MB (DB 266,338,304 + sources.json 15,054 + atlas code ~25 KB + vendored Python runtime ~1.9 MB) — ~54% of the Python limit, so NO feed scoping was needed and the hosted form carries complete current coverage. The coldest measured request class (~19.5 s cold plan in this throttled sandbox; ~25 s class for a cold return composite) sits 12–15× under the 300 s duration cap. Memory fits the 2 GB cap with ~2× headroom on observed workloads; the pressure point is the per-day connections cache (~450 MiB per additional service day in a long-lived warm instance), recorded here as a known characteristic, not solved in this session.
- Design: one serverless function, `api/index.py`, is a thin adapter over the existing `server.handle` — no routing logic is forked, so the hosted and local APIs cannot drift. The original `/api/v1/...` path reaches the adapter via a vercel.json rewrite that injects it as the `atlas_path` query parameter; the bare function URL answers with the meta document as a deployment health check. `web/` stays the static UI, reached through explicit rewrites (`/`, `/app.js`, `/style.css`, `/vendor/*`). The function's `maxDuration` is 300.
- Data path: the database is generated by the deploy build, never committed (`.gitignore` already excludes `/data/` and `*.sqlite`). `vercel.json` sets `buildCommand: python3 scripts/prepare_data.py`; `includeFiles` then bundles `data/atlas.sqlite` + `data/sources.json` (plus the four atlas modules) into the function. Verified from a pristine checkout in this session: the full pipeline (six feed downloads + import) completed in 136.7 s and produced a database of exactly 266,338,304 bytes with service periods identical to the workspace copy. `.vercelignore` keeps the local `data/` (regenerated at build), repository-internal Markdown and the ancestor `prototype.html` out of the deployment upload.
- Verification: full suite 51/51 (40 pre-existing + 11 new adapter tests in `tests/test_vercel_adapter.py`: path resolution, status mapping, 405 handling, fixture end-to-end). On real data, adapter responses were byte-identical to the local server's on 8 cases — stops lookup, coverage, plan Hartford→Springfield, plan with return, the bubble reference case (1,034 reachable, 758,777-byte body), and the 400/404 error paths. The bundle layout was also run standalone from a separate tree (adapter + root modules + `data/` only) with identical reference answers. Vercel's own `@vercel/python` builder (v32.0.0, invoked directly as in the Percival session) accepts the project: entrypoint `handler` detected, Python 3.12 selected, Lambda produced with the correct layout (generated `vc__handler__python.py` wrapper, vendored runtime, all required paths present).
- Sandbox staging defect (recorded so it is not misread as a project problem): in THIS sandbox, the builder's file-staging streams deterministically truncate large bundled files at exactly 65,536 bytes — reproduced with a minimal project whose only large file was a 307,200-byte includeFile containing no Atlas code — and in Atlas runs the same defect zeroed `server.py`/`routing.py` as collateral. Pristine sources were hash-verified intact before every run; the corruption is in this environment's copy streams, not in the project files or the Vercel configuration. Consequence: a byte-intact local bundle extraction could not be produced here, so the decisive byte-level check is the first real deploy's build log plus the three reference queries (stops `Court Square` → `pvta:1495`; plan Hartford→Springfield found; bubble from `hartford:6` = 1,034 reachable). The `vercel build` CLI itself also stops at its project-link/auth gate in this sandbox (same limitation as the Percival session). One earlier pristine-build failure in this session was sandbox disk exhaustion (`/tmp` is a 512 MB tmpfs; Errno 28) — an environment artifact, not a feed or importer problem; the retry on the overlay filesystem succeeded as recorded above.
- Remaining owner step (single action): in the Vercel dashboard, create/link a project for this repo (root = repo root, branch `feature/browser-proof-of-concept` until the owner promotes it) and deploy — or `vercel link` + `vercel deploy --prod` from a checkout. Then run the three reference queries above against the deployment URL. Hobby build rate limits observed elsewhere tonight may delay the build; that is a quota wait, not a failure.

## Codex Luna session — 2026-11-14, latency chunks L2.1–L2.3

- **L2.1 startup pre-warm:** `server.py` now builds `routing.network()` and
  `database.connections(day)` before listening. `ATLAS_DATE` selects the date;
  otherwise it uses today. The first Hartford→Springfield HTTP plan after
  startup returned HTTP 200 in 0.66 s, compared with the handoff's 19.54 s
  cold-request baseline. Existing response keys were preserved. Focused test,
  full suite (42 tests), compilation, and diff checks passed.
- **L2.2 plan early exit:** `routing.scan` accepts the plan destination and
  stops once sorted departures exceed the best destination arrival. Synthetic
  local and intercity through-ride tests preserve the destination itinerary
  while consuming fewer connections; reachability and bubble scans still scan
  the full day. Same-process medians: local 0.013 s vs 1.574 s for the old
  full-scan path (profile baseline 1.98 s); Hartford→Springfield 0.063 s vs
  1.660 s (baseline 2.10 s). Full suite passed.
- **L2.3 reverse latest:** `routing.latest()` proposes a minute from the
  Mobility Bubble reverse computation and certifies it against the forward
  planner at that minute and the next; disagreements use the exact former
  binary search. The fixture and three sampled real-data pairs returned the
  same complete result dictionaries as binary search. A target-origin cutoff
  in the reverse pass avoids scanning departures earlier than the proposed
  latest start. Warm composite median was 0.952 s vs the profile baseline
  7.84 s; the post-L2.2 binary-only counterfactual was 0.834 s. Full suite
  passed (42 tests).

- **L2.4 bubble walk propagation:** replaced up to 12 full-dictionary passes
  per reverse fixpoint round with a queue that revisits only stops whose
  feasible time improved. The Hartford 2026-11-17 reference classification
  stayed at 1,034 reachable, 12,041 unreachable, and zero unknown. Three-run
  warm classification median fell from 2.095 s to 1.194 s (43% faster). The
  12 focused bubble tests passed; the final full suite passed (42 tests),
  along with Python compilation and `git diff --check`.
# Implementation record — reviewed PDF fallback foundation (Codex, 2026-11-15)

- Added `pdf_ingest.py` and PDF tables to fresh SQLite builds. A PDF is accepted only with a human-reviewed manifest containing the official source URL, SHA-256, retrieval/effective dates, extraction method and reviewer metadata. OCR manifests must name an OCR extractor; invalid hashes, dates, times, duplicates and non-chronological stop times are rejected.
- Normalized PDF documents, schedule rows and stop times coexist separately from GTFS. Ambiguous, pending, low-confidence or unlinked rows are retained for audit but are never marked routing-eligible; routing does not consume PDF rows yet. This prevents a timetable stop name from becoming invented geometry.
- Added read-only `GET /api/v1/pdf-schedules` for source traceability and five fixture tests covering reviewed OCR records, ambiguity, pending/unlinked gating, hash mismatch and chronology. This is a foundation, not M0.1 completion: real official PDF extraction, source discovery, reviewer tooling, activation/version rollback and PDF routing remain open.

## Codex session — external smoke test

- Added `scripts/external_smoke.py`, a standard-library-only command that starts the real loopback server on a temporary port, checks the homepage/controller plus metadata, coverage, stop lookup and PDF registry endpoints, optionally exercises a Hartford plan, and always shuts the server down. This gives a normal Terminal workflow independent of Codex's socket restrictions and avoids claiming browser acceptance.

## Codex session — MBTA full-mode coverage

- Replaced the importer’s hard-coded MBTA commuter-rail-only filter with `config/coverage.json`. The MBTA policy selects agency `1`, route types 0–7, and a Boston/southern New England bounds policy; other feeds retain the default regional clip unless configured otherwise.
- Corrected clipped-trip persistence to retain the published `stop_sequence` instead of re-numbering retained stops. Connections therefore cannot be invented across an out-of-scope stop.
- Rebuilt the local database from the already-downloaded official MBTA archive without refreshing the network: 366 routes, 113,694 trips and 7,604 stops. The archive reported 605 invalid coordinates and 6,218 scoped transfer rules not modeled; these remain visible limitations. This is expanded scheduled coverage, not proof of live service or completed MBTA transfer/accessibility validation.

## Codex session — minimalist transit theming

- Added a separate `web/theme.css` layer so visual changes do not tangle with controller behavior. Light, dark and system modes now share the same tokenized surfaces, controls and focus treatment.
- Chose a quiet, desaturated basemap with solid published route colors by feed/GTFS route color. Estimated walking/scooter links remain the single warm dashed visual, preserving the distinction between scheduled transit and geographic estimates. Route browsing buttons use the same solid color stripe.
- No routing semantics or stored browser data changed. Static JS/CSS validation remains required; full visual browser acceptance still belongs in the external smoke/browser workflow.

## Codex session — SLE and optional MTA rail

- Verified the loaded data already contains Shore Line East: 40 `hartford:SLE` trips across New Haven, Branford, Guilford, Madison, Clinton, Westbrook, Old Saybrook and New London; the Amtrak archive also publishes a separate Shore Line East slice. It remains core regional scheduled coverage rather than a fabricated line.
- Added an optional LIRR feed entry and `--include-optional` import path. Optional feeds are excluded from planner scans by default; the UI toggle sends `include_optional=1` to include them after import. This keeps the core map/planner focused while allowing broader MTA rail exploration.
- Added a ranked keyboard-accessible stop picker with feed labels, replacing reliance on the browser-native datalist for station selection. Raw IDs remain accepted for compatibility but are no longer the primary user-facing label.

## Codex session — source-backed fare estimates

- Added `fares.py`, `/api/v1/fares`, and itinerary fare display. The first supported table is the adult one-way CTrail Hartford Line matrix effective 2026-07-01, with source and purchase links included in responses. Direct Hartford Line plans now show the calculated fare.
- Added the current regular adult CTtransit local 2-hour fare as a simple supported fare. Express routes, reduced fares, passes, fare capping, and unsupported mixed-agency combinations remain explicit unknown/partial results instead of guessed prices.
- Fare estimates are informational scheduled-data calculations, not ticket guarantees. Fare tests cover matrix symmetry, unknown stations, local-bus fare and express-zone gating.

## Codex session — unified TUI and LIRR feed correction

- Added `scripts/atlas_tui.py` as the single terminal control panel for starting/stopping the web app, core or optional feed preparation, external smoke tests, regression tests and feed status. It uses only the Python standard library and writes the server log to ignored `data/atlas-tui-server.log`.
- Corrected the optional LIRR current static URL from `gtfs_lirr.zip` to `gtfslirr.zip`; the former produced the reported 403 because it was the wrong object name. The MTA developer resource confirms LIRR feeds are available without an API key, and the current static URL is recorded by the feed registry sources. The legacy MTA URL remains documented by public feed catalogs as historical fallback evidence.

## Codex session — 12-hour trip scheduling

- Browser time fields now accept explicit AM/PM values such as `8:00 AM` and `11:59 PM`; itinerary, departure, return and latest-start displays use a 12-hour clock. The API and routing engine remain integer service-day seconds, so existing clients and overnight behavior are preserved.
- This is user-selected trip scheduling only. No recurring reminders, background jobs or automated notifications were added.

## Codex session — Amtrak CT/MA station codes

- Added `config/station_codes.json` for the Amtrak stations actually present in the loaded CT/MA regional data. The API now exposes `station_code`, state and human label fields; the stop picker displays codes such as HFD, NHV, SPG, WOR and BOS and searches them through the same ranked picker. Feed IDs remain unchanged.

## Codex session — local MCP connector

- Added `scripts/atlas_mcp.py`, a dependency-free newline-delimited JSON-RPC MCP server that exposes Atlas metadata, stop search, coverage, departures, supported fares and scheduled trip planning.
- Chose stdio plus the existing loopback HTTP API so local Ollama hosts and other MCP-capable clankers can use the same routing and fare behavior as the browser without duplicating the engine or requiring credentials.
- The connector deliberately does not launch the web server, fetch live arrivals or imply complete regional coverage. The Atlas API must be running locally, and the README includes a generic MCP client configuration example.

## Codex session — Ollama MCP bridge

- Added `scripts/ollama_mcp_chat.py` for local setups where Ollama is installed without a separate MCP-capable desktop host. It launches the Atlas MCP server, translates its schemas into Ollama `/api/chat` tools, executes returned tool calls, and feeds results back into the conversation.
- Kept the bridge standard-library-only and local-only. Ollama remains on `127.0.0.1:11434`; Atlas remains on its loopback HTTP port. This is an adapter for local experimentation, not a remote service or production agent runtime.
- The bridge defaults Qwen3's `think` API option to false for responsive transit lookups, with `--think` available for complex requests. This follows Ollama's documented Qwen3 thinking toggle rather than hiding model output after generation.

## Codex session — local HTTP MCP adapter

- Added `scripts/atlas_mcp_http.py` as a loopback-only Streamable HTTP adapter over the canonical MCP dispatcher. This makes the same Atlas tools usable by Open WebUI while preserving stdio for LibreChat and the Ollama bridge.
- The adapter is deliberately single-user and local: it does not add authentication, remote exposure, live data or a second routing implementation. Docker clients need an explicit host-gateway configuration.

## Codex session — Chromebook TUI AI controls

- Extended `scripts/atlas_tui.py` with Atlas/Ollama health checks, model listing, guarded Ollama start/stop, and a foreground launch path for `ollama_mcp_chat.py`. This keeps the Chromebook workflow in one terminal without making Ollama or the MCP bridge a recurring background task.
- Reworked the TUI into a simple default menu (`Start Atlas + Ollama`, chat, status, Advanced) while retaining the full feed/import/test controls under Advanced. The implementation stays Python/subprocess based and is portable to Windows PowerShell as well as Chromebook/Linux shells.

## Codex session — Percival identity and personality

- Named the local Ollama/MCP assistant **Percival** and mirrored the canonical `PERSONALITY.md` from `softnessasastrength/percival` into root-level `personality.md`. The transit bridge adds its domain-specific tool rules at runtime rather than forking the canonical character file.
- The bridge loads that file at startup; the MCP server identifies as `percival-transit-atlas`; the TUI presents the simplified Percival stack/chat labels.
- Personality is deliberately grounded: tool-first route/stop resolution, no invented transit facts, and clear separation between scheduled data and live or guaranteed service.
- Added protocol and argument-mapping tests in `tests/test_mcp.py`.

## Codex session — Percival evidence and visit workflow

- Added `atlas_route_report` for source-aware route identity, feed status, optional service-date coverage and explicit limitations.
- Added `atlas_come_to_me` for protected outbound/return visit planning. It is draft-only: no messages, bookings or purchases are sent.
- Refined the TUI into a compact dashboard with one-key start/chat/status/advanced controls while preserving the complete engineering menu.

## Codex session — Open WebUI transport validation

- Added protocol-level HTTP adapter tests for MCP initialize, tool discovery and notifications, including Percival’s evidence and visit tools.
- Documented the two-process Open WebUI validation flow and kept the adapter loopback-only. Actual Open WebUI UI acceptance remains a manual external check because no Open WebUI instance is attached to this environment.

## Codex session — Chromebook LAN launcher

- Added `scripts/percival_lan.py` to start Atlas and the MCP HTTP adapter together. Loopback remains the default; `--lan` is an explicit, loudly warned opt-in for a trusted private network.
- This supports a lightweight phone client while keeping the database and Ollama model on the Chromebook. No authentication or public exposure is implied.

## Codex session — explicit local preferences

- Added `percival_memory.py` and three MCP tools for reading, setting and clearing user-supplied trip preferences. Storage defaults to ignored `data/percival_preferences.json` and uses an atomic replacement write.

## Codex session — separated live-data overlay

- Added `live.py` and `GET /api/v1/live` as an isolated provider layer. The first adapter targets the official MBTA V3 JSON API's predictions and alerts resources; it accepts namespaced Atlas route/stop IDs and normalizes JSON:API resources.
- Chose explicit `live`/`unknown` states instead of silently falling back to schedule data. Provider errors are data and do not make the main HTTP API fail; `/plan`, `/route`, `/bubble` and `/reachability` do not import or invoke live status.
- CTtransit and PVTA were left as `unknown` rather than guessing undocumented endpoints. This is the foundation for a bus-focused trains.fyi-like view, but live coverage still requires one verified adapter per agency and freshness/accessibility UX work.

## Codex session — live board UI

- Added a browser Live board view without changing the existing planner. It accepts provider, route and stop filters and displays provider freshness, predictions, alerts and limitations.
- Chose a provider/stop-board foundation before building a full departure-board visual: countdowns and route/headsign presentation require consistent provider timestamps and normalized route relationships. The next refinement will add those fields where the provider supplies them, with explicit unknown fallbacks.

## Codex session — rideshare boundary

- Deferred Uber/Lyft implementation to a separate last-mile layer. The feasible first slice is user-initiated deep links from known coordinates; it must not imply live price, pickup ETA, availability, accessibility, or booking.
- Uber's current official docs distinguish deep links from estimate APIs and state that deep links do not fetch time or price estimates. No provider credentials, booking flow, or paid API access is being added. PVTA remains schedule-only until its realtime feed contract is published to developers.

## Codex session — Percival UI/UX pass

- Chose IBM Plex Mono as the primary interface font with Ubuntu Mono as the technical/status fallback. The CSS uses local/system font stacks, preserving usability when the fonts are not installed.
- Started the UI pass with a departure-board visual for live rows, countdown-style labels, clearer route/stop empty states, and compact responsive controls. No backend semantics changed.

## Codex session — ordered route chains

- Added an optional `routes` constraint to the connection-scan router rather than creating a second routing engine. The constraint permits repeated continuation on the current route, then requires the next requested route ID after a transfer.
- Added a browser chain builder with add/reorder/remove controls and an MCP `route_chain` argument. Empty chains preserve the original automatic planner behavior; unusual chains are allowed when loaded timetable data supports them, while results remain scheduled feasibility rather than guaranteed timed transfers.

## Codex session — whole-network Amtrak policy

- Replaced Amtrak's implicit regional default bounds with an explicit `whole_network` coverage policy. The existing downloaded official archive rebuilt to 64 routes, 645 stops and 2,461 trips with no importer errors.
- Kept geographic clipping as the default for other agencies. Future feeds can be added through `config/feeds.json` and `config/coverage.json`; importer page provenance now prefers feed metadata and falls back to the URL rather than requiring a hard-coded Python map entry.
- This expands scheduled topology only. Reservation requirements, ticketing, seat availability, live status, and guaranteed Amtrak connections remain unknown unless separately sourced.
- Preference memory is deliberately not conversational inference: only explicit values are saved, validated, and used. It does not change feed provenance or turn unknown service into a fact.

# 2026-11-15 — iOS build path is a SwiftUI client, not a backend port

The iOS request authorizes the M3 investigation but does not imply that this Linux environment can produce a signed iOS build. The existing Python/SQLite Atlas remains the server-side engine. The native client should be a separate SwiftUI/Xcode target that consumes the versioned HTTP API, with no iOS dependencies added to the backend. First implementation should cover coverage/meta, stop and route discovery, scheduled plan results, live status as an explicitly separate surface, and source/uncertainty notices. Secure remote access, pagination/compact payloads, full parameter validation, provenance/expiry gates, authenticated persistence, offline policy and API contract tests are prerequisites for a production iOS client. A PWA is the near-term phone option while Xcode work happens on a Mac.

# 2026-11-15 — API v1 bounded payloads and strict option validation

- Added opt-in `compact=1` metadata and `page`/`page_size` pagination for
  large route/stop metadata arrays, reachability stops, and Mobility Bubble
  reachable stops. Existing callers that omit these parameters retain their
  prior response shape; paginated responses include totals and `has_next`.
- Rejected malformed boolean values, unsupported plan kinds, and unnamespaced
  route-chain IDs at the HTTP boundary. No authentication or write surface
  was added.
- Added contract tests for strict flags/enums, opt-in pagination metadata and
  compact metadata. The focused non-socket suite passes; the full HTTP suite
  remains unexecutable here because opening a local loopback socket returns
  `PermissionError` in the restricted executor.

# 2026-11-15 — Android starts as a thin native WebView shell

The first Android implementation is deliberately a Java/WebView shell in `android/`. It reuses the existing responsive web UI and Python API, remembers a user-selected Atlas URL, and supports both Termux loopback and a trusted Chromebook/Mac LAN host. This is the shortest verifiable path to an APK without creating a second routing engine. It enables cleartext HTTP only for the current local-development workflow; authentication/TLS must precede untrusted-network or production use. A later Compose/native client is justified only after the API contract, offline semantics and secure access are stable.

The TUI now exposes Android development diagnostics/building from the main `d` shortcut and Advanced menu. It reports missing Java, Gradle, ADB, SDK manager and SDK environment variables, but intentionally leaves package installation and system configuration to the user.

# 2026-11-15 — avoid automatic UPnP exposure for Percival

The Android connection problem is device discovery, not a need to expose a
router port. UPnP/IGD would be unsafe while the LAN launcher exposes
unauthenticated Atlas and MCP HTTP endpoints. The planned solution is local
same-network discovery (mDNS/Android NSD or a QR URL handoff), plus an
authenticated private overlay such as Tailscale for remote access. Router
port-forwarding and public tunnels remain blocked until TLS, authentication,
scope-limited MCP access and rate limits exist.

# 2026-11-15 — Percival Outings uses exact forward-certified round trips

- Added a separate `/api/v1/outings` workflow rather than changing the existing
  reachability contract. A selected stop is `verified` only when the router
  returns both an outbound within the configured budget and a return after the
  minimum stay that includes transfers/walking and reaches the origin by the
  hard deadline. `ruled_out` and `unknown` carry specific machine-readable
  reasons.
- Candidate browsing is bounded for interactive use. Every green candidate is
  forward-certified in both directions; overflow is explicitly reported as an
  incomplete search and receives no feasibility classification. Selecting any
  stop runs the exact latest-return workflow.
- The connection scan already considers all catchable departures and retains
  the earliest arrival, so a later faster outbound can correctly replace an
  earlier slow one. A deterministic regression locks this behavior alongside
  no-return, insufficient-stay, final-walk deadline, overnight, and missing
  coverage cases.
- The map UI now has an Outings workspace, verified/ruled-out map markers,
  compact leave/arrive/stay/return/home facts, and privacy-safe copy text that
  contains the meeting stop/window but not the origin or home itinerary.
- No offline transit-pack format exists in this repository; only the versioned
  browser discoveries backup exists. Offline/PWA packs remain deferred and no
  format was invented for this feature.
# 2026-11-15 — published stop order is not numeric adjacency

- Reproduced a missing scheduled connection when a GTFS trip used published
  stop sequences 10 → 20. A query that merely selects the next retained row
  would fabricate a connection when the intervening published stop was
  geographically clipped.
- Store the full trip ordinal alongside the untouched published sequence.
  Join connections on consecutive ordinals and pass those ordinals to the
  scanner and Mobility Bubble for through-ride continuity. Old databases
  fail with an explicit rebuild message instead of silently using the flawed
  numeric join. No downloaded feed was modified in this worktree.
- Five deterministic adjacency/import tests and the full suite provide
  regression evidence. See `ARCHITECTURE_CORRECTNESS.md` for invariants,
  migration and the larger unresolved temporal questions.
- A disposable CTtransit import from the locally downloaded archive produced
  736,288 stop times and 406,627 connections on 2026-11-15; the archive had
  no published sequence gaps. This validates real-feed compatibility, while
  the synthetic fixture proves the gap behavior. The active database was
  untouched. The full suite passed 100 tests; a Bubble HTTP test patch leak
  was fixed after it caused a false failure in the combined run.

# 2026-11-15 — CT/MA operator evidence and UTC timetable normalization

- The requested coverage expansion is source-gated. Greyhound uses the current
  FlixMobility GTFS but selects only `GREYHOUND-us` routes; MTA Metro-North is
  added and LIRR is enabled by default for trips near its stations. Existing
  CTtransit GTFS contains Hartford DASH; the Hartford archive contains SLE.
- GTFS agency times are measured from agency-local noon minus 12 elapsed hours.
  The Greyhound feed uses UTC, so connection materialization now normalizes
  each trip against the selected New York service day. Synthetic tests cover
  normal dates, a next-UTC-day evening trip, and ordering through the fall DST
  fold. The web clock's ambiguous DST-hour presentation remains unresolved.
- A disposable six-feed import passed structural integrity after preserving
  parent stations and removing transfer rules with clipped endpoints. It
  returned a scheduled New Haven → Jamaica outing with both legs, but this
  does not establish ticket availability or a guaranteed Grand Central walk.
- Peter Pan's reachable GTFS file ends in 2024 and is historical test data;
  GHTD Link is booking-dependent; CTtransit Flex was not identified in the
  current official feed. None was fabricated into current routing. Major
  Connecticut city zoom buttons were added; browser access was unavailable,
  so visual acceptance remains pending. See `REGIONAL_COVERAGE.md`.

# 2026-11-15 — PR #71 integration: Percival companion stack meets regional/platform main

Merged `main` (regional coverage, Outings, Android/iOS/KaiOS proofs of concept,
offline packs, street routing) into `feature/percival-mcp` (MCP companion stack).
Resolution principles: no lost work, no invented transit data, per-hunk synthesis
rather than blanket ours/theirs. Notable outcomes:

- **Config is the single source of truth for feed optionality.**
  `prepare_data.py` now propagates `optional` from `config/feeds.json` (main's
  data-driven line) instead of hard-coding LIRR as optional. Per main's verified
  regional record (REGIONAL_COVERAGE.md), LIRR is a default feed, joined by
  Metro-North and Greyhound; the `include_optional` mechanism is unchanged and
  applies to any feed flagged optional.
- **Importer/routing: main's implementations adopted after full comparison.**
  They are supersets of the feature branch's: agency-timezone validation with a
  per-trip timezone column, publisher `seq` retained alongside a dense `ordinal`
  (feature's seq-only change could fabricate a segment after stop clipping),
  per-stage route-chain labels (feature's single-label prefix filter could
  discard the only chain-completing path), GTFS transfer rules, transfer edges
  and optional street-graph walking legs.
- **server.py: main's superset adopted** (Outings endpoint, compact/paginated
  payloads, strict boolean/kind/route-chain validation, expanded city list).
  Feature's duplicate implementations of the same endpoints were identical or
  weaker; its one unique text (meta limitation wording) was stale relative to
  the adopted coverage policy (Amtrak is whole-network).
- **Web UI: synthesized.** Main's Outings/location/all-routes HTML and init
  wiring referenced functions no branch implemented (`browseOutings`,
  `verifyOuting`, `toggleLocation`, `toggleFollow`, `showAllRoutes`,
  `clearAllRoutes`); compact implementations were added against the existing
  `/api/v1/outings` and route-geometry contracts, labelled in `web/app.js` as
  integration completion. Feature's Mobility Bubble function and wiring, dropped
  by the textual auto-merge, were restored; feature's stopId-preserving swap and
  published-route-colour rendering were kept over main's plainer variants.
- **Docs:** API.md and ROADMAP/DECISIONS histories unioned; README rewritten as
  the union of both branches' verified content, corrected where the integrated
  configuration superseded it (LIRR optionality, MNR/Greyhound coverage rows).

## Integration verification fixes (same date, found by the merged test suite)

- **Duplicate `refresh()` in `import_gtfs.py` removed.** Main's file defined
  `refresh()` twice; the second definition shadowed the first, silently losing
  the `include_optional` parameter (breaking `--include-optional` and
  `prepare_data.py`) and the project's descriptive User-Agent (a Mozilla-style
  UA in `download_gtfs`). Synthesized into one `refresh(include_optional=False)`
  that keeps main's validated download path (PVTA scheme fallback, 60 MiB cap,
  required-files check, atomic replace, prior ZIP kept on failure) with the
  documented honest `USER_AGENT` on every request.
- **Synthetic routing fixtures made hermetic again.** Main's `routing.scan`
  refactor reads walk edges via `transfer_graph()`, which queries the real
  database; the synthetic fixtures in `test_core`, `test_bubble`,
  `test_outings` and `test_connection_adjacency` patched the older
  `neighbors()` seam only, so they errored with "unable to open database
  file" on any checkout without a populated `data/atlas.sqlite`. The fixtures
  now also patch `transfer_graph` (the convention one existing test already
  used); no assertion was changed.
- **`tests/test_integration_config.py` added:** guards that
  `config/feeds.json`, `config/coverage.json` overrides and the feed
  `prepare_data.py` special-cases stay mutually consistent.
- The download stub fixture in `test_core` now builds a minimally valid GTFS
  archive (the five required files) to match `download_gtfs` validation; its
  User-Agent and status assertions are unchanged.
- Result: `python3 -m unittest discover -s tests` — 202 tests, all passing,
  no skips, in the integration sandbox (loopback available). Standalone
  baselines for comparison: feature branch 71/71 OK; main alone showed the
  identical 1 failure + 30 errors fixed above, i.e. no integration
  regressions were introduced and three pre-existing main defects were
  repaired en route.

## All-routes overlay: bounded concurrency + cancel (2026-11-15, fix/all-routes-draw_muse)

- `showAllRoutes` in `web/app.js` fetched `/api/v1/route` geometry strictly
  one route at a time (~5.5 s per route on the 10-feed dataset; the all-feeds
  draw never completed in an 11-minute browser window) and a re-click mid-draw
  started a second concurrent draw, because the toggle state only flipped on
  completion.
- Fix is client-side only (server API unchanged): a fixed pool of 8 workers
  shares the route list, progress status updates as each route lands, and a
  draw-generation token makes a re-click cancel cleanly — in-flight results
  are dropped, the partial overlay is cleared, and the button/status reset.
  Changing the agency filter mid-draw now also cancels and restarts.
- Verified: `node --check web/app.js`; full unit suite 202/202; headless
  browser cancel pass (zero page errors, cancel state stable after settle).
  Remaining bottleneck is per-request server cost (~5 s per route call), not
  client serialisation; a bulk geometry endpoint is the follow-up if
  full-scope draw time still matters (see `web/AGENTS.md` guidance).
## Release machinery — tag-driven Debian releases (2026-11-15)

- **Releases are tag-driven.** Pushing a `v*` tag runs
  `.github/workflows/release.yml`: compile plus the full `unittest` suite
  as a gate, then `packaging/build_deb.sh` with the tag's version, then
  the `.deb` attached to the tag's GitHub release. If the tests fail,
  nothing is built or published. The version lives only in the tag;
  `build_deb.sh` stamps it into `DEBIAN/control` and the launcher's
  `version` output. Procedure in `docs/RELEASING.md`.
- **The build script reproduces the hand-built package layout** (first
  release 0.0.1, built by hand the same day): whole checkout under
  `/usr/lib/transit-atlas` with `data` symlinked to
  `/var/lib/transit-atlas/data`, launcher at `/usr/bin/transit-atlas`,
  `/etc/transit-atlas/percival.conf`, systemd unit, and the maintainer
  scripts kept verbatim under `packaging/DEBIAN/` (system user, no
  network I/O; the database is built on first run by
  `transit-atlas prepare`, never bundled).
- **`scripts/setup_ollama.sh` committed.** The hand-built 0.0.1 package
  shipped it — the launcher's `setup-ollama` command execs it — but it
  had never been committed, so a package built from a clean checkout
  would have silently lacked it. It is now in the repo unchanged, mode
  100755.
- **Modes normalised at build time.** The hand-built `.deb` carried the
  build workspace's shared-directory modes (most files 0660, a few
  scripts 0770). `build_deb.sh` ships directories 755, plain files 644,
  and 755 for the launcher, the maintainer scripts, shell scripts and
  every file git records as executable, with root ownership forced via
  `dpkg-deb --root-owner-group` — the same package from any checkout.

## Percival Core bundled into the Debian package (2026-11-15)

- **Owner decision (2026-11-15): one package, two services.** From
  0.0.2 the `transit-atlas` Debian package also carries Percival Core
  (`softnessasastrength/percival`): the Atlas on 127.0.0.1:8000 and
  Percival's front door on 127.0.0.1:8123, one install, one launcher
  (`transit-atlas percival`), two systemd units. The Atlas package
  already carried the Percival *companion* (MCP, chat, personality,
  TUI); this bundles Percival *Core* proper — registry, audit,
  executor, bring-to-me — beside it.
- **The repositories stay separate.** Percival is never vendored into
  this repo's history. It enters the package only as a build input:
  `packaging/build_deb.sh` requires `PERCIVAL_DIR` (a checkout of the
  pinned ref) and stages the whole tree under `/usr/lib/percival-core`
  with a `BUILD_INFO` provenance file. A build without the input
  fails loudly instead of silently shipping the pre-bundle artifact.
- **The pin is deliberate.** `packaging/PERCIVAL_PIN` records the
  exact `percival` commit the package bundles (initially
  `b39a4eeca2963017d73823dff4483d6eaabef0b0`, the head that merged the
  local runner). Bumping it is its own PR with the bump recorded here;
  the release workflow checks out the pinned ref and gates on the
  Percival suite as well as the Atlas suite before building.
- **ARM64 is a hard requirement.** The owner tests in an ARM64 Linux
  VM on Apple silicon. Both trees are pure Python stdlib — the
  package stays `Architecture: all` with zero native binaries — and
  the bundled `scripts/setup_ollama.sh` selects its Ollama asset and
  pinned digest by `uname -m` (amd64 / arm64), failing loudly on
  anything else.
- **Install-and-setup in one (owner addendum, 2026-11-15).** The
  launcher gains `transit-atlas setup`: prepare the data if the
  database is absent (as the `transit-atlas` user where the system
  layout requires it), then bring both services up — `systemctl
  enable --now` under systemd, backgrounded `nohup` servers with
  logs beside the data directory without it — print both URLs and
  the stop commands, and stay idempotent on re-runs.
- **Build-machine independence fix (found during the 0.0.2 bundle
  verification).** `build_deb.sh`'s mode normalisation followed the
  app tree's `data` symlink; on a build machine without
  `/var/lib/transit-atlas/data` (any clean runner — including the
  release workflow's) the dangling symlink failed the build. Every
  earlier build had been masked by a locally installed package. The
  strip pass now covers files and directories only.
- **Printed instructions must work for the person reading them
  (found during the 0.0.2 verification).** A non-root smoke test
  proved the shipped trees are world-readable (the v0.0.1 lockdown —
  0660 files, 2770 dirs, `root:transit-atlas` — does not recur: the
  build normalises to 644/755, `root:root`), but a bare
  `transit-atlas prepare` from a personal account still fails by
  design: the seed registry and database live in the service-owned
  `/var/lib/transit-atlas/data`. The postinst banner and
  `docs/RELEASING.md` now print the working forms — `sudo
  transit-atlas setup`, or `sudo -u transit-atlas transit-atlas
  prepare` — instead of the bare command.
## Transfer-buffer doctrine — first-mile walk exempt (2026-11-15)

- **Doctrine adopted (owner ruling, 2026-11-15): the transfer buffer does
  not apply to first-mile walking.** In `routing.scan`, stops reached by
  walking from the origin are ready to board at their walk-arrival time —
  starting a journey is not a transfer. The buffer still applies in full
  at genuine transfers: after alighting from a vehicle, the next boarding
  waits `arrival + buffer`. Implementation is one line: the walk closure
  in `scan`'s `relax` propagates the popped node's `first` flag to walk
  neighbours, so the origin-seeded closure inherits the exemption while
  transit-seeded closures keep the buffer.
- **Why:** applying the buffer to the first-mile walk systematically
  missed the first catchable vehicle after a short walk (worked example:
  the walk arrives cttransit:12294 at 29008, ready was 29308 under the
  300 s buffer, and the first boardable trip had departed at 29040), and
  the Mobility Bubble then classified hundreds of stops
  `no_feasible_return` even though their return chains resolved. This
  entry supersedes the earlier RT-3 framing of that divergence as a
  reverse-scan defect: `bubble.py` and the reverse scan are unchanged by
  this fix, and `latest_back` values are identical with and without it —
  the divergence was entirely in outbound scan arrivals.
- **Measured effect (reference bubble, current data):** origin
  `hartford:6`, Tuesday 2026-11-17, 08:00, 60-minute budget,
  module-level `bubble.classify` against the packaged database built
  2026-11-15 (nine feeds; `atlas.sqlite` 856,506,368 bytes): reachable
  **810 → 1,151**. The new behaviour loses zero stops the old behaviour
  reached, restores all but one of the feature branch's 1,035, and
  reaches 103 stops that neither the old behaviour nor the feature
  branch reached (closure and exemption combined). Brute-force
  cross-validation against `routing.plan` in both directions: 24/24
  sampled stops agree, 0 mismatches. 1,151 is the reference count for
  the current dataset; the 1,034 recorded earlier in this file was
  measured on the previous six-feed dataset. README carries no numeric
  bubble reference, so this entry is the publication point.
- **Contract encodings amended to state the doctrine, not deleted:**
  `test_scan_walk_then_board_with_buffer` now asserts both halves (a
  first-mile boarding survives an excessive 700 s buffer; a
  post-alighting boarding 60 s after arrival is blocked by a 180 s
  buffer and succeeds with a 30 s buffer), joined by the new
  `FirstMileReturnShapeFixture` regression tests in `test_bubble`. The
  shared golden fixture case `walk-buffer-block` — shared verbatim with
  the Android JVM tests — now expects arrival 900 with modes
  `walk,test:r` instead of NONE; the fixture's `missed-transfer` case
  continues to encode the buffer at genuine transfers. The Android
  engine must be aligned to the same doctrine; its JVM parity suite is
  verified by CI's android-debug check and was not run in the sandbox.
- **Known residual, deliberately untouched:** `transfer_edges.edges()`
  pre-ceils walk length to whole meters before dividing by speed, making
  89,495 directed walk edges exactly +1 s versus computing seconds in
  one step. One stop (cttransit:597) misses bubble reachability by that
  single second (arrival 30370 vs latest_back 30369). Separate parity
  decision; not part of this change.

## Peter Pan import — owner doctrine exception (2026-11-15)

- **The exception, in the owner's words:** "Approve the third-party exception, labelled as unofficial/stale" (2026-11-15). Scope: Peter Pan Bus Lines only, and only the source named below. This entry is the record the repo doctrine requires before third-party data is imported (`scripts/AGENTS.md`: never substitute outdated or third-party data as verified current service).
- **Why an exception was needed:** the official Peter Pan GTFS (Trillium-hosted, listed by MassDOT) was downloaded and inspected on 2026-11-15: its `feed_info.txt` ends service on 2024-12-31, ~10½ months stale. Peter Pan publishes no PDF timetables — its site is a booking engine and the only timetable PDF ever captured on the domain is a 2020 commuter schedule that returns 404 today. Both tiers of the original import task therefore failed on currency and nothing was imported under it.
- **Source used:** the UTEL-UIUC Intercity Bus GTFS (IBG), a 2025 research compilation of US intercity bus services (Ahammed, Shih & Lehe, *Findings*, 2026, doi:10.32866/001c.159284; data at `UTEL-UIUC/intercity-bus-gtfs`). Its `Data_Source.csv` records both Peter Pan agencies — Peter Pan Bus Lines (IBG agency_id 40) and Peter Pan (BZ) (agency_id 71) — as compiled from Transcor Data Services (TDS) platform data, source date 2025-08-15, downloaded 2025-08-29. The IBG Peter Pan calendars are a newer generation than the stale official file, not a re-encode of it: the continuing services run 2025-09-08 → 2028-08-15, where the Trillium calendars end 2024-12-31. Archive SHA-256 at import: `6f592b96af3b5a3d0004ade84a5212aeae0fb53e963d92f52544e2aa019e15b2`.
- **Alternatives considered and rejected:** Transitland's archived copies of the official feed (older than the live stale file — fetched versions end 2023-09-21); the BTS Intercity Bus Atlas (GIS layers only; BTS does not redistribute carrier GTFS); aggregator-generated PDFs (Moovit/BusMaps — demonstrably stale patterns, e.g. one Boston–Springfield trip/day against ~10+ bookable departures).
- **How the import is fenced and labelled:** `config/feeds.json` registers the IBG archive under feed id `peterpan` with `source_status: "unofficial"` and a provenance string naming the compilation, the 2025-08 TDS collection, the exception date and the sunset condition; `config/coverage.json` restricts the feed to agency_ids 40/71 and route_type 3 under the standard regional clip, and its description — which becomes the source `scope` in `data/sources.json` — leads with UNOFFICIAL. The label therefore surfaces in `/api/v1/meta`, Mobility Bubble responses and `atlas_route_report`, not only in docs. Companion fix in `import_gtfs.py`: a source's recorded `agencies` provenance now lists only the agencies its coverage policy actually imports (a compilation archive names every operator it contains, excluded ones included); the Peter Pan source entry lists exactly the two Peter Pan agencies.
- **Imported counts (local build, 2026-11-15):** 56 stops / 59 routes / 242 trips after the regional clip, zero import errors (the archive's Peter Pan content nationally is 78 stops / 76 routes / 357 trips; New York, Philadelphia, Washington and other out-of-region endpoints are clipped by the standard bounds, as with the other regional feeds). Direct Hartford → Worcester trips are in the imported data (PPB 5633FS: 20:45 → 21:45 and 23:50 → 00:50 on Tuesday 2026-11-17); Springfield → Worcester plans on a Peter Pan leg (PPB 6710, 08:15 → 09:10) and Worcester → Hartford on PPB 6713 + Hartford Line. Standing reference checks unchanged (Court Square → `pvta:1495`; `hartford:6` → `pvta:5101` dep 30900 / arr 33428).
- **Sunset condition:** when a current official Peter Pan GTFS (or an official current timetable source) is published, it replaces this source: point `config/feeds.json` at the official URL, remove the exception's `source_status`/`provenance` labelling and the coverage description's UNOFFICIAL lead, and record the replacement in this file.
- **Known labelling nuance:** `service_start`/`service_end` in `data/sources.json` are computed from the imported archive's whole calendar file, so for compilation feeds (this one, and the Flix archive behind `greyhound`) they span every operator in the file rather than the imported agencies. The operator-specific period is stated in the provenance fields instead; do not read the archive-wide span as Peter Pan's service window.
## Fare zones, transfer window and PVTA fare-free — 2026-11-15 (Muse)

- **Hartford Line verified, not just carried over.** All 28 adult one-way
  pairs in `fares.py` were checked cell-by-cell against the official
  CTrail fare table PDF effective 2026-07-01 (hartfordline.com) on
  2026-11-15; the existing table was exact, so it is unchanged.
- **Shore Line East added as a station-pair matrix.** CTDOT publishes
  SLE fares as a station matrix (portal.ct.gov CTrail fares PDF,
  effective 2026-07-01), not zones; modelled like the Hartford Line
  table. Both New Haven stations (Union Station, State Street) map to
  the published "New Haven" fare point.
- **CTtransit express zone system modelled as data.** Official fare
  panels (route 921 map; timetable panels for 901/903/905/907/918/921)
  state zones are labelled A–F per route, zones traveled =
  min(5, max(2, |boarding − exit| + 1)), one-way $3.20/$4.10/$5.00/$6.00
  for 2/3/4/5 zones. The priced route set is the 19 express routes
  verified route-by-route in CTtransit's current GTFS (901, 903, 904,
  905, 906, 910, 912, 913, 914, 918, 919, 921, 923, 926, 927, 928, 940,
  950, 971); a 9xx short name outside that set is an explicit unknown,
  never assumed express and never priced as local.
- **Documented gap — stop→zone.** A stop's zone is published only as
  geography on printed route maps. CTtransit's GTFS ships `zone_id`
  empty for all 9,611 stops and has no fare_attributes/fare_rules, so
  express legs inside itinerary plans remain explicit unknowns
  ("needs a zone count"); `/api/v1/fares` prices express trips when the
  caller supplies `from_zone`/`to_zone`, and `fares.for_plan` accepts
  an `express_zones` mapping for callers that know them.
- **2-Hour Pass (transfer) policy wired in.** Official text
  (cttransit.com/fares/transfers): passes are issued with fare payment;
  local passes give unlimited free local transfers and express travel
  needs additional payment (the difference, per CTtransit's Token
  Transit guidance); "Express 2-Hour passes retain the full value of
  the original zone fare paid, providing unlimited local and express
  rides for the number of zones paid", with additional payment for a
  higher zone fare. Timed itineraries now price leg-by-leg: covered
  legs are itemized at $0 with `covered: true`, top-ups are charged as
  differences, and the window is anchored at the first purchase (the
  official text does not restart it on a top-up — recorded assumption).
  Rail legs neither use nor extend the bus pass. An unpriced express
  leg breaks the chain: later bus legs are priced as new purchases with
  a note rather than silently assumed covered. Untimed itineraries keep
  the previous behaviour exactly (local legs collapse to one $1.75
  entry). The owner's lead — "a two-hour transfer policy with the
  purchase of an express ticket" — is confirmed and is broader than
  stated: the express pass also covers further express rides up to the
  zones paid, and a local purchase carries value toward express.
- **PVTA is $0, dated, with one exception.** MassDOT's FY27 RTA
  assistance (mass.gov, 2026-06-10) funds systemwide year-round
  fare-free RTA service; PVTA's contract runs to 2027-06-30 and its
  FY2025 statements record fares collected only on the B79
  Amherst–Worcester route. PVTA legs price at $0 labelled
  "currently fare-free" with the as-of date; the B79 is priced from its
  published town-pair table on pvta.com (pairs the table marks "X"
  stay explicit unknowns). The legacy $1.50 table still shown on
  PVTA's fares page is historical context and was NOT modelled.
- **MBTA deferred.** Commuter-rail zone fares (1A–10 plus interzone)
  are the bulk of MBTA fare geography; adding only the bus/subway flat
  fares would misrepresent mixed itineraries. Recorded as a gap, not
  priced.
- **Labelling.** New fare results carry `estimate: "rough"`, a `basis`
  (flat / zone count / station pair) and an `as_of` retrieval date.
  Hartford Line results are byte-identical to before. One deliberate
  label correction: a bus-only itinerary's top-level `product` now
  names the CTtransit local fare instead of the Hartford Line product
  (amounts and statuses unchanged).
## 2026-11-15 — Stop marker treatment (branch feat/stop-marker-treatment_muse)

Owner feedback: the ambient stop dots were visual noise, worst when zoomed in.
Before: every stop in the viewport (up to 600) was drawn with the same
radius-7 / weight-2.5 ring marker used for plan results, from zoom 12 up, with
no way to hide the layer. Now: ambient stops use a small solid dot (radius 4,
weight 1) that never grows; rendering is density-controlled — one dot per
30px screen cell (deterministic, so the same stops win on redraw) inside a
per-zoom budget (150 at z12–13, 350 at z14–15, 600 at z16+); when a plan,
route or bubble result is on the map the ambient field dims so the result
stays prominent, while result stops keep the ring style. A "Stops" toggle in
the map controls hides the ambient layer entirely (aria-pressed, default on).
Popups are unchanged, so click-a-stop planning (Start here / Go here / Meet
here / Departures) works exactly as before wherever stops are shown.
## F-009 saved commute profiles — 2026-11-15

- Owner-requested (Percival feature queue F-009): a commute is a standing
  profile, not a retyped plan query. Profiles live in the existing
  device-local Percival preferences file under a `commutes` key, validated
  by `percival_memory` like every other preference; nothing is stored in
  git and nothing is inferred from conversation.
- Profile shape: home/work as Atlas stop IDs, a preferred route chain per
  direction (outbound and return stored separately — asymmetry is the
  normal case), and declared rideshare legs `{from_stop, to}` where
  transit ends before the endpoint.
- Evaluation (`commute.py`; MCP tools `percival_get_commute`,
  `percival_set_commute`, `percival_clear_commute`, `atlas_commute_evaluate`)
  reuses `/api/v1/plan` only; it never reimplements routing. The declared
  chain is planned first; where it cannot run on the evaluated date, the
  unpinned answer is shown and the note says the preference could not be
  honoured; where it runs, an unpinned comparison states any time cost.
- Rideshare legs are estimates only (F-004 doctrine): haversine distance
  x 1.3 road circuity, drive time at 35-60 km/h, labelled "rideshare —
  estimated drive, not a quote, not booked"; no price, no booking path,
  no rideshare API. Stop coordinates resolve through the route endpoint's
  published stop lists (the stops endpoint searches names, not IDs); a
  stop no hinted route serves yields an explicit unknown, never a guess.
- The return evaluation always includes the last viable return, with the
  search bounded to the service day (deadline 28:00 GTFS extended time).
  An unbounded window demonstrably surfaces the next evening's service
  (a 42:53 "departure") and calls it tonight's last return.
- Verified against the packaged ten-feed data for Tuesday 2026-11-17 with
  representative stops (Enfield St @ Elm St -> Shoppes at Buckland Hills):
  outbound chain 905 -> 82 applied, 07:00 -> 08:41; return chain 82 ->
  Hartford Line applied, transit ends Windsor Locks 19:19, rideshare
  estimate 10-18 minutes (estimated final arrival 19:29-19:37); last
  viable return departs work 18:53, Windsor Locks 20:11. Known
  limitation: the first plan for an unwarmed date can exceed the MCP
  layer's 30-second call timeout (a pre-existing Atlas property, shared
  with `atlas_plan_trip`); warm dates answer in well under a second
  per plan.
## 2026-11-15 — Live vehicles on the map (branch feat/live-vehicles-map_muse)

The live overlay (/api/v1/live, live.py) now plots vehicle positions.
live.py: the MBTA adapter also reads the V3 /vehicles endpoint (normalized
to the same vehicle row shape CTtransit already returned; a vehicles-endpoint
failure degrades to an empty list and never flips the board to unknown), and
_unknown() results carry an empty vehicles list so clients can rely on the
key. Web: a "Vehicles" toggle in the map controls polls both verified
providers every 30 s and draws circle markers (orange; grey and translucent
when the vehicle's timestamp is over 5 minutes old or missing), with a
tooltip (route, vehicle, age, STALE flag) built as a DOM node, and a status
line reporting per-provider counts, stale counts, or "unknown". A provider
that cannot be verified contributes no markers — positions are never
invented. Live board prediction times now render as countdowns for both
providers. Invariant preserved: live data is informational only and never
alters scheduled routing or feasibility.
## 2026-11-15 — GTFS-RT protobuf spike (branch spike/gtfs-rt-protobuf_muse, TESTING ONLY)

Under the owner's 2026-11-15 testing-only doctrine exception (not a
production adoption, not a standing doctrine change), the MTA MNR/LIRR
combined GTFS-RT feeds were decoded end-to-end with a protobuf binding in
spikes/gtfs_rt/. Findings: routes join the static feeds perfectly on both
railroads; LIRR trip IDs join 126/126; MNR trip IDs join 0/207 (different
identifier space from the imported static feed's composite IDs); the MNR
feed carries no vehicle entities; Amtrak has no public GTFS-RT and its
map payload is encrypted. Full evidence and the production-cost options
(vendored minimal decoder recommended if adoption is ever approved) are
in spikes/gtfs_rt/README.md. No shipped code imports the spike.
