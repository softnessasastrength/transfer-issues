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
## 2026-11-15 — Day-trip planner with protected return anchor (branch feat/day-trip-anchor_muse)

Built on the existing outings engine (evaluate/browse) and routing.plan /
routing.latest — no parallel system. outings.plan_day composes an ordered
list of visits: each leg is accepted only if, after the visit's minimum
dwell, a certified path back to the anchor boarding stop still arrives by
the anchor departure (less the transfer buffer); a leg that would break
the anchor is refused with the reason and the day stands partial. The
anchor is either derived (last viable return home from the final visit,
via routing.latest) or pinned to a service: outings.last_service_departure
reads the last departure of a route from a stop out of the imported
connections — never a hard-coded time — and the pinned trip must itself
start a certified journey home. Output states the anchor, its slack, and
what happens if it is missed (the next return, or that none exists that
day). Endpoint: /api/v1/daytrip; UI in the Outings panel.

Owner's anchor belief, checked against the imported schedule: the last
905 from Hartford (origin Asylum St @ Bushnell Park, Enfield-bound) is
**18:17 on weekdays** — not 18:20 — and **17:17 on Saturday and Sunday**.
The mechanism reads the value from the data in all cases.
## 2026-11-15 — MCP HTTP hardening (RT-4) (branch fix/mcp-http-auth_muse)

scripts/atlas_mcp_http.py previously dispatched any POST: wildcard CORS,
a session id that was issued but never checked, no Host validation, and an
unbounded request body — an unauthenticated preference write from a foreign
Origin was demonstrated in red-team phase 2. Now: every POST requires a
per-install bearer token (`Authorization: Bearer`), sourced from
`ATLAS_MCP_TOKEN` when set, else a token file `mcp_http_token` in the data
dir created with mode 0600 and reused across restarts; no
Access-Control-Allow-* headers are emitted; the Host header must name this
machine (loopback names, the bind host, or the machine's LAN addresses when
bound wide); bodies over 1 MiB are refused with 413 before being read.
percival_lan prints the token and its location once at startup. Operator
impact: existing unauthenticated LAN/Open WebUI setups must add the token
header — see README/TERMUX updates in the same change. ollama_mcp_chat.py
speaks stdio to atlas_mcp.py, not HTTP, and is unchanged.
## 2026-11-15 — import_gtfs honours ATLAS_DATA_DIR (branch fix/import-gtfs-data-dir_muse)

import_gtfs.py hard-coded `DATA = ROOT/'data'` while database.py resolved
`pathlib.Path(os.environ.get('ATLAS_DATA_DIR', ROOT/'data'))`, so an import
run and the server could silently work on different data directories; the
Debian package bridged the gap with a symlink. import_gtfs now resolves the
data dir exactly as database.py does. The .deb packaging is untouched by
this change (its symlink becomes harmless redundancy, removable in a
packaging pass). tests/test_import_gtfs_data_dir.py asserts the override
and the default in subprocesses, since the value is bound at import time.
## 2026-11-15 — WP10/EdgeHTML build shipped in-repo (branch feat/wp10-shim_muse)

The verified Windows Phone 10 shim (built during the PR #71 integration
from the audit in WP10_EDGEHTML_AUDIT) now lives in the repo: web/wp10.html
(index.html pointed at the transpiled bundle), web/app-wp10.js (app.js via
esbuild --target=es2017 --format=iife, byte-identical to the verified
2026-11-15 build), web/polyfills-wp10.js (prepended to the bundle;
replaceChildren / Object.fromEntries / Element.remove), and
scripts/build_wp10.sh as the regeneration recipe. docs/WP10.md explains
what it is, why EdgeHTML needs it, and the verification status: Chromium-
verified, with the actual Windows 10 Mobile emulator run still the owner's
step — no EdgeHTML claim is made until then. The bundle is a snapshot, not
a live mirror: re-run the build script whenever app.js changes.
## SEAT (Southeast Area Transit District) feed added (2026-11-15)

- **Decision:** register SEAT as the tenth configured feed
  (`config/feeds.json` id `seat`), owner-approved 2026-11-15 after the
  CT cities sweep found Norwich and Groton with zero stops in the data
  because their local district was not imported. This follows the
  user-controlled network doctrine: the owner selects agencies; no
  other agency was added or changed.
