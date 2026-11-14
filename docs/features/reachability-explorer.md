# Reachability Explorer — primary Transit Atlas feature

**Status:** Approved product priority; design specification only. **Date:** 2026-11-14.

## Product problem

Traditional journey planners answer “which route connects A and B?” but fail to show whether a destination is *practically accessible* at a chosen time, including the ability to stay and return home. The primary user story is: “Can I visit a friend's home in Wethersfield at 3:00 PM on a weekday without personally driving, and when must I leave?”

**North star:** Make personal car ownership/driving unnecessary for as many journeys as feasible, without hiding cost, service gaps, risk, or reliance on hired vehicles. Transit-first is a preference, never a hard-coded mode bias.

## First-class experiences

1. **Explore from here:** Display a map of reachable geography for a selected departure time, travel-time budget, and allowed modes. Use a schedule-aware *network travel-time surface*, not a circular radius or unverified geographic interpolation.
2. **Arrive by:** Given a specific destination (address/POI/station/coordinate) and deadline, compute feasible latest departures, arrival buffers, and alternatives.
3. **Visit and return:** Given destination arrival time, minimum stay, and latest return-home deadline, compute both directions with actual service calendars and final departures. Report *no feasible round trip* when appropriate. The return constraint is independent of outbound feasibility.
4. **At a glance:** Show reachable, conditional, unverified/missing-data, and unreachable areas distinctly. Let users inspect why an area is excluded and see relevant timetable provenance.
5. **Mode combinations:** Walking, local/express bus, commuter/intercity rail, ferry, and eligible bike/scooter legs. Optional taxi/ride-hailing first/last-mile adapters may be considered subject to user budget and provider availability. No personal driving requirement.
6. **Explain and challenge:** Show candidate journeys, rejection reasons, fare estimates versus quotes, missed connections, uncertainty, data freshness, and why one alternative ranked above another. Allow a contextual override without silently rewriting persistent preferences.
7. **Temporal exploration:** Adjust departure/arrival times, weekday/date, stay duration, transfer buffers, mode constraints, and cost ceiling. Recompute surfaces as schedules change, including overnight and last-trip behavior.

## Architectural approach

- Build on the versioned Python/SQLite transit graph, source-aware service calendars, transfer edges and offline OSM walking/cycling graph where actually installed. Preserve current Android, Termux, Crostini, iOS and browser work.
- Separate **candidate generation** from **feasibility constraints** from **ranking policies**. Transit-first preference must not suppress viable alternatives. Rank only feasible journeys; preserve Pareto alternatives for user inspection.
- Compute bounded, time-dependent multi-source reachability with a chosen origin/time and service-day calendar. Support arrive-by and round-trip evaluation as separate queries. Geographical surface geometry must derive from validated reachable graph vertices and licensed geometry, not straight lines across inaccessible areas.
- Offline regional packs should enable core reachability, map exploration, date-specific schedules and return feasibility without network, within device storage limits. No arbitrary pack-size cap, silent pruning, or hidden network dependency. Online live feeds and provider fare/ETA lookups are optional, clearly marked enhancements.
- An online server may precompute/cache expensive travel-time surfaces for thin clients. KaiOS may display ranked reachable destinations or compact tiles/list summaries rather than compute polygons on-device; it must never claim full offline reachability without a local engine and validated data.
- Version API additions only after inspecting existing /api/v1/ contracts. Candidate endpoints (proposals, not implemented): `POST /api/v1/reachability/surface`, `POST /api/v1/reachability/destination`, `POST /api/v1/reachability/round-trip`. Define request/response schemas and compatibility before code changes.
- Avoid storing identifiable friend names, home addresses, or location history in synthetic fixtures or logs. Use invented addresses/coordinates or anonymous fixture IDs.

## Example acceptance scenario (synthetic, not a timetable claim)

**Request:** An origin in Enfield, CT; destination at an anonymous residential location in Wethersfield, CT; Tuesday 3:00 PM arrival; minimum 90-minute visit; return home by 9:00 PM; walking and public transit permitted; ride-hailing optional with a capped budget.

**Required outputs:** feasible outbound and return alternatives; latest safe outbound departure; earliest/last feasible return; arrival buffer; mode/cost comparison; coverage/source freshness; explicit failure reasons. If no actual data for a service or destination exists, report the gap and do not invent a connection.

## Synthetic validation laboratory

- Deterministic fixture networks with bus, train, ferry, walking, scooter, and optional synthetic ride-hailing edges; no real fares or schedules represented as live.
- Test weekday/weekend/holiday calendars, midnight crossover, timed transfers, missed last departures, delayed/canceled legs, ferry seasonality, directionality, prohibited transfers, walk limits, scooter battery constraints, accessibility constraints, and unverified source data.
- Metamorphic properties: raising a fare without improving any other dimension must not make that option more attractive; improving a leg's travel time must not make the same otherwise-identical itinerary worse; hard deadline violations cannot be ranked feasible; adding a valid service should not remove previously feasible destinations under unchanged assumptions; identical seed/input/policy/data versions must reproduce results.
- Test **round-trip asymmetry**: an easy outbound trip with no valid return is not marked “visit-and-return reachable.”
- Generate reproducible seeds and a Decision Ledger recording inputs, policy/data versions, candidates, rejected reasons, uncertainty and chosen outcome. Minimize failed cases into regression fixtures.
- Validate against representative official feeds and human-checked journeys before claims of regional accuracy; distinguish passing synthetic tests from real-feed, map, offline, and device acceptance.

## Delivery sequence and dependencies

**P0 — Product specification and UX contract (this PR):** define user stories, status vocabulary, schemas, provenance and test matrix. No implementation or test-pass claim.

**P1 — Deterministic reachability core:** offline-capable time-dependent graph search, latest-departure/return constraints, synthetic fixtures and property tests. Depends on validated calendar/transfer data.

**P2 — Destination and return-trip UX:** address/POI resolution from user-installed offline data, explanation and last-trip UI, API compatibility tests.

**P3 — Map surface:** travel-time polygons/raster or vector tiles, temporal slider, source/uncertainty overlays, performance measurements and geographic correctness checks.

**P4 — Multimodal policy adapters:** ferry/rail verified feed coverage and optional ride-hailing quotes/deep links. Provider APIs require authorized access; never fabricate fares or autonomously book.

**P5 — Cross-client integration:** Android and browser first, then Crostini/Termux parity, lightweight KaiOS presentation as supported. Hardware claims only after tests.

Preserve current M0 core verification and existing draft PR stack. This is a **primary feature in product scope**, not authorization to skip prerequisites, silently merge work, or claim implementation.
