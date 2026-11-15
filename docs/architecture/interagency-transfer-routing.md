# Step 2: official-first interagency transfer routing

**Decision B (owner-approved):** respect official GTFS transfer rules first, then infer short walking/cycling links between nearby stops, clearly labeling these as geographic estimates. This is a **draft** implementation and is not a street-verified pedestrian graph.

## Code

- `transfer_edges.py`: directed transfer graph with published GTFS rules, parent-station expansion, type 3 forbidden connections, type 2 minimum time, and proximity candidates within a configurable radius (default 500 meters). Estimates use straight-line distance × 1.3 at 4.5 km/h walking or 12 km/h cycling; all ground edges remain labeled estimated, including official links whose actual path is not validated.
- `routing.py`: existing Python connection-scan planner now uses the shared graph and a priority-queue walking closure. Walking links can chain; the default boarding buffer remains 300 seconds in the existing planner. Published forbidden transfers override geographic proximity in their specified direction.
- `tests/test_interagency_transfers.py`: synthetic tests for nearby cross-agency links, forbidden directed transfers, minimum times, parent-station rules, radius limits, unsupported modes, and boarding feasibility.

## Running

```bash
python3 -m unittest tests.test_interagency_transfers tests.test_unified_network -v
python3 -m py_compile transfer_edges.py routing.py
```

Use the existing Mac mini server with an imported GTFS database for LAN testing. The Step 1 unified output is not automatically configured as the server's active database. Do not claim real cross-agency feasibility without real-feed integration tests.

## Safety and limitations

- A geometric link does **not** prove a safe or legal pedestrian route, accessible crossing, sidewalk, station entrance or scooter allowance. It must never be presented as street-verified.
- This implementation uses the original Python planner for Mac mini testing. **Native Kotlin offline journey routing is not yet implemented.**
- The graph does not automatically install agencies or fetch data. It uses stops/transfers already present in the selected local database.
- Only published transfer restrictions are known; unrecorded barriers cannot be detected until Step 3 offline pedestrian graphs are integrated.
- Scheduled journeys do not guarantee connections, live service or accessibility. No synthetic tests are claimed executed in this session.
- Next architecture decision: choose the offline street network data source/format and routing implementation strategy for Step 3.
