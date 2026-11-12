# Checkpoint validation — 2026-11-12

- `python3 -m unittest discover -s tests -v`: **14 passed**. Synthetic tests cover extended GTFS times, malformed times, holiday removal/addition, weekend filtering, staying on a vehicle, tight-transfer rejection, pickup/dropoff restrictions, overnight seconds, latest-start search, estimated ground links, API date/range validation and unknown endpoints.
- `python3 -m compileall -q import_gtfs.py database.py routing.py server.py scripts tests`: passed.
- Generated local SQLite `PRAGMA integrity_check`: passed (`ok`).
- Direct API metadata smoke check and active-service query: passed against local imported data.
- Browser/end-to-end verification: **not performed**; frontend controller is absent.
- PDF fixture tests and full GTFS fixture/import validation: **not implemented**.

These tests establish limited checkpoint behavior, not complete GTFS compliance, complete source coverage or safe travel recommendations. Do not mark M0 or M0.1 complete on this evidence.
