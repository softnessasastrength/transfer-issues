# Connecticut + PVTA: offline iOS proof-of-concept plan

**Status:** Pack exporter implemented, end-to-end offline iOS app **not implemented**. The current SwiftUI shell still needs a running Python backend. Do not claim airplane-mode trip planning works.

## Geographic intent

- CTtransit and Hartford Line are the initial Connecticut feeds in the importer.
- PVTA is included when a valid, imported feed is actually present.
- Other Connecticut operators (local bus, rail and connecting services) need source discovery and validation before calling this the *entire* Connecticut transit network.
- No historical or invented PVTA service may stand in for unavailable official data.

## Generate the first transit data pack on Mac mini

From repo root, after preparing feeds:

```bash
python3 scripts/build_offline_poc.py
# If PVTA is still missing and you only need to test the packaging workflow:
python3 scripts/build_offline_poc.py --allow-partial --output build/offline-ct-pvta-partial
```

The script refuses an existing destination database, does not mutate `data/atlas.sqlite`, and creates:

- `atlas.sqlite`: selected agency records, associated service calendars, shapes and transfer references
- `sources.json`: selected provenance records
- `manifest.json`: SHA-256, byte size, route counts, explicit missing-feed list, and limitations

The pack is **not bundled into the iOS target yet**. Keep build artifacts and downloaded transit archives out of Git.

## Required next implementation stages

1. **PVTA acquisition:** verify a legally usable current GTFS source, record download provenance, validate agency/routes/trips/calendars, and demonstrate that representative PVTA journeys can be calculated.
2. **Connecticut source inventory:** identify missing CT bus and rail agencies and import/validate official feeds. Include ferry or demand-responsive service only after an explicit scope decision.
3. **Native offline database:** bundle versioned SQLite packs in the iOS app or import them into Application Support, verify manifest hash, and expose route/stops/timetables via Swift queries.
4. **Offline journey engine:** port or otherwise embed the existing Python routing semantics; test service exceptions, midnight trips, transfers, and return journeys against desktop fixtures.
5. **Offline maps:** choose licensed vector tile provider and package regionally clipped maps; implement offline renderer. The current OpenStreetMap raster tile URL requires internet and is not a bulk-download source.
6. **Pedestrian/scooter routing:** source and preprocess legally redistributable road/path data, implement a local graph, and distinguish verified street paths from current straight-line estimates.
7. **GPS:** implement native Core Location permission and position marker; GPS should not require network, but first fix may take longer.
8. **Airplane-mode acceptance:** test cold launch, route discovery, timetable, two-leg trip, map, location fix, restart persistence, stale schedule warning, and no accidental network dependency.

## Storage planning

Measure the exporter output first. Map tiles and pedestrian graph will likely dominate. The earlier 1–3 GB total is a design budget, not a measured result or hard cap. Plan download, disk-space and rollback checks for versioned packs.