- **Source (GTFS tier; no PDF fallback needed):** SEAT's own GTFS page
  (https://www.southeastareatransitdistrict.com/gtfs-feed/) publishes
  the current archive; the download URL registered is the Remix-hosted
  zip the FTA NTD GTFS weblink lists for SEAT
  (https://gtfs.remix.com/seat_preston_ct_us.zip). The archive
  self-identifies: `feed_info.txt` publisher "Southeast Area Transit
  District", contact info@seatbus.com, version "Updated: Aug 13, 2026".
- **Freshness verified before import:** feed service window
  2026-06-29 → 2027-06-27 (feed_info and calendar agree), covering the
  import date and the 2026-11-17 reference date. Retrieved 2026-11-15;
  archive SHA-256
  f020c77423df7369b02172c68fa80ac22349432d6457bf40a349e9ea49af5a9d.
- **Import (full ten-feed `scripts/prepare_data.py` build, 2026-11-15):**
  SEAT 17 routes / 808 trips / 610 stops, zero errors, zero warnings.
  No coverage-policy entry was needed: every SEAT stop falls inside
  the default regional clip. All nine pre-existing feeds reproduced
  their established counts; the packaged database grew from
  856,506,368 to 863,408,128 bytes.
- **Verification (scratch server on the rebuilt database, Tuesday
  2026-11-17, 08:00):** Norwich Transportation Center
  (`seat:2508339`) and Groton Square (`seat:2508625`) resolve and plan
  to/from Hartford (`hartford:6`) in both directions via New London
  and Amtrak (Norwich→Hartford 08:00→11:36; Hartford→Norwich
  08:00→11:55; Groton→Hartford 08:00→11:36; Hartford→Groton
  08:00→11:15). New London is unregressed: `amtrak:NLC` still
  resolves, and SEAT's New London Union Station stop
  (`seat:2508298`) interchanges with Amtrak by the estimated walk.
  60-minute bubbles: Norwich 219 reachable, Groton 9 (small because
  the bubble requires a same-hour return and SEAT headways are long —
  a service fact, not a planner failure). Standing reference checks
  unchanged: Court Square search returns exactly `pvta:1495`;
  Hartford → Springfield Union Station plans 08:35 → 09:17.
- **Limits:** fixed-route GTFS only. SEAT demand-response service is
  not in the feed and is not represented; nothing about it is implied.
## RIPTA GTFS imported — Rhode Island coverage (2026-11-15)

- **Source (official):** RIPTA's developer page
  (https://www.ripta.com/mobile-applications/) links the GTFS schedule
  dataset; the archive is served from https://ripta.com/RIPTA-GTFS.zip
  (redirecting to https://ripta.com/system/files/gtfs_file/RIPTA-GTFS.zip).
  Retrieved 2026-11-15; 2,235,955 bytes; SHA-256
  2aa2cd24209215c6a2b5d2d170527a555529af5fd58d5041713f35dbc2795f97.
- **Freshness:** feed_info.txt declares 2026-11-01 → 2027-01-15 for the
  Rhode Island Public Transit Authority — current at retrieval, so the
  GTFS tier applies and no PDF fallback was needed.
- **Registered** as feed `ripta` in config/feeds.json. No coverage.json
  override: every RIPTA stop falls inside the default regional clip
  (40.9–43.1, −73.8–−70.5), so the scope recorded at import is the
  default description, like CTtransit, PVTA and WRTA.
- **Service model:** the archive ships no calendar.txt. All service is
  enumerated as type-1 calendar_dates rows (203 rows, 7 service ids,
  dated 2026-10-13 → 2027-01-15; every weekday, Saturday and Sunday in
  the window is listed). The importer's existing calendar/exception
  model honours exactly those dates; tests/test_ripta_feed.py pins the
  behaviour with a synthetic archive of the same shape (service on a
  listed date, none on an unlisted one).
- **Import counts (2026-11-15 local build):** 3,553 stops / 59 routes /
  4,969 trips, zero import errors. The published file carries 5,009
  trips; the 40 not imported are single-stop stub records (one
  stop_time each) that cannot form a rideable segment.
- **Verification (local 7-feed build, Tue 2026-11-17):** Providence
  resolves at Kennedy Plaza (12 stops match; ripta:16400 carries 151
  departures that day). Plans from Kennedy Plaza at 08:00 —
  Providence → Hartford (RIPTA 51 to Providence Station, walk to
  Amtrak, Amtrak via New Haven, arrive 11:36), Providence → Boston
  South Station (Amtrak from Providence, arrive 09:33),
  Providence → Newport (RIPTA 24 to Newport Transit Center, arrive
  09:27). Standing reference checks unchanged: Court Square →
  pvta:1495; hartford:6 → pvta:5101 departs 30900, arrives 33428.
## 2026-11-15 — City selector as a sidebar; favicon + touch icon (branch feat/city-selector-sidebar_muse)

The city buttons floated over the map as an absolute-positioned strip.
They now live in a persistent left sidebar (web/index.html: nav#citySidebar
beside a .mapCanvas wrapper that keeps the map and its overlays), stacked
above the map at narrow widths instead of covering it. Behaviour is
unchanged underneath: a city click still does the same setView + status
update (now with aria-pressed/selected state, plus a Regional view entry
mirroring the reset control, which also clears the selection), and the
sidebar's NETWORK SCOPE buttons drive the existing #agency and
#allRoutesAgency selects — setting their values and dispatching their
change events — so the route browser filter and the all-routes overlay
(including Job 1's mid-draw cancel/restart) see exactly the same state as
before. The selects themselves remain and stay in sync via syncScope.
Also: the app shipped no icons (the owner's Safari log showed 404s for
/favicon.ico, /apple-touch-icon.png, /apple-touch-icon-precomposed.png) —
web/favicon.svg (a minimal compass mark in the app palette) and a generated
180x180 web/apple-touch-icon.png are added with link tags in index.html.
Sidebar implementation note: two pre-existing bare-`nav` rules collided
with the new <nav> sidebar — style.css's `nav{display:flex}` /
`nav button{border:0}` and theme.css's `@media (max-width:900px)
nav{order:3}` (both written for the header nav). The sidebar block in
style.css pins `#citySidebar{order:0;display:block}` and restores button
borders inside it; without that, the sidebar stacked *below* the map at
narrow widths (found by the 400px browser pass, fixed, re-verified).

## setup-ollama extraction — tarball layout defect (2026-11-15)

- **Defect (shipped in the v0.0.1 and v0.0.2 packages):**
  `scripts/setup_ollama.sh` extracted the pinned Ollama tarball with
  `--strip-components=1`. The v0.40.16 tarball's top level is `bin/` +
  `lib/` — `bin/ollama`, with `lib/ollama/` carrying `llama-server`,
  the `libggml*` libraries, licenses, and the `cuda_v12/`, `cuda_v13/`
  and `vulkan/` directories (verified against the real archive: the
  amd64 asset's SHA-256 matches the pinned digest `87bfafb2…`, and
  its member listing shows exactly this layout). Stripping one
  component mapped `bin/ollama` to a regular file named `ollama` in
  the target root; every `lib/ollama/*` member then mapped beneath
  that file and failed, and `set -e` aborted the setup. The script's
  own symlink already expected the unstripped layout
  (`/usr/local/lib/ollama/bin/ollama`).
- **Live evidence:** the owner's first real `transit-atlas
  setup-ollama` run (Ubuntu WSL, 2026-11-15): the download completed
  and the pinned digest verified OK, then tar failed on every lib
  member with "Cannot open: Not a directory" / "Cannot mkdir: Not a
  directory" and no Ollama was installed.
- **Fix:** the extraction no longer strips components. It lives in an
  `extract_ollama` function that also asserts the layout afterwards —
  `bin/ollama` executable and `lib/ollama/llama-server` present — and
  exits nonzero with a clear message if upstream's layout ever
  changes, so the failure is loud at setup time instead of silent at
  inference time. Everything else about the script is unchanged
  (pinned version and per-arch digests, root check, zstd bootstrap,
  `ollama` user, systemd unit with background fallback, model pull
  from `/etc/transit-atlas/percival.conf`). A repo-wide grep confirms
  no other `--strip-components` use exists to twin the defect
  (`packaging/build_deb.sh` and the release workflow never reference
  the extraction).
- **The verification gap that shipped it, and the new rule:** the
  script was digest-verified but never executed end-to-end, so a
  wrong flag survived review — a checksum proves the archive is the
  right one, not that the install works. Rule: an install/setup path
  is not verified until its real operations have run against a
  real-shaped input. `tests/test_setup_ollama.py` embodies it: it
  builds a synthetic `.tar.zst` with the real layout shape and runs
  the script's own `extract_ollama` against it, plus a flat-layout
  fixture that must fail the assertion loudly. The test requires a
  `zstd` binary on PATH (the script installs it via apt on target
  machines) and skips where none exists.
## 2026-11-15 — UI/UX playground (branch feat/ui-playground_muse)

web/playground.html (+ playground.js / playground.css) is a standalone
variant-testing page served like any other web asset at /playground.html.
It does not touch index.html/app.js. It mounts real components against the
real local API: (1) the city/network selector in both forms — the Job 5
sidebar and the previous floating strip + Network select — switchable;
(2) the plan form running /api/v1/plan; (3) bubble controls running
/api/v1/bubble; (4) the scope-filtered route list with the all-routes draw
(bounded concurrency, the Job 1 pattern). Switches: selector form; theme
via the app's own data-theme knob (light/dark/system — no invented design
system); viewport presets (desktop / tablet 768 / phone 400) via a
width-constrained stage, plus a 67% density preset (CSS zoom) — the owner
reports the app "looks fucking amazing" at 67% browser zoom, so that
density is now deliberately testable. Reuse honesty: app.js is a monolith
that binds to the app page's DOM on load, so the playground re-implements
the component wiring against the same endpoints and the app's own
stylesheets rather than importing app.js; that is stated on the page.
## 2026-11-15 — Chat bridge loads only the character prompt (branch fix/mcp-chat-personality-extraction_muse)

scripts/ollama_mcp_chat.py loaded the ENTIRE personality.md as the system
prompt, so the §1 how-to, §3 rehearsal guide and §4 knobs leaked in and the
model paraphrased its own instructions ("my personality is set based on
the rules…", "I'm a fictional character") instead of inhabiting the
character. personality.md's §1 already specified the correct behaviour:
the model receives only §2, between the BEGIN/END CHARACTER PROMPT
markers. The loader now extracts exactly that span
(extract_character_prompt), falling back to the whole file when the markers
are absent rather than failing. The appended operational rule is unchanged,
and personality.md itself is untouched — voice edits remain the owner's
rehearsal calls.

## 2026-11-15 — Offline map pack spike: PMTiles + Range serving + tile-source switch

The base map can go fully local. `scripts/build_map_pack.sh` (operator-run
only — the app never downloads a pack) builds a PMTiles vector pack from
Geofabrik Connecticut + Massachusetts extracts (replication timestamp
2026-11-14T21:20:41Z, downloaded 2026-11-15, MD5-verified against
Geofabrik's published sums — a truncated MA download once passed curl
silently and caused hours of misleading failures, so the check is part of
the recipe) with planetiler 0.10.2 (OpenMapTiles schema). Measured pack:
Greater Springfield–Hartford bbox (-72.75, 41.68, -72.42, 42.18), z8–z16,
**64,943,623 bytes**, 45/45 z12 tiles inside the bbox window present.
Two build gotchas are recorded in the script: planetiler 0.10.x silently
honours only the LAST --osm-path (the states are merged with osmium merge
into one sorted PBF first), and planetiler's own downloader is bypassed
by pre-fetching its auxiliary sources with curl.
Serving: packs live in `DATA/packs/` (never in git); `GET /api/v1/packs`
lists them from a packs.json manifest; `GET /packs/<file>` serves byte
ranges (206/Content-Range, suffix + open-ended, 416, traversal rejected)
because PMTiles readers need Range and SimpleHTTPRequestHandler lacks it.
UI: a Base map switch (Online / Local pack) in the map controls, Local
disabled until a pack exists; rendering by vendored protomaps-leaflet
3.0.1 (BSD-3-Clause) with compact OpenMapTiles paint rules; when local is
active the attribution reads "© OpenStreetMap contributors (ODbL) ·
Local offline pack", and the Sources page lists installed packs.
Verified offline: with every external host blocked in headless Chromium,
the map drew Hartford from the pack (30,553 sampled painted pixels:
water, roads, landcover, buildings), zero page errors. Limitations: no
text labels on the local layer yet (offline glyph fonts are a follow-on),
one pack used by the switch, no in-app download manager (the lan_server
allowlist extension is the named follow-on), and WP10/EdgeHTML vector
rendering is NOT claimed — the emulator decides; a capped-zoom raster
pack is the documented fallback. Full notes: docs/OFFLINE_MAP_PACK.md.
## GBT GTFS imported — Bridgeport coverage (2026-11-15)

- **Source (official):** Greater Bridgeport Transit's GTFS is published
  by its GTFS vendor, Trillium Solutions, at
  https://data.trilliumtransit.com/gtfs/gbt-ct-us/gbt-ct-us.zip — the
  producer URL the Mobility Database registers for Greater Bridgeport
  Transit (mdb-530, Bridgeport, CT). GBT's own "For Transit Geeks"
  page (https://gogbt.com/for-transit-geeks/) is the agency's GTFS
  contact point and is recorded as the registry's official_page.
  Retrieved 2026-11-15; 1,335,948 bytes; SHA-256
  b37a1d7a2331481545aee066eeeaffbd9981fa963b3e02dddf1a8cc2116162b2.
- **Freshness:** feed_info.txt declares 2026-09-23 → 2026-12-27 for the
  archive (publisher Trillium Solutions, Inc.; agency.txt names Greater
  Bridgeport Transit, America/New_York) — current at retrieval, so the
  GTFS tier applies and no PDF fallback was needed. It is the shortest
  window of any configured feed: poll for republication before it
  lapses on 2026-12-27.
- **Registered** as feed `gbt` in config/feeds.json. No coverage.json
  override: every GBT stop falls inside the default regional clip
  (40.9–43.1, −73.8–−70.5), so the scope recorded at import is the
  default description, like CTtransit, PVTA, WRTA, SEAT and RIPTA.
- **Service model:** base service lives in calendar.txt (year-round
  weekday / Saturday / Sunday service ids) and calendar_dates.txt
  carries only four holiday exception rows (2026-11-26 and 2026-12-25
  swap weekday service for Sunday service). frequencies.txt is present
  but empty — no frequency-based trips are excluded. The published
  file lists 1,209 stops; 1,183 are referenced by stop_times and all
  imported (the parent station record brings the stored count to
  1,184); the 26 unreferenced stops are served by no trip in this
  edition. tests/test_gbt_feed.py pins the registry entry and the
  calendar + holiday-exception behaviour with a synthetic archive of
  the same shape.
- **Import counts (2026-11-15 local six-feed build):** 1,183 stops /
  16 routes / 1,753 trips, zero import errors, zero warnings.
  check_data_integrity.py PASS on the rebuilt database.
- **Verification (local six-feed build, Tue 2026-11-17):** Bridgeport
  Transportation Center resolves (16 matches: parent station
  gbt:2382213 plus its berths). Plans from the parent station at
  08:00 — Bridgeport → Hartford (walk to MNR Bridgeport, MNR to New
  Haven, Amtrak to Hartford, arrive 10:25) and Hartford → Bridgeport
  (Amtrak to New Haven, MNR to Bridgeport, arrive 09:51). Departures
  are carried on the terminal's 15 berth stops, not the parent record:
  520 departures across the berths that day, first 05:20. 60-minute
  bubble from the terminal: 467 reachable. Standing reference checks
  unchanged: Court Square → pvta:1495; hartford:6 → pvta:5101 departs
  30900, arrives 33428.
- **Limits:** fixed-route GTFS only. GBT demand-response service
  (GBT Connect) is not in the feed and is not represented; nothing
  about it is implied.

## Norwalk Transit District GTFS imported — Norwalk coverage (2026-11-15)

- **Source (official):** Norwalk Transit District hosts its GTFS on
  the agency's own InfoPoint portal (Avail Technologies' mystop
  platform) at https://mystop.norwalktransit.com/InfoPoint/gtfs-zip.ashx
  — the URL the FTA NTD GTFS Weblinks dataset lists for Norwalk
  Transit District (NTD 10057) and the direct-download URL the
  Mobility Database carries for this service (mdb-2242; that record
  mis-labels the provider as the California "Norwalk Transit System"
  but carries this URL with the Connecticut bounding box, matching the
  archive's stop extents). The older agency-site GTFS_Data.zip URL in
  the deprecated mdb-529 record returns 403 and was not used: exactly
  one live feed exists, and this is it. Retrieved 2026-11-15; 519,729
  bytes; SHA-256
  95315af7abe653b8ebf55903a33ad62ace85d54c9421d62184d5e25014cf6d58.
- **Freshness:** feed_info.txt declares 2026-10-19 → 2027-05-31 for
  the archive (publisher Norwalk Transit District; agency.txt names
  Norwalk Transit District, America/New_York) — current at retrieval,
  so the GTFS tier applies and no PDF fallback was needed. But see the
  service model: the declared end overstates the enumerated service,
  so poll for republication before 2026-12-31.
- **Registered** as feed `norwalk` in config/feeds.json. No
  coverage.json override: every Norwalk stop falls inside the default
  regional clip (40.9–43.1, −73.8–−70.5), so the scope recorded at
  import is the default description, like CTtransit, PVTA, WRTA,
  SEAT, RIPTA and GBT.
- **Service model:** the mirror image of RIPTA's. calendar.txt
  carries a single all-week base service id that no trip uses; every
  trip's service is enumerated date-by-date in calendar_dates.txt as
  type-1 additions — service 26 (weekdays, 531 trips) every Mon–Fri
  2026-10-19 → 2026-12-31 except Thanksgiving and Christmas, service 7
  (Saturdays, 254 trips) through 2026-12-26, service 8 (Sundays and
  holidays, 158 trips) Sundays through 2026-12-27 plus the holiday
  dates 2026-11-26, 2026-12-25, 2027-01-01, 2027-01-18 and 2027-05-31
  running the Sunday schedule. Regular service is therefore
  enumerated only through 2026-12-31 even though feed_info declares
  2027-05-31. frequencies.txt is present but empty — no
  frequency-based trips are excluded. All 253 published stops are
  referenced by stop_times and all imported; there are no parent
  stations (the Burnell Blvd Hub is an ordinary stop, norwalk:9).
  tests/test_norwalk_feed.py pins the registry entry and the
  enumerated-dates behaviour — including that a January 2027 weekday
  has no service — with a synthetic archive of the same shape.
- **Import counts (2026-11-15 local six-feed build):** 253 stops /
  9 routes / 943 trips, zero import errors, zero warnings.
  check_data_integrity.py PASS on the rebuilt database.
- **Verification (local six-feed build, Tue 2026-11-17):** Burnell
  Blvd Hub resolves (norwalk:9). Plans from the hub at 08:00 —
  Norwalk → Hartford (WHEELS route 5 to South Norwalk, MNR to New
  Haven, Amtrak to Hartford, arrive 10:25) and Hartford → Norwalk
  (Amtrak to New Haven, MNR to South Norwalk, WHEELS route 7 to the
  hub, arrive 10:38). 375 departures from the hub that day, first
  05:09. 60-minute bubble from the hub: 221 reachable. Standing
  reference checks unchanged: Court Square → pvta:1495;
  hartford:6 → pvta:5101 departs 30900, arrives 33428.
- **Limits:** fixed-route GTFS only. Norwalk demand-response service
  is not in the feed and is not represented; nothing about it is
  implied. Route 8 (Coastal Link) is operated jointly with GBT; each
  agency publishes its own trips for it, so the Atlas carries both
  agencies' Coastal Link trips under their own feed ids.

## HART / HARTransit GTFS imported — Danbury coverage (2026-11-15)

- **Source (official):** HARTransit publishes its GTFS on its Passio
  platform at https://passio3.com/hart/passioTransit/gtfs/google_transit.zip
  — the URL the FTA NTD GTFS Weblinks dataset lists for Housatonic
  Area Regional Transit (NTD 10051; FTA-checked in the registry
  snapshot) and Transitland's `static_current` for feed
  f-hartransit~ct~us, both checked first-hand this session. It is
  HART's own feed, not the shared UConn/WRTD Passio archive
  (passio3.com/uconn/...), which Transitland carries as the separate
  feed f-university~of~connecticut. No second live HART feed exists:
  the registries name this one URL (plus a historic archive copy).
  Retrieved 2026-11-15; 1,026,450 bytes; SHA-256
  5b68464fd1d6ea8aed1b191fa277984015dccd3c338804977d22ab86d10dab24.
- **Freshness:** feed_info.txt declares the edition 2026-11-14 →
  2026-12-15 (publisher Passio Technologies, feed_version 20260917;
  agency.txt names HARTransit, America/New_York) — a rolling ~31-day
  Passio window, current at retrieval and covering the 2026-11-17
  verification date, so the GTFS tier applies and no PDF fallback was
  needed. Freshness is a polling commitment: poll weekly for the next
  edition.
- **Registered** as feed `hart` in config/feeds.json. No
  coverage.json override: every timed HART stop falls inside the
  default regional clip (40.9–43.1, −73.8–−70.5), so the scope
  recorded at import is the default description, like CTtransit,
  PVTA, WRTA, SEAT, RIPTA, GBT and Norwalk.
- **Importer fix (genuine defect, flagged per instructions):** the
  archive times only its timepoints — 17,580 of its 21,422 stop_times
  rows carry empty arrival/departure times (timepoint 0), which GTFS
  permits. The importer treated one empty time as a malformed row and
  discarded the whole trip, so all 624 HART trips were rejected
  (invalid_or_missing_time ×624) and the feed imported as 0/0/0.
  import_gtfs.py now skips an untimed row — never the trip, and never
  an invented time — and counts it under the warning
  `untimed_stop_times_skipped`; a non-empty malformed time still
  rejects its trip exactly as before. The change is a no-op for feeds
  that time every stop: all six companion feeds reproduced their
  established counts byte-for-byte in the same build.
  tests/test_hart_feed.py pins both behaviours with a synthetic
  archive of the same shape.
- **Service model:** four calendar.txt patterns spanning 2025-01-01
  → 2027-12-31. Weekday service 23684.61481 carries 12 routes (324
  trips); a second weekday pattern, 50236.130201, carries only the
  four LOOP routes (8/9/10/17, 40 trips); Saturday pattern
  50236.130229 carries 13 routes (180 trips); Sunday pattern
  50236.130230 carries only the LOOP routes (80 trips).
  calendar_dates.txt holds 24 exceptions: weekday patterns removed
  on holidays (Thanksgiving and the day after, Christmas Eve/Day,
  New Year's, MLK Day, Memorial Day, Labor Day) and the Sunday
  pattern added on six holidays. Because the importer records the
  window from the calendar data, sources record 2025-01-01 →
  2027-12-31: service past the declared 2026-12-15 edition end is
  the current pattern projected, not a publisher guarantee. The
  archive has no frequencies.txt; all 624 trips carry stop_times,
  and every trip's first and last stop is timed. All 575 published
  stops are referenced by stop_times, but only 125 are ever timed,
  so only those 125 import (see Limits).
- **Import counts (2026-11-15 local seven-feed build):** 125 stops /
  16 routes / 624 trips, zero import errors, one warning
  (untimed_stop_times_skipped 17,580). check_data_integrity.py PASS
  on the rebuilt database.
- **Verification (local seven-feed build, Tue 2026-11-17):** Pulse
  Point resolves (hart:74163, the feed's most-served stop). Plans
  from Pulse Point at 08:00 — Danbury → Hartford (MNR Danbury branch
  to South Norwalk, MNR to New Haven, Hartford Line to Hartford,
  arrive 12:27) and Hartford → Danbury (Amtrak to New Haven, MNR to
  South Norwalk and up the Danbury branch, arrive 11:53). 143
  departures from Pulse Point that day, first 06:05. 60-minute
  bubble from Pulse Point: 62 reachable — an honest sparse count;
  the timepoint-only skeleton and long headways mean few same-hour
  returns (contrast Bridgeport's 467). The Danbury–Norwalk 7 Link is
  direct in the data: five southbound departures from Pulse Point
  (06:30, 07:30, 09:00, 15:35, 16:30), four HART departures from its
  Norwalk WHEELS Hub stop (hart:74703), and a through plan Norwalk
  WHEELS Hub → Pulse Point riding route hart:3261 end to end
  (08:45 → 09:45); hart:74703 sits ~90 m from Norwalk Transit's
  Burnell Blvd Hub (norwalk:9). Standing reference checks unchanged:
  Court Square → pvta:1495; hartford:6 → pvta:5101 departs 30900,
  arrives 33428.
- **Limits:** fixed-route GTFS only, and timepoint-level within it.
  HART demand-response service is not in the feed and is not
  represented; nothing about it is implied. 450 published stops
  appear only as untimed intermediates and are not in the Atlas;
  trips pass them physically, but the Atlas cannot quote a time
  there, so it does not pretend to serve them. HART realtime was not
  touched.
## River Valley Transit GTFS imported — Middletown / lower Connecticut River valley coverage (2026-11-15)

- **Source (official):** the merged agency's GTFS is published by its
  vendor Trillium at
  https://data.trilliumtransit.com/gtfs/ninetown-connecticut-us/ninetown-connecticut-us.zip
  — the direct-download URL the Mobility Database registers for this
  service (mdb-551, marked official; the record still names the
  legacy provider "Middletown Area Transit (MAT)" but its Middletown
  bounding box matches the archive's stop extents) and Transitland's
  `static_current` for the Estuary Transit District feed
  `f-drke-ninetown~connecticut~us`. The archive self-identifies:
  feed_id `ninetown-connecticut-us`; agency.txt names River Valley
  Transit (agency_id 4964, https://estuarytransit.org/,
  America/New_York) — the Estuary Transit District formed 2022-07-01
  from Middletown Area Transit and 9 Town Transit; the agency's own
  homepage states the merger in those terms. Retrieved 2026-11-15;
  1,052,013 bytes; SHA-256
  2b660f9a28d3edefbd01e66317a2cef8e0291575fe44f50aa200410a36622f9c.
- **Duplicate-feed trap, resolved:** a second Trillium URL
  (`rivervalley-ct-us.zip`, Transitland `f-rivervalley~ct~us`) serves
  the same service. Both archives were downloaded and extracted this
  session: all 25 GTFS files are **byte-identical** (per-file SHA-256
  compared; the zip containers differ in packaging only, and both
  declare feed_id `ninetown-connecticut-us` with the same
  feed_version). Exactly one feed is configured — the registered
  ninetown URL above — so no trip can be doubled. A `--flex-v2`
  GTFS-Flex variant of the archive also exists (demand-response);
  it is not a fixed-route schedule and is not imported.
- **Freshness:** feed_info.txt declares 2026-11-13 → 2027-11-04
  (publisher Trillium Solutions, Inc., feed_version "UTC:
  13-Nov-2026 16:39") — current at retrieval, so the GTFS tier
  applies and no PDF fallback was needed.
- **Registered** as feed `rivervalley` in config/feeds.json. No
  coverage.json override: every RVT stop falls inside the default
  regional clip (40.9–43.1, −73.8–−70.5; archive extents
  41.2614–41.6084, −72.8004–−72.0935), so the scope recorded at
  import is the default description, like CTtransit, PVTA, WRTA,
  SEAT, RIPTA, GBT, Norwalk and HART.
- **Service model:** base service lives in calendar.txt as six
  patterns, all spanning 2026-11-03 → 2027-11-30: "Fall 2026
  (Weekday)" Mon–Fri, plus "(MTuW)", "(Thurday only)" [publisher's
  spelling], "(Friday only)", "(Saturday only)" and "(Sunday only)"
  patterns. calendar_dates.txt carries a header and **no rows** —
  this edition publishes no holiday exceptions at all, so holidays
  run the ordinary patterns exactly as published; the Atlas does not
  infer reductions the publisher did not declare. frequencies.txt is
  present but empty — no frequency-based trips are excluded. All
  30,424 stop_times rows are timed (this feed does not exercise the
  untimed-row handling). Of 976 published stops, 859 are referenced
  by stop_times and imported; the 117 unreferenced stops are pruned
  by the importer and not carried. Of 17 published routes, 16 carry
  trips; the seasonal Clinton Trolley publishes zero trips in this
  edition and is not carried. The importer records the service
  window from the calendar span (2026-11-03 → 2027-11-30), which is
  wider than feed_info's declared edition window — service at the
  edges is the current pattern as published, not a separate
  publisher guarantee. tests/test_rivervalley_feed.py pins the
  registry entry and this shape — split weekday patterns, the
  Thursday-only pattern, the absence of any Thanksgiving exception,
  the calendar-span window, unreferenced-stop pruning and the
  zero-trip route — with a synthetic archive of the same shape.
- **Import counts (2026-11-15 local seven-feed build):** 859 stops /
  16 routes / 906 trips, zero import errors, zero warnings.
  check_data_integrity.py PASS on the rebuilt database.
- **Verification (local seven-feed build, Tue 2026-11-17):**
  Middletown's Downtown Terminal resolves (rivervalley:2750874, the
  feed's most-served stop). Plans from the terminal at 08:00 —
  Middletown → Hartford (RVT route 585 Westlake Drive, walk,
  CTtransit to downtown Hartford, arrive 08:56) and Hartford →
  Middletown (CTtransit legs, walk to the terminal, arrive 09:02).
  116 departures from the terminal that day, first 06:00.
  60-minute bubble from the terminal: 351 reachable. Standing
  reference checks unchanged: Court Square → pvta:1495;
  hartford:6 → pvta:5101 departs 30900, arrives 33428.
- **Limits:** fixed-route GTFS only. RVT demand-response service is
  not in the feed and is not represented; nothing about it is
  implied. The Clinton Trolley's absence is the publisher's (zero
  trips in a fall edition of a seasonal service), not an Atlas
  finding that the trolley does not exist.

## UConn / WRTD shared GTFS imported — Storrs + Willimantic coverage (2026-11-15)

- **Source (official):** UConn Transportation Services publishes one
  shared GTFS for both agencies on the Passio platform at
  https://passio3.com/uconn/passioTransit/gtfs/google_transit.zip
  — the URL the FTA NTD GTFS Weblinks dataset lists for Windham
  Region Transit District (NTD 10149; FTA check "Success") and
  Transitland's `static_current` for feed
  f-university~of~connecticut (operator "University of Connecticut /
  Windham Region Transit District"), both checked first-hand this
  session. agency.txt carries a single record naming both:
  "University of Connecticut (UCONN / WRTD)" (agency_id 1541,
  https://transpo.uconn.edu/). It is a different feed from HART's own
  Passio archive (passio3.com/hart/...). No second live feed covers
  this service: the Mobility Database catalog carries no UConn/WRTD
  row at all, and WRTD's own homepage links riders to the same UConn
  Passio portal (uconn.passiogo.com) — there is no WRTD-only archive
  to import alongside, and the shared archive is imported exactly
  once under feed id `uconn`. Retrieved 2026-11-15; 394,502 bytes;
  SHA-256 b1f58af7dd467b94c970d78adfccd6b6dbcfcb5a14899be8af38ebc49dc436b9.
- **Freshness:** feed_info.txt declares the edition 2026-11-14 →
  2026-12-15 (publisher Passio Technologies, feed_version 20260917)
  — the rolling ~31-day Passio window the audit recorded, covering
  the retrieval date and the verification date (Tue 2026-11-17,
  confirmed inside the enumerated service). Freshness is a polling
  commitment: poll weekly for the next edition, as with HART.
- **Service model:** calendar.txt carries 15 patterns, all spanning
  2025-01-01 → 2027-12-31, and calendar_dates.txt carries 2,159
  exceptions — every one a removal (type 2) — across 1,095 dates.
  The removals are the service definition: they express the UConn
  academic calendar (the 676 "Summer/Breaks" pattern is removed on
  677 dates and runs when campus service is reduced, e.g. it is
  active Tue 2026-11-24 while the campus pattern is removed) and a
  Village Heights closure detour switchover (the detour 671 patterns
  run through late November 2026 while the regular 671 patterns are
  removed; the regular pattern is active again by Tue 2026-12-01).
  One weekday pattern carries 277 of the 550 trips across most
  campus routes plus the 674D/E opening/closing trips. The 674 is a
  loop: a single trip runs Willimantic → Storrs → Willimantic. On
  Tue 2026-11-17 five patterns are active (991 all-week, 675, the
  campus pattern, the 674 pattern, the 671 detour pattern), 350
  trips. Twelve of the Red Line's 51 trips ride a service pattern
  with no active weekdays and no additions, so as published they
  never run; the other 39 ride the campus pattern. 42 stop_times
  rows are untimed, all at one stop (Roanoak Ave at Cameo Dr), which
  is therefore the only published stop not carried (229 of 230);
  the importer skips those rows under the PR #107 fix and invents
  nothing. Because the importer records the window from the calendar
  data, sources record 2025-01-01 → 2027-12-31: service past the
  declared 2026-12-15 edition end is the current pattern projected,
  not a publisher guarantee. The archive has no frequencies.txt.
- **Import counts (2026-11-15 local seven-feed build):** 229 stops /
  28 routes / 550 trips, zero import errors, one warning
  (untimed_stop_times_skipped 42). All six companion feeds reproduced
  their established counts exactly. check_data_integrity.py PASS on
  the rebuilt database.
- **Verification (local seven-feed build, Tue 2026-11-17):** both
  service areas verified. Storrs: the Nash-Zimmer Transportation
  Center resolves (uconn:84931 EB / uconn:84932 WB, metres from
  CTtransit's own NZTC stop cttransit:12794); plans NZTC → Hartford
  (08:00 → 08:54, CTtransit Storrs–Hartford service) and Hartford →
  NZTC (08:00 → 09:15) both found; 10 departures from NZTC EB that
  day, first 06:11; 60-minute bubble from NZTC: 83 reachable.
  Willimantic: the Windham Intermodal Center resolves (three stop
  records within ~30 m: uconn:141918, uconn:174794, uconn:208545);
  plans WIC → Hartford (08:30 → 10:50, 674B to Storrs + CTtransit)
  and Hartford → WIC (08:00 → 09:51, CTtransit + walk) both found;
  19 departures from uconn:141918 that day, first 06:23. Interlocks:
  the 674 runs Storrs → Willimantic direct (arrive 08:51 from an
  08:00 start) and the 991 runs Willimantic → Norwich
  Transportation Center direct (10:15 → 10:52). Standing reference
  checks unchanged: Court Square → pvta:1495; hartford:6 → pvta:5101
  departs 30900, arrives 33428.
- **Limits:** fixed-route GTFS only. WRTD Dial-A-Ride and any UConn
  demand-response service are not in the feed and are not
  represented; nothing about them is implied. One published stop
  appears only as untimed rows and is not in the Atlas; trips pass
  it physically, but the Atlas cannot quote a time there, so it does
  not pretend to serve it. Post-edition service is a projection of
  the November pattern (see Service model); if the feed is not
  republished on its rolling cycle, the lapsed edition must be
  handled the way LRTA's was — never silently trusted. UConn/WRTD
  realtime (Passio publishes GTFS-RT under the same /uconn/ path)
  was not touched.

## Milford Transit District GTFS imported — Milford coastal coverage (2026-11-15)

- **Source (official):** the district's GTFS is hosted at
  https://hosted-gtfs-feeds.s3.amazonaws.com/Milford/gtfs.zip
  — the weblink the FTA NTD GTFS Weblinks dataset lists for Milford
  Transit District (NTD 10107; FTA-validated 2026-02-17), the
  direct-download URL of the Mobility Database's record for this
  service (id `ntd-10107`, marked official; its bounding box matches
  the archive's stop extents exactly), and Transitland's
  `static_current` for `f-milford~transit~district`. The archive
  self-identifies: agency.txt names Milford Transit District
  (agency_id 10107 — the NTD ID itself,
  https://www.milfordtransit.com/, America/New_York); feed_info.txt
  names the publisher as Arcadis. Retrieved 2026-11-15; 31,898
  bytes; SHA-256
  101000e07d867a93fd63966d8abff17bb5c48aa5f876cc8e7b3d86df126050d4.
- **Duplicate-feed check:** exactly one live feed covers this
  service. The FTA registry carries one weblink row for NTD 10107
  and the Mobility Database one record; the Database's
  `urls.latest` is its own NTD mirror of this same archive, not a
  second producer feed, and is not configured.
- **Freshness:** feed_info.txt declares 2025-12-31 → 2026-12-31 —
  current at retrieval and covering the verification date, so the
  GTFS tier applies and no PDF fallback was needed. The window
  ends 2026-12-31: poll for republication before year-end.
- **Registered** as feed `milford` in config/feeds.json. No
  coverage.json override: every Milford stop falls inside the
  default regional clip (40.9–43.1, −73.8–−70.5; archive extents
  41.1804–41.2366, −73.1131–−72.9980), so the scope recorded at
  import is the default description, like CTtransit, PVTA, WRTA,
  SEAT, RIPTA, GBT, Norwalk, HART and River Valley.
- **Service model:** base service lives in calendar.txt as two
  patterns — WEEKDAY (Mon–Fri) and SATURDAY — both spanning
  2025-12-31 → 2026-12-31, exactly feed_info's declared window
  (declared edition and calendar span agree, unlike the Passio and
  Trillium editions). The archive has **no calendar_dates.txt at
  all** — this edition publishes no holiday exceptions, so
  holidays run the ordinary patterns exactly as published; the
  Atlas does not infer reductions the publisher did not declare.
  There is no Sunday service. All 57 published trips are loops out
  of Milford Center: each starts at MILFORD-CENTER and ends at its
  southbound twin MILFORD-CENTER-S (the twin is the terminus of
  every loop and originates none). Route 2 publishes weekday trips
  only (11); Routes 3 and 4 run weekdays and Saturdays (23 each).
  All 525 stop_times rows are timed and all 15 published stops are
  referenced by stop_times, so every published stop imports — this
  feed does not exercise the untimed-row handling. There is no
  frequencies.txt. tests/test_milford_feed.py pins the registry
  entry and this shape — the loop, Thanksgiving running the
  ordinary weekday pattern, the Saturday pattern set with Route 2
  absent, the empty Sunday, and the calendar-span window — with a
  synthetic archive of the same shape.
- **Import counts (2026-11-15 local seven-feed build):** 15 stops /
  3 routes / 57 trips, zero import errors, zero warnings.
  check_data_integrity.py PASS on the rebuilt database.
- **Verification (local seven-feed build, Tue 2026-11-17):**
  Milford Center resolves (milford:MILFORD-CENTER, the feed's
  most-served stop, ~110 m from the MNR Milford station,
  mnr:145). Plans from the anchor at 08:00 — Milford → Hartford
  (walk to Milford station, MNR New Haven Line to New Haven,
  Hartford Line to Hartford, arrive 09:27) and Hartford → Milford
  (Amtrak to New Haven, MNR to Milford, walk to Milford Center,
  arrive 09:36). 37 departures from Milford Center that day (every
  weekday trip originates there), first 06:00. 60-minute bubble
  from the anchor: 120 reachable. Standing reference checks
  unchanged: Court Square → pvta:1495; hartford:6 → pvta:5101
  departs 30900, arrives 33428.
- **Limits:** fixed-route GTFS only. Milford Transit District
  demand-response service is not in the feed and is not
  represented; nothing about it is implied. The Coastal Link
  corridor service through Milford rides in GBT's and Norwalk's
  feeds, not this one — this feed is the district's three local
  loop routes only.

## Northeastern Connecticut Transit District (NECTD) GTFS imported — Quiet Corner coverage (2026-11-15)

- **Source (official):** the district's GTFS is hosted at
  https://hosted-gtfs-feeds.s3.amazonaws.com/NECTD/gtfs.zip
  — the weblink the FTA NTD GTFS Weblinks dataset lists for
  Northeastern Connecticut Transit District (NTD 10156;
  FTA-validated 2026-01-14), and Transitland's `static_current`
  for `f-northeastern~connecticut~transit~district` (operator
  `o-northeastern~connecticut~transit~district`, us_ntd_id
  10156). The archive self-identifies: agency.txt names
  Northeastern Connecticut Transit District (agency_id 10156 —
  the NTD ID itself, https://www.nectd.org/index.php,
  America/New_York); feed_info.txt names the publisher as
  Arcadis. Retrieved 2026-11-15; 205,577 bytes; SHA-256
  495aa7c32127ad119af6dd02dfc441e8ce99d2144c802775a0dc5a64f2bc25f7.
- **Duplicate-feed check:** exactly one live feed covers this
  service. The FTA registry carries one weblink row for
  NTD 10156 and Transitland one feed record; no second producer
  feed was found. (The Mobility Database carries no record for
  this service that could be located — consistent with the
  coverage audit's note that the Database is materially
  incomplete for Connecticut; the FTA registry is the
  authoritative cross-check.)
- **Freshness:** feed_info.txt declares 2025-12-31 → 2026-12-31 —
  current at retrieval and covering the verification date, so the
  GTFS tier applies and no PDF fallback was needed. The window
  ends 2026-12-31: poll for republication before year-end.
- **Registered** as feed `nectd` in config/feeds.json. No
  coverage.json override: every NECTD stop falls inside the
  default regional clip (40.9–43.1, −73.8–−70.5; archive extents
  41.5854–41.9848, −71.9898–−71.8564), so the scope recorded at
  import is the default description, like CTtransit, PVTA, WRTA,
  SEAT, RIPTA, GBT, Norwalk, HART, River Valley and Milford.
- **Service model:** base service lives in calendar.txt as two
  patterns — Weekdays (Mon–Fri, 49 trips) and Weekender (Sat–Sun,
  5 trips) — both spanning 2025-12-31 → 2026-12-31, exactly
  feed_info's declared window (declared edition and calendar span
  agree, unlike the Passio and Trillium editions). The archive
  has **no calendar_dates.txt at all** — this edition publishes
  no holiday exceptions, so Thanksgiving and Christmas run the
  ordinary Weekdays pattern exactly as published; the Atlas does
  not infer reductions the publisher did not declare. The four
  colour routes (Orange 22 trips, Green 10, Red-Purple Shuttle
  10, Blue 7) run weekdays only; Sunday service exists, on the
  Weekender route alone. All 704 stop_times rows are timed and
  all 50 published stops are referenced by stop_times, so every
  published stop imports — this feed does not exercise the
  untimed-row handling. The Green route declares
  continuous_pickup (a deviated-style flag in the data; the Atlas
  models the published fixed stops). There is no frequencies.txt.
  tests/test_nectd_feed.py pins the registry entry and this
  shape — the weekday colour-route set, Thanksgiving running the
  ordinary weekday pattern, the Weekender running Saturday and
  Sunday, and the calendar-span window — with a synthetic archive
  of the same shape.
- **Import counts (2026-11-15 local seven-feed build):** 50 stops /
  5 routes / 54 trips, zero import errors, zero warnings.
  check_data_integrity.py PASS on the rebuilt database.
- **Verification (local seven-feed build, Tue 2026-11-17):** the
  Commerce Ave Commuter Lot in Danielson resolves
  (nectd:GREEN-1, the feed's most-served stop). Plans from the
  anchor at 08:00 — NECTD → Hartford (Green route to Killingly
  Commons, walk to CTtransit's own Killingly Commons stop,
  CTtransit to Hartford, depart 08:30 arrive 12:16) and
  Hartford → NECTD (CTtransit to Killingly Commons, walk,
  Red-Purple Shuttle to the anchor, depart 08:00 arrive 10:50).
  18 departures from the anchor that day, first 07:30. 60-minute
  bubble from the anchor: 3 reachable — the honest measure of a
  sparse rural district at that hour. The Orange route's
  southern terminus, Lisbon Landing/SEAT Connection
  (nectd:ORANGE-13), is co-located with SEAT's Lisbon Landing
  stops: plans to Norwich Transportation Center (depart 08:00
  arrive 08:55) and from Norwich Transportation Center (depart
  08:00 arrive 08:25) both found, and the stop carries 5 Orange
  departures that day. In an eight-feed build (the same subset
  plus UConn/WRTD), WRTD's Danielson Downtown stop
  (uconn:84886) sits at identical coordinates to nectd:GREEN-1,
  and the anchor plans to the Windham Intermodal Center via the
  993 (depart 08:00 arrive 09:22), with the reverse also found.
  Standing reference checks unchanged: Court Square → pvta:1495;
  hartford:6 → pvta:5101 departs 30900, arrives 33428.
- **Limits:** fixed-route GTFS only. NECTD demand-response
  (dial-a-ride) service is not in the feed and is not
  represented; nothing about it is implied. NECTD operates
  deviated-route service in practice; the GTFS models it as
  fixed stops and the Atlas represents the feed as published.

## Northwestern Connecticut Transit District (NWCTD) GTFS imported — Torrington / Litchfield County coverage (2026-11-15)

- **Source (official):** the district's GTFS is hosted at
  https://hosted-gtfs-feeds.s3.amazonaws.com/NWCTD/gtfs.zip
  — the weblink the FTA NTD GTFS Weblinks dataset lists for
  Northwestern Connecticut Transit District (NTD 10131;
  FTA-validated 2026-01-14, certification flag set). The archive
  self-identifies: agency.txt names Northwestern Connecticut
  Transit District (agency_id 10131 — the NTD ID itself,
  https://www.nwcttransit.com/about-localbusroute/,
  America/New_York); feed_info.txt names the publisher as
  Arcadis and the edition as nwctd_03082026. Retrieved
  2026-11-15; 77,317 bytes; SHA-256
  4a55e25c960a6c0ebb6afa8a492b7faa884c27364f997b6442840c9a1c174462.
- **Duplicate-feed check:** exactly one live feed covers this
  service. The FTA registry carries one weblink row for
  NTD 10131 and no second producer feed was found. (Neither the
  Mobility Database nor Transitland carries a record for this
  service that could be located — checked first-hand against the
  Database's full schedule catalog and the Transitland Atlas
  feed tree — consistent with the coverage audit's note that
  the Database is materially incomplete for Connecticut; the
  FTA registry is the authoritative cross-check. Secondary
  consumers such as busmaps.com and the Transit app carry the
  same routes and stops from this feed.)
- **Freshness:** feed_info.txt declares 2026-07-20 → 2026-12-31 —
  current at retrieval and covering the verification date, so
  the GTFS tier applies and no PDF fallback was needed. One
  honesty note: the earliest calendar pattern starts 2026-07-28,
  so the declared window overstates enumerated service by eight
  days at the front; the window the importer records is the
  calendar span, 2026-07-28 → 2026-12-31. The window ends
  2026-12-31: poll for republication before year-end, grouped
  with Milford and NECTD.
- **Registered** as feed `nwctd` in config/feeds.json. No
  coverage.json override: every NWCTD stop falls inside the
  default regional clip (40.9–43.1, −73.8–−70.5; archive extents
  41.7269–42.0168, −73.3352–−73.0463), so the scope recorded at
  import is the default description, like CTtransit, PVTA, WRTA,
  SEAT, RIPTA, GBT, Norwalk, HART, River Valley, Milford and
  NECTD.
- **Service model:** base service lives in calendar.txt as four
  patterns — Weekdays (Mon–Fri, 36 trips) and Saturday
  (30 trips), both spanning 2026-07-28 → 2026-12-31, plus two
  winter patterns, WD_Winter (Mon–Fri) and WND_Winter (Sat),
  spanning 2026-08-27 → 2026-12-23 and carrying route 1B
  (Winsted College Only, 6 trips each) alone. The archive has
  **no calendar_dates.txt at all** — this edition publishes no
  holiday exceptions, so Thanksgiving and Christmas run the
  ordinary patterns exactly as published; the Atlas does not
  infer reductions the publisher did not declare. **No pattern
  runs on Sunday**: this district publishes no Sunday service.
  The route named SaturdayTorrington also runs seven of its
  fourteen trips on the Weekdays pattern, as published. Twelve
  of the forty-eight published stops are referenced by no trip
  (among them Litchfield Green, Bantam Post Office and Stop and
  Shop) and are pruned at import. All 770 stop_times rows are
  timed, so this feed does not exercise the untimed-row
  handling. The fare table is published (REGULAR $1.75 with one
  transfer, YOUTH $1.40, SENIOR $0.85); the Job Access route has
  no fare_rules rows. There is no frequencies.txt.
  tests/test_nwctd_feed.py pins the registry entry and this
  shape — the weekday route set including the winter college
  trip, Thanksgiving running the ordinary weekday patterns,
  the Saturday patterns running, Sunday carrying no service,
  the calendar-span window, and the pruning of an unreferenced
  published stop — with a synthetic archive of the same shape.
- **Import counts (2026-11-15 local seven-feed build):** 36 stops /
  6 routes / 78 trips, zero import errors, zero warnings.
  check_data_integrity.py PASS on the rebuilt database.
- **Verification (local seven-feed build, Tue 2026-11-17):** the
  John St stop in downtown Torrington resolves (nwctd:John St,
  the feed's most-served stop, 138 stop_times rows). It sits
  ~25 m from CTtransit's own Mason St @ John St stop
  (cttransit:13578), and the through journeys ride that
  interlock: plans from the anchor at 08:00 — NWCTD → Hartford
  (walk to Mason St @ John St, CTtransit 450 to Waterbury,
  928 express to Asylum St @ Bushnell Park, walk to Hartford
  Union Station, depart 08:00 arrive 11:09) and Hartford →
  NWCTD (CTtransit 83, 928 and 450 to Mason St @ John St, walk
  to the anchor, depart 08:00 arrive 10:41). 38 departures from
  the anchor that day, first 06:30. 60-minute bubble from the
  anchor: 4 reachable — the honest measure of a sparse rural
  district at that hour. Standing reference checks unchanged:
  Court Square → pvta:1495; hartford:6 → pvta:5101 departs
  30900, arrives 33428.
- **Limits:** fixed-route GTFS only. NWCTD demand-response
  (dial-a-ride) service is not in the feed and is not
  represented; nothing about it is implied. NWCTD operates
  deviated-route service in practice; the GTFS models it as
  fixed stops and the Atlas represents the feed as published.
