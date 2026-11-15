# GTFS-Realtime protobuf spike — MTA rail + Amtrak options

**Doctrine exception scope (owner, 2026-11-15): testing only.** The
stdlib-only rule is waived for testing/evaluation of protobuf GTFS-RT
feeds. This is NOT a production adoption and NOT a standing doctrine
change. Everything in this directory is spike code: it is not imported by
the shipped app, not wired into any server path, and the PR carrying it is
labelled TESTING/SPIKE. Permanent adoption returns to the owner for a
separate doctrine decision.

Method: `decode_mta.py` fetches the public MTA combined GTFS-RT feeds for
Metro-North and LIRR (no API key) and decodes them with
`gtfs-realtime-bindings` (protobuf) in a throwaway venv.
`analyze_alignment.py` joins the decoded route/trip IDs against the
Atlas's imported static feeds in `atlas.sqlite`. One live fetch,
2026-11-15 ~20:41 UTC. Amtrak options probed separately (below).

## What actually arrives

| | MNR (`mnr/gtfs-mnr`) | LIRR (`lirr/gtfs-lirr`) |
|---|---|---|
| Size / fetch / parse | 129,806 B / 0.99 s / 1.2 ms | 69,416 B / 0.96 s / 1.9 ms |
| Header | GTFS-RT "1", FULL_DATASET, timestamped | GTFS-RT "2.0", FULL_DATASET, timestamped |
| Trip updates | **207** (all with trip_id, route_id, start_date, stop_time_updates, event times; only 7 carry delay) | **126** (all fields incl. delay on every update) |
| Vehicle positions | **0 entities** | **58** (all with position, timestamp, stop_id, current_status; none carries route_id — route joins via trip) |
| Alerts | 0 at fetch time | 0 at fetch time |

The `-vehicles` / `-alerts` URL variants do not exist for these feeds:
they return HTTP 200 with an S3 `NoSuchKey` XML error body. A client must
sniff content type, not trust the status code. The combined feed is the
only MTA rail RT product.

## ID alignment with the Atlas's static feeds

- **Routes join perfectly on both railroads**: RT route IDs are exactly
  the static suffixes (MNR 6/6, LIRR 12/12).
- **LIRR trips join perfectly**: 126/126 RT trip IDs (`GO203_26_6011`
  style) match imported static trips.
- **MNR trips do not join at all**: 0/207. The RT feed's plain numeric
  trip IDs (`3264990`) live in a different identifier space from the
  imported static feed's composite IDs (`246135524613552+2449819+1`).
  A production MNR adapter would need MTA's own static GTFS (if its
  trip_ids match the RT space) or a fuzzy join on route + start time +
  stop pattern. Until that is solved, MNR live data can only be
  presented at route level, never attached to scheduled trips.

## Amtrak live status options

- **No public Amtrak GTFS-RT feed exists.**
- Amtrak's Track-Your-Train map endpoint
  (`maps.amtrak.com/.../getTrainsData`) is reachable (HTTP 200, ~1.25 MB)
  but returns an **encrypted base64 payload**, not JSON. Using it would
  require extracting Amtrak's rotating decryption key from their web
  app — fragile and not a foundation to build on. Not recommended.
- Third-party aggregators exist (e.g. TransitDocs ASM) under their own
  terms; none was evaluated here.
- Verdict: Amtrak live stays honestly "unknown" in the Atlas until an
  official feed exists.

## Failure modes observed

- Wrong-variant URLs: HTTP 200 + XML error body (see above).
- MNR vehicle absence is a feed property, not an outage signal: the
  combined feed carried zero vehicle entities on a Sunday afternoon
  with trains running. Absence of vehicles must never be rendered as
  "no trains".
- Feed header versions differ per railroad (v1 vs v2.0); the standard
  bindings decode both transparently.

## What a production adapter would cost

1. **Adopt `gtfs-realtime-bindings` + protobuf as real dependencies.**
   Simplest and most correct; breaks the stdlib-only doctrine outright.
2. **Vendored minimal protobuf decoder (stdlib-only).** GTFS-RT uses a
   small, stable subset of the protobuf wire format; a hand-rolled
   decoder for FeedMessage / TripUpdate / VehiclePosition / Alert is an
   estimated 200–300 lines, skipping unknown fields by wire type. Keeps
   the doctrine; the risk is schema drift, mitigated by the field census
   above (the needed subset is small and stable).
3. **Vendor the generated `gtfs_realtime_pb2.py` + pure-Python protobuf
   runtime.** Still effectively a dependency, ~1 MB of vendored code.

**Recommendation:** if the owner decides to adopt, option 2 fits this
project's doctrine and the observed field subset is small — but solve
the MNR trip-ID join first, or ship LIRR-only trip-level live data with
MNR at route level. Adoption itself is undecided and returns to the
owner.
