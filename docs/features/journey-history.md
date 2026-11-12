# My Transit History — journey map and personal network coverage

**Status:** proposed, not implemented. Requested 2026-11-12. This is a product concept and acceptance specification, not a claim that trips are being recorded.

## Product goal

Offer a dedicated **My Transit History** screen showing a color-coded, interactive map of journeys actually taken. This is a private personal atlas, not just a chronological trip list. The map supports exploration, reflection and rediscovery alongside the existing Explore and Travel modes.

## Experience

- Open **History** from primary navigation. Show a regional map with journeys overlaid on licensed basemap/offline network data.
- Filter by date range (day/month/year/all), agency, transit mode (bus/rail/walk/bike/scooter), route and confirmed-vs-manual provenance.
- Tap a journey to inspect date, origin/destination, stops, legs, transfers, mode, route/agency, source of geometry and notes.
- Color-code route/agency/mode or journey identity via a switchable legend. Preserve contrast and distinguish overlaps with line patterns/labels, not color alone.
- **My Network** overlay: highlight confirmed ridden routes and stops against not-yet-ridden lines. Do not mark an entire route ridden merely because one segment was traveled; distinguish full-route and segment-level coverage.
- Optional **journey replay** moves through recorded legs in order; no fabricated GPS trace or exact timestamps.
- Statistics: completed journeys, distinct routes/agencies, stops/towns visited, approximate distance where data quality permits. Show unknowns and avoid double-counting transfers.
- Import/manual entry of older trips with explicit “recalled/manual” provenance and optional approximate dates.
- Offline-first: map, records, filtering and export must work in airplane mode once licensed offline maps are packaged.

## Data model and source honesty

Separate `PlannedJourney` from `CompletedJourney`. A route search, saved itinerary or app-open event must **never** create a completed journey. User confirmation is required in the MVP. Optional future automatic detection requires a separate opt-in and uncertainty review.

Proposed local entities:
- `journey`: UUID, date/time (including timezone and uncertainty), completion status, entry method (confirmed/manual/optional recorded), notes, timestamps.
- `journey_leg`: ordered leg, mode, agency/route/trip IDs when known, stop IDs, times and source metadata.
- `journey_geometry`: optional geometry with source type (verified GTFS shape, matched offline network path, user GPS trace with explicit consent, approximate sketch); accuracy and availability flags.
- `journey_events`: user edits and corrections, optional lightweight audit for export/recovery.

Never present a published GTFS shape as proof of the exact path the user traveled. For incomplete geometry, show a dotted/approximate representation or omit the segment. Transit shapes can change with feed versions: retain the geometry provenance/version needed to render historical journeys without rewriting history from today's feed.

## Privacy and control

- Off by default for passive trip tracking. User-confirmed history entry is available without background tracking.
- Local-only storage by default; no cloud account or analytics required. No automatic uploads or sharing.
- Separate opt-ins for GPS recording, activity recognition, background location and future automatic trip detection. None is necessary for the initial manual/confirmed history.
- Offer pause/disable, delete single trip, clear history with confirmation, import/export JSON, and backup/restore without duplicating IDs.
- Minimize precise location retention; prefer transit-leg metadata and published geometry when sufficient. If recording GPS traces is later authorized, make retention and deletion explicit.
- History may expose sensitive home/work routines; do not leak to logs, crash reports, screenshots or shared links.

## MVP implementation order

1. Local SQLite schema/migrations and portable export format with synthetic tests.
2. Confirm completed itinerary or add manual trip; clear distinction from planned routes.
3. History list and details with edit/delete.
4. Color-coded map overlays with legend and filtering, offline-map fallback.
5. Ridden segment coverage and conservative statistics.
6. Optional replay and user-controlled richer recording only after privacy/device validation.

## Acceptance tests

1. Planning a trip does not create a completed journey; confirming it creates exactly one record.
2. Manual entry with partial date, unknown agency or missing geometry remains valid and honestly labeled.
3. Map renders overlapping trips with accessible labels/legend and stable color assignment.
4. Filtering by date, agency, mode and route returns expected synthetic journeys.
5. One ridden stop-to-stop segment does not mark an entire line as ridden.
6. Repeated use of a route counts multiple journeys but one distinct route; statistics handle unknown distances.
7. GTFS feed update does not silently rewrite stored historical geometry or identifiers.
8. Airplane-mode viewing, editing, filtering and export work without network calls once offline map assets exist.
9. Delete/clear and backup/import work without loss, duplication or unintended data disclosure.
10. Location and activity permissions denied: manual history and confirmed itineraries remain fully usable.
11. Optional recorded traces are never created without explicit consent; app lifecycle stops recording when authorization ends.
12. Actual Android/iOS device and accessibility tests must be recorded as run or not run; this proposal has no device validation.

## Dependencies and scope

Requires the offline atlas map and route/stop data, a stable journey/leg contract and local persistence. Reuse the existing browser journal where practical but **do not silently migrate or overwrite** existing notes. No automatic recording, cloud sync or production UI is implemented by this proposal.
