# Checkpoint validation — 2026-11-12

- `python3 -m unittest discover -s tests -v`: **14 passed**. Synthetic tests cover extended GTFS times, malformed times, holiday removal/addition, weekend filtering, staying on a vehicle, tight-transfer rejection, pickup/dropoff restrictions, overnight seconds, latest-start search, estimated ground links, API date/range validation and unknown endpoints.
- `python3 -m compileall -q import_gtfs.py database.py routing.py server.py scripts tests`: passed.
- Generated local SQLite `PRAGMA integrity_check`: passed (`ok`).
- Direct API metadata smoke check and active-service query: passed against local imported data.
- Initial checkpoint browser/end-to-end verification was not performed. See the newer desktop record below.
- PDF fixture tests and full GTFS fixture/import validation: **not implemented**.

These tests establish limited checkpoint behavior, not complete GTFS compliance, complete source coverage or safe travel recommendations. Do not mark M0 or M0.1 complete on this evidence.


## Desktop proof-of-concept verification

- 17 Python tests passed, including real loopback HTTP requests for page/controller delivery, API error/status handling and metadata contract.
- `node --check web/app.js` and Python compilation passed.
- Real local database: Hartford → Springfield on 2026-11-12 at 08:00, no ground transfers; outbound and return were found. This is a scheduled-data smoke test, not validation of operation or reservations.
- Browser validation **blocked**: Playwright's bundled Chromium was absent; system Chromium failed with `socket() failed: Operation not permitted` creating its Unix-domain process socket. Additional single-process startup did not resolve it. No screenshots or successful browser interaction are claimed.
- `tests/browser_smoke.cjs` is provided but **not passed here**. It exercises 905 route/trip selection, a rail return query, bookmark/journal persistence, literal-text rendering, backup export/import and sources in an isolated browser profile. Install Playwright and its Chromium as development-only test dependencies; with the server running, use `node tests/browser_smoke.cjs`. Optional `CHROMIUM_PATH`, `ATLAS_URL` and `ATLAS_DATE` select a browser/server/service date. A matching imported feed date and CTtransit/Hartford data are required.
- No macOS/Apple Silicon or Safari execution was available. M0.D remains pending browser acceptance. M0/M0.1 are incomplete.
