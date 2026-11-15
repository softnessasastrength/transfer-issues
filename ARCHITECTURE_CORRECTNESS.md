# Percival architecture and routing correctness — 2026-11-15

## Implementation map

`import_gtfs.py` downloads official archives on demand and builds a combined
SQLite schedule. `database.py` selects calendar services and materializes
departure-sorted connections across the prior, selected and next service
dates. `routing.py` scans connections plus estimated ground links;
`bubble.py` uses a reverse approximation; `outings.py` forward-certifies a
selected outbound and return. `server.py` exposes these through `/api/v1/`.
The web map consumes the API. The Android WebView shell is local source code;
PR #73 adds an unbuilt SwiftUI screen. Offline pack work exists on separate
branches, while this checkout routes from the server's SQLite database.

## Five consequential risks, ranked

1. **Confirmed algorithmic defect: lost GTFS segments and through rides.** The former SQL join
   required consecutive numeric `stop_sequence` values. GTFS only requires
   sequence order. A 10 → 20 trip disappeared; joining the next retained
   row would instead fabricate a segment across a clipped stop. The fixture
   in `tests/test_connection_adjacency.py` reproduces both cases. This PR
   stores full-trip ordinals and uses them for the scan and through-ride state.
   This was reproduced with synthetic GTFS; the tested CTtransit archive had
   zero such published sequence gaps, so no real-feed trip loss was observed.
2. **Confirmed data-boundary gap: dangling transfer endpoints.** The local
   integrity checker reports `transfer without stop` on the current database.
   The importer loads transfers before deleting unused stops. Station rules
   may therefore be ignored or misapplied. Fix and reimport before relying on
   interagency transfer claims.
3. **Reproducible design limitation: incomplete coverage and freshness.**
   Source outer dates do not prove route operation. Geographic clipping and
   unavailable feeds can hide a journey; negative answers must remain
   `unknown` unless the relevant network is complete. Outings handles listed
   missing feeds conservatively, but per-trip provenance and expiry gates are
   incomplete.
4. **Theoretical temporal risk: daylight-saving folds and gaps.** The engine
   represents a service day as integer seconds and shifts neighboring service
   dates by exactly 86,400 seconds. Across DST, elapsed time and local clock
   time diverge; repeated local times cannot be disambiguated from the current
   feed model. This needs a policy and differential fixtures before a claim of
   DST-correct journey timing.
5. **Confirmed trust boundary: unauthenticated LAN MCP.** The optional LAN
   launcher exposes preference tools over HTTP without authentication.
   Production remote access requires auth, origin controls and confirmation
   for destructive preference operations. Native/offline clients lack a
   stable signed-pack activation and rollback contract in this checkout.

## Routing invariants and adversarial checks

- Each transit connection must join adjacent positions of one published trip;
  a clipped intermediate stop must break the chain. The fixture verifies
  nonconsecutive published sequence values and a clipped middle stop.
- A through ride must preserve trip identity and full-trip position; boarding
  another vehicle must satisfy the transfer buffer and applicable rule.
  Existing synthetic tests cover a tight transfer and through ride; the new
  fixture covers a 10 → 20 → 30 through ride.
- A leg must never arrive before departure. Ground links must stay within the
  configured radius, use the selected mode's estimate, and disclose that
  street geometry, crossings and scooter permissions are unverified.
- Service-day offsets must preserve the published service identity. Existing
  tests cover a 24+ time and calendar exception; no DST fold/gap proof exists.
- A round trip is feasible only if a forward-certified return departs after
  the minimum stay and arrives home by the deadline. Outings fixture tests
  include no return, final walk, overnight and minute-boundary cases.
- Missing, expired or clipped data must not become a proof of no service.
  A bounded browse must report unevaluated candidates separately. Feed
  provenance is evidence of published data, never a live-service guarantee.

These synthetic tests prove implementation behavior for specified inputs.
They do not certify every publisher's feed or real-world operation.

## Decision record: route and offline architecture

Keep the current connection scan as the scheduled server reference while
hardening its input contract. Its flat departure order and SQLite storage fit
the current date-specific network and are already tested. Do not replace it
with RAPTOR merely for speed: RAPTOR would require route-pattern normalization
and transfer semantics that the current importer has not established. A
time-dependent Dijkstra could express station constraints flexibly but would
increase graph state and complicate reproducible calendar/through-ride tests.
Revisit algorithm choice only after a differential golden suite measures
correctness and performance on the same fixture and real-feed samples.

For offline clients, prefer a versioned, immutable SQLite-derived pack with
manifest hash, source period, schema version, validation report and atomic
activation/rollback. Keep a portable data contract and golden itineraries
across Python/native implementations; a shared native routing library would
add cross-toolchain and low-resource hardware costs before parity is proven.
Partition by agency/region only when transfer edges across boundaries are
explicit and verified. Cache activation must not silently replace a known
working pack with an unvalidated download. Browser map tiles have separate
licensing and expiry requirements. Personal preferences should remain local
or use authenticated export/import, not transit evidence.

## Migration and resume

The new `times.ordinal` column requires a rebuild from already downloaded
GTFS archives before running the new router on an existing SQLite file.
`database.connections()` fails explicitly on the old schema instead of
silently dropping nonconsecutive segments. The importer keeps the published
`seq` for timetable display. Rebuild into a disposable data directory first,
validate imports and integrity, then activate through the existing safe
deployment workflow; do not replace the user's live database blindly.
Next: fix dangling transfer references; add DST policy and fixtures; build a
cross-platform golden itinerary corpus before shipping offline routing.

## Verification and team integration

Run `python3 -m unittest discover -s tests -q` and, for a focused synthetic
smoke test, `python3 -m unittest discover -s tests -p 'test_connection_adjacency.py' -v`.
The full suite passed 100 tests on 2026-11-15. A disposable import of the
already downloaded CTtransit archive produced 736,288 stop times and 406,627
connections for 2026-11-15, with the new ordinal index. This archive had no
published numeric sequence gaps; the fixture supplies that adversarial case.
The existing active database was not changed. Python 3.13 emitted SQLite
ResourceWarnings from other tests; this work closes the production query
connections and the new fixture connections, but does not claim all handles
in the repository are closed.

The ongoing Outings work should keep selected trips forward-certified; a
reverse Mobility Bubble label alone is insufficient proof. The existing
Bubble HTTP test leaked its manually started routing patches; this branch
repairs the cleanup. PR #76 depends on #75, which depends on #74 and #69.
Rebase or merge in dependency order, then retest with an ordinal-aware database.
The LAN pack integrity checker currently accepts a `times` table without
`ordinal`; update its schema gate before an imported pack can be activated for
this router. PR #73 is an unbuilt iOS source change; PR #72 is toolchain
research, not device validation. The LAN launcher exposes unauthenticated
MCP preference tools; keep it on a trusted loopback/network until the planned
security boundary is implemented.
