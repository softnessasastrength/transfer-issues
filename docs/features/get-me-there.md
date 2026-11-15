# One-tap "Get Me There" — saved destinations

**Authorized request (2026-11-12):** provide a prominent button for "I need to get to 120 Slater Street, Manchester, Connecticut."

## Intended experience

- On the map-first home screen, offer a clear **Get Me There** action alongside Explore.
- Support a user-defined saved destination preset: **120 Slater Street, Manchester, CT**. Treat this as an address, not a verified transit stop or geocoded coordinate.
- Request current location only after a user action and platform permission; allow a manually selected origin when location is unavailable or declined.
- Resolve destination coordinates through an explicitly sourced geocoder when connected, or a previously verified offline address/POI index when offline. Never invent coordinates or claim offline address resolution without an index.
- Compute available date/time-specific scheduled transit options with walk/scooter last-mile connections, source/freshness indicators and return feasibility; distinguish estimated ground connections from verified paths.
- When a valid route cannot be calculated, explain why (missing feed, unavailable service, expired data, unresolved address, no location permission) and preserve manual exploration.
- Store favorites locally and privately, with export/backup; do not transmit them by default.
- Design for airplane mode. A saved verified coordinate should work offline once native map and journey engines are implemented.

## Acceptance tests

1. Tap saved destination -> route calculation with explicit origin and destination.
2. Declined GPS -> manual origin option.
3. Offline -> no mandatory remote geocoding; previously resolved saved address remains usable.
4. Missing/expired CT or PVTA schedule -> honest coverage warning, not fabricated journey.
5. Return-trip option computes feasible last connection rather than assuming service exists.
6. Address input is text-safe; saved destination and journal data are not silently overwritten.

**Status:** product specification only. No routing UI or saved address geocoder implemented by this document.
