# Offline-first storage and availability policy

**Decision date:** 2026-11-12. **Priority:** binding product requirement for all agents.

## Non-negotiable product choice

**Do not optimize Transit Atlas for minimum storage footprint at the expense of offline capability, coverage, detail, reliability or user control.** The owner explicitly accepts large local data packages (2 GB, 5 GB, or more if needed). No arbitrary storage budget is authorized. A functional airplane-mode application is more important than a small download.

This does not excuse corrupt data, runaway logs, duplicate caches, unnecessary copies, unbounded temporary files, or careless battery use. Engineering efficiency is welcome when it preserves the offline experience, but *size reduction is not a product success metric*.

## Essential features must not require internet

- Cold start, map rendering and geographic exploration, route and stop lookup, timetables and service calendars.
- Source-aware transit journey planning, transfers, walking/cycling/scooter connections where the relevant local routing graph exists, last departure and return feasibility.
- Saved destinations, preferences, journey history, color-coded journey maps, local speed profiles and opted-in on-device journey verification.
- Local search/geocoding for supported downloaded areas, including offline address/POI index where available.
- Viewing provenance, coverage gaps and schedule effective dates, and exporting/deleting user-owned data.

The app must report missing/offline-unavailable coverage clearly, never quietly substitute an online service or fabricate a route. A fully offline experience requires *both* a native engine and licensed offline geographic/map data; caching a web page or SQLite route list alone is insufficient.

## Data distribution

- Keep a reasonably sized app binary when convenient, but prioritize comprehensive downloadable **regional data packs** with local SQLite, authoritative timetables, route shapes, licensed basemap tiles/vector data, pedestrian/cycling graphs and offline address indexes.
- Allow a full Southern New England package and region-selective installation for users who prefer it; the owner may install all regions without size limits.
- Download or sideload data in advance, validate checksums/schema/source periods, install atomically, preserve previous working version for rollback and avoid overwriting private history/preferences.
- Never automatically delete installed regional packs solely to meet a storage target. Storage management and removal are explicit user decisions, subject to OS storage constraints.
- Avoid needless network calls and cloud dependencies; offline navigation must not require an account, server availability, map tile endpoint or live geocoder.

## Connectivity as optional enhancement

Internet may update official schedules, download map packs, or provide clearly labeled live vehicle positions, service alerts and other optional enhancements. When offline, show the last known *scheduled* information and its freshness, never represent it as current live status.

## Acceptance criteria

1. Airplane-mode cold start with a fully installed, validated regional pack; no mandatory network requests.
2. Offline map pan/zoom, route/stop discovery and timetable browsing in downloaded geography.
3. Offline origin/destination resolution (from downloaded address index or previously saved coordinates) and date-aware journey/transfer/return routing.
4. Offline local history, personalization, privacy controls and export.
5. Disconnect during a journey: essential functionality continues, with explicit live-data-unavailable state.
6. Partial/missing/expired pack: honest coverage and freshness warnings; no invented timetable.
7. Large regional packs are supported within device filesystem and available storage limits, without an arbitrary app-imposed cap.
8. Failed/corrupt update cannot destroy last verified pack or user-owned records.
9. No auto-pruning of offline coverage without user approval.
10. Real device tests document actual airplane-mode behavior and installed pack sizes, without setting a size-reduction target.

**Current state:** This is a specification, not evidence of implemented offline maps, routing or address search. Device testing is pending.
