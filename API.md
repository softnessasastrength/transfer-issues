# API v1 — development contract

Base: `/api/v1/`. JSON, read-only GET endpoints. This is an early contract; stabilize and test before native clients. Times are integer service-day seconds in America/New_York. Values above 86400 refer to the following calendar day. A dated trip identity is `YYYY-MM-DD|feed:trip_id`. Entity IDs are namespaced by feed.

| Endpoint | Parameters | Result |
|---|---|---|
| `meta` | none | API version, feeds/provenance, cities, routes, stops, limitations |
| `coverage` | `date=YYYY-MM-DD` | Per-feed imported status and service-range bounds |
| `departures` | `stop`, `date`, optional `route` | Boardable departures on that calendar day; coverage |
| `route` | `id`, `date` | Active trips, published stops/shapes, dated weekday/Saturday/Sunday counts |
| `trip` | `id` | Ordered stop times (original service-day seconds) |
| `plan` | `from`, `to`, `date`, `time`, `deadline` | Earliest itinerary or explicit no-result with coverage |
| `reachability` | `from`, `date`, `time`, `deadline` | Reachable stop IDs, coordinates and earliest arrivals |

Planning options: `mode=walk|scooter`, `radius=0..3000` meters, `buffer=0..3600` seconds, comma-separated `feeds`. `time=0..86399`; `deadline` between `time` and 172799. `kind=latest` searches latest feasible origin start at one-minute resolution. `return=1` and `visit=0..86400` add earliest and latest return feasibility within the same deadline.

Errors use `{"error":"message"}` with HTTP 400 for invalid input, 404 for unknown endpoint, 500 for unexpected server errors. There is no authentication or write API yet; bind to loopback only. No CORS policy or trusted reverse-proxy handling is implemented.

`found: false` means no result under loaded data and calculation limits, **not** that no transit exists. `estimated: false` on a transit leg denotes published schedule data rather than an estimated ground link; it does not mean live service is verified. Current coverage checks indicate the feed's outer date range, not proof that every route operates on a date. Every route/leg includes a feed identifier resolvable to the source registry.

Known contract gaps: unified PDF confidence/validation statuses, per-trip provenance/expiry gates, pagination, full parameter validation and authenticated persistence. These must be completed before M0/M0.1 acceptance and before an iOS client depends on v1.
