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
- Preference memory is deliberately not conversational inference: only explicit values are saved, validated, and used. It does not change feed provenance or turn unknown service into a fact.
