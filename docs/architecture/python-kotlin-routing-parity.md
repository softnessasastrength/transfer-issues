# Step 8: Python/Kotlin routing parity

The owner selected **B: shared Python/Kotlin parity testing**.

## CI failures inspected before implementation

Step 7 CI run `43304734966` failed in two separate jobs:
- **Python:** 47 tests executed, 7 errors, caused by `tests/test_core.py` mocking the old `neighbors` path but not the newer `transfer_graph` dependency. As a result tests attempted to read a nonexistent production `data/atlas.sqlite` in CI. Fixed the fixture to mock `transfer_graph` with an empty adjacency, retaining the isolated synthetic nature of the test.
- **Android:** `android-actions/setup-android@v3` failed trying to install obsolete SDK package `tools`. The compile and Kotlin tests never started. Removed that action and use the Android SDK command-line tools available on the GitHub Ubuntu runner; the explicit `sdkmanager` step remains. Actual runner success still needs verification.

## Shared golden contract

`tests/fixtures/routing_golden.psv` defines 13 synthetic journeys in a language-neutral pipe-separated format:
- stops `a`, `b`, `c` with fixed synthetic coordinates;
- links with trip ID, route, sequence, departure/arrival, pickup/dropoff flags;
- directed walking transfer edges with duration;
- origin/destination, start/deadline, transfer buffer;
- expected arrival (or `NONE`) and ordered leg modes.

`tests/test_routing_golden_parity.py` feeds these fixtures through the real Python `routing.plan` with only database and adjacency boundaries mocked. `RoutingGoldenParityTest.kt` reads the **same fixture file** and feeds the Kotlin `OfflineRouter.plan` in memory. Both assert arrival time and leg-mode sequence. This detects semantic divergence without live feeds or external data.

## Verification limits

- The shared test compares two implementations against one independently specified expected result; it does **not** claim that two matching errors imply correct GTFS behavior.
- Test fixture scenarios cover direct, unavailable, pickup/dropoff, through rides, missed transfers, walking, overnight, same-stop and deadline cases. No calendar, DST, parent station, service frequency, large-graph performance or real-feed coverage is established.
- Do not claim Android compilation or parity passing until the new CI run completes successfully. CI must also compile the existing UI and SDK integration.
- No feeds were downloaded, no prior PRs merged, and no app release created.

## Next decisions

A. Fix any remaining CI/build failures and verify Kotlin/Python golden parity on every PR.
B. Expand golden cases to calendars, overnight service, and parent-station transfers.
C. Validate against selected official GTFS and OSM datasets.
D. Add Android emulator end-to-end offline installation and airplane-mode tests.
