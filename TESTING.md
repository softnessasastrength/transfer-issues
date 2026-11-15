# Checkpoint validation — 2026-11-12

- `python3 -m unittest discover -s tests -v`: **14 passed**. Synthetic tests cover extended GTFS times, malformed times, holiday removal/addition, weekend filtering, staying on a vehicle, tight-transfer rejection, pickup/dropoff restrictions, overnight seconds, latest-start search, estimated ground links, API date/range validation and unknown endpoints.
- `python3 -m compileall -q import_gtfs.py database.py routing.py server.py scripts tests`: passed.
- Generated local SQLite `PRAGMA integrity_check`: passed (`ok`).
- Direct API metadata smoke check and active-service query: passed against local imported data.
- Initial checkpoint browser/end-to-end verification was not performed. See the newer desktop record below.
- Reviewed-PDF fixture validation: `python3 -m unittest tests.test_pdf_ingest -v` (hash/provenance, OCR metadata, chronology, ambiguity and routing gate). PDF rows are intentionally kept outside routing; official PDF extraction and stop-link review still require an operator-supplied manifest.
- Standalone external smoke test: `python3 scripts/external_smoke.py`; add `--routing --date YYYY-MM-DD` to exercise the planner. This starts and stops the loopback server itself and uses only Python's standard library.
- Optional MTA fixture coverage: `test_optional_planning_feeds_are_excluded_by_default` verifies that LIRR-style optional feeds stay out of normal plans and enter only with `include_optional=1`.

These tests establish limited checkpoint behavior, not complete GTFS compliance, complete source coverage or safe travel recommendations. Do not mark M0 or M0.1 complete on this evidence.


## Desktop proof-of-concept verification

- 17 Python tests passed, including real loopback HTTP requests for page/controller delivery, API error/status handling and metadata contract.
- `node --check web/app.js` and Python compilation passed.
- Real local database: Hartford → Springfield on 2026-11-12 at 08:00, no ground transfers; outbound and return were found. This is a scheduled-data smoke test, not validation of operation or reservations.
- Browser validation **blocked**: Playwright's bundled Chromium was absent; system Chromium failed with `socket() failed: Operation not permitted` creating its Unix-domain process socket. Additional single-process startup did not resolve it. No screenshots or successful browser interaction are claimed.
- `tests/browser_smoke.cjs` is provided but **not passed here**. It exercises 905 route/trip selection, a rail return query, bookmark/journal persistence, literal-text rendering, backup export/import and sources in an isolated browser profile. Install Playwright and its Chromium as development-only test dependencies; with the server running, use `node tests/browser_smoke.cjs`. Optional `CHROMIUM_PATH`, `ATLAS_URL` and `ATLAS_DATE` select a browser/server/service date. A matching imported feed date and CTtransit/Hartford data are required.
- No macOS/Apple Silicon or Safari execution was available. M0.D remains pending browser acceptance. M0/M0.1 are incomplete.

## Ember session verification — 2026-11-14

- `python3 -m unittest discover -s tests -v`: **29 passed** (17 prior + 12 new Mobility Bubble fixture tests in `tests/test_bubble.py`).
- Fresh `scripts/prepare_data.py` import on 2026-11-14: five feeds imported; PVTA HTTP 403 (gap visible, not filled).
- API smoke on real data (2026-11-17): meta/coverage/route/trip/departures/plan/reachability/bubble all exercised; Hartford <-> Springfield with return; bubble from hartford:6 = 1,034 reachable stops, cross-validated against brute-force plan() on 20 sampled stops with zero mismatches.
- Browser acceptance: `tests/browser_smoke.cjs` **passed** in this environment (Playwright + Chromium, ATLAS_DATE=2026-11-17), plus a bubble-button smoke with zero page errors. This clears the previously recorded Chromium-socket blocker for this environment only; macOS/Safari acceptance is still unclaimed.

## PVTA User-Agent fix verification — 2026-11-14

- Diagnosis probes against `https://www.pvta.com/g_trans/google_transit.zip`: default curl UA -> HTTP 403; default Python urllib UA -> HTTP 403; Safari UA -> HTTP 200; descriptive project UA (`TransitAtlas/0.1 (+https://github.com/softnessasastrength/transfer-issues)`) -> HTTP 200, `application/x-zip-compressed`, Last-Modified Mon, 02 Nov 2026 19:12:54 GMT, 5,456,432 bytes.
- `python3 -m unittest discover -s tests -v`: **30 passed** (29 prior + new `DownloadTests.test_refresh_sends_user_agent`, which stubs `urllib.request.urlopen` locally — no live network — and asserts the User-Agent header is sent and a stale `refresh_error` is cleared on success).
- Fresh `scripts/prepare_data.py`: all six feeds imported, no refresh errors. PVTA counts: 62 routes / 13,381 trips / 1,973 stops, zero import errors, service period 20261102–20261219.
- API smoke on real data (Tuesday 2026-11-17): departures from Court Square, Springfield (`pvta:1495`) = 167; Springfield local plan `pvta:5101` -> `pvta:1495` found (G2, 08:00 -> 08:02:56); Hartford (`hartford:6`) -> Court Square found with Hartford Line rail + PVTA P11 leg (08:35 -> 09:28:46).
- Bubble reclassification, `hartford:6`, 2026-11-17 08:00, 60-minute budget: before — reachable 1,034, unreachable 10,068, unknown feeds [pvta]; after — reachable 1,034, unreachable 12,041, unknown feeds []. The +1,973 unreachable delta equals the PVTA stop count exactly. Bubble from Springfield Union Station (`pvta:5101`): 582 reachable, 580 of them PVTA stops.
