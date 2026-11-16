# CT/MA regional coverage checkpoint — 2026-11-15

This is a source and test inventory, not a claim of complete transit coverage
or live operation. A `verified` outing means both legs exist in the loaded
published timetable; it does not confirm a seat, ticket, pickup, accessibility,
or a vehicle arriving as scheduled.

## Runnable schedule feeds

| Service | Evidence and tested state | Limits |
| --- | --- | --- |
| CTtransit and Hartford DASH | [CTtransit GTFS](https://www.cttransit.com/about/developers) is already configured. The tested archive contains route `DASH`, 48 trips, and its published stops. | [CTtransit describes regular DASH as weekday service](https://prod2.cttransit.com/services/hartford-dash-shuttle); event service varies. The app uses only dates in the feed. |
| Hartford Line and Shore Line East | The configured Hartford Line archive has 33 `HART` trips and 40 `SLE` trips; both entered the six-feed smoke database. | The archive types `SLE` as GTFS route type 3 (bus). This is publisher data and may reflect substitution; rail-mode completeness was not established. |
| Metro-North | [MTA developer resources](https://api.mta.info/) publish a current GTFS archive. Disposable import: 6 routes, 36,909 trips, 14,074 connections on 2026-11-15. | 16,233 scoped transfer rules were excluded by the current importer. Platform/transfer assurance is incomplete. |
| LIRR | The existing [MTA GTFS source](https://rrgtfsfeeds.s3.amazonaws.com/gtfslirr.zip) is now selected by default. Disposable import: 12 routes, 1,871 trips, 16,678 connections on 2026-11-15. | 344 scoped transfer rules were excluded. The Grand Central interchange in a sample journey is an estimated walk. |
| Greyhound | [FlixMobility's published GTFS](https://gtfs.gis.flix.tech/gtfs_generic_us.zip) includes Greyhound and FlixBus. This branch selects only Greyhound agency routes and normalizes its UTC timetable. Disposable import: 150 routes, 4,799 trips, 6,145 connections on 2026-11-15. | Ticket purchase and seat availability are not verified. The feed's service period and actual operation need regular checking. |
| SEAT (Southeast Area Transit District) | [SEAT's official GTFS page](https://www.southeastareatransitdistrict.com/gtfs-feed/) publishes the current archive (the Remix-hosted zip the FTA NTD weblink lists for SEAT). Full ten-feed import on 2026-11-15: 17 routes, 808 trips, 610 stops, zero import errors; feed service period 2026-06-29 – 2027-06-27. Norwich and Groton — stop-less in the 2026-11-15 CT cities sweep — now resolve and plan to/from Hartford in both directions (via New London + Amtrak). | Fixed-route scheduled service only; SEAT demand-response is not in the GTFS and is not represented. Long SEAT headways keep 60-minute return-feasible bubbles small (Norwich Transportation Center 219, Groton Square 9 on 2026-11-17). |
| GBT (Greater Bridgeport Transit) | [GBT's "For Transit Geeks" page](https://gogbt.com/for-transit-geeks/) is the agency's GTFS contact point; the current archive is published by GBT's GTFS vendor Trillium at the producer URL the Mobility Database registers for GBT (mdb-530). Disposable six-feed import on 2026-11-15: 16 routes, 1,753 trips, 1,183 stops, zero import errors; feed service period 2026-09-23 – 2026-12-27. Bridgeport Transportation Center resolves (parent station plus 15 berths) and plans to/from Hartford in both directions (via MNR Bridgeport → New Haven + Amtrak). | Fixed-route scheduled service only; GBT demand-response (GBT Connect) is not in the GTFS and is not represented. Shortest feed window of any configured feed (ends 2026-12-27) — poll for republication. Departures are carried on the terminal's berth stops, not the parent station record. |
| Norwalk Transit District (WHEELS) | The agency hosts its GTFS on its own InfoPoint portal (mystop.norwalktransit.com) — the URL the FTA NTD GTFS weblinks dataset lists for Norwalk Transit District (NTD 10057) and the direct-download URL the Mobility Database carries for this service (mdb-2242; the older agency-site GTFS_Data.zip URL in the deprecated mdb-529 record returns 403 and is not used). Disposable six-feed import on 2026-11-15: 9 routes, 943 trips, 253 stops, zero import errors; feed_info service period 2026-10-19 – 2027-05-31. Burnell Blvd Hub resolves and plans to/from Hartford in both directions (via South Norwalk MNR → New Haven + Amtrak). | Fixed-route scheduled service only; Norwalk demand-response is not in the GTFS and is not represented. All trip service is enumerated date-by-date in calendar_dates.txt (the calendar.txt base service is used by no trip) and regular service is enumerated only through 2026-12-31 — the declared 2027-05-31 end is three 2027 holiday dates — so poll for republication before year-end. Route 8 Coastal Link is the joint GBT/Norwalk service; each agency publishes its own trips for it. |
| HART (HARTransit) | HARTransit publishes its GTFS on its Passio platform at https://passio3.com/hart/passioTransit/gtfs/google_transit.zip — the URL the FTA NTD GTFS Weblinks dataset lists for Housatonic Area Regional Transit (NTD 10051) and Transitland's `static_current` for f-hartransit~ct~us; a separate feed from the shared UConn/WRTD Passio archive (passio3.com/uconn/...). Disposable seven-feed import on 2026-11-15: 16 routes, 624 trips, 125 stops, zero import errors; feed_info edition 2026-11-14 – 2026-12-15. Pulse Point in Danbury (hart:74163) resolves and plans to/from Hartford in both directions (via the MNR Danbury branch → New Haven + Amtrak/Hartford Line), and the Danbury–Norwalk 7 Link runs direct between Pulse Point and HART's Norwalk WHEELS Hub stop (hart:74703), a short walk from Norwalk Transit's Burnell Blvd Hub. | Fixed-route scheduled service only; HART demand-response is not in the GTFS and is not represented. The publisher times only its timepoints: 17,580 of the archive's 21,422 stop_times are untimed and are skipped by the importer — never interpolated — so only the 125 timed stops are carried and the 450 published stops that appear in no timed trip are absent. calendar.txt patterns span 2025-01-01 – 2027-12-31, far beyond the declared edition window: service past 2026-12-15 is the current pattern projected, not a publisher guarantee — poll weekly for the next edition. |
| River Valley Transit (Estuary Transit District) | The merged agency's GTFS is published by its vendor Trillium at the URL the Mobility Database registers for this service (mdb-551, marked official; the record still names legacy provider Middletown Area Transit) and Transitland carries as the Estuary Transit District feed `f-drke-ninetown~connecticut~us`. A second Trillium URL (`rivervalley-ct-us.zip`) serves byte-identical content (verified 2026-11-15 by per-file hash comparison) and is deliberately not configured — one feed only. Disposable seven-feed import on 2026-11-15: 16 routes with trips, 906 trips, 859 stops, zero import errors; calendar patterns span 2026-11-03 – 2027-11-30 (feed_info declares 2026-11-13 – 2027-11-04). Middletown's Downtown Terminal resolves (rivervalley:2750874) and plans to/from Hartford in both directions (via CTtransit at the Hartford end). | Fixed-route scheduled service only; RVT demand-response service is not in the GTFS and is not represented (a GTFS-Flex variant exists and is likewise not imported). The edition publishes no calendar_dates exceptions at all — holidays run the ordinary weekday pattern as published. The seasonal Clinton Trolley route publishes zero trips in this edition and is not carried; 117 published stops are referenced by no trip and are not carried. |
| Other configured local service | CTtransit, PVTA, WRTA, MBTA, Amtrak and Hartford Line were configured before this branch. | The six-feed smoke database here did not include PVTA, WRTA or MBTA; prior local data and tests do not prove all CT/MA districts are covered. |

The disposable six-feed database passed `scripts/check_data_integrity.py`.
A scheduled New Haven (`mnr:149`) → Jamaica (`lirr:102`) round trip for
2026-11-16, leaving no earlier than 08:00, allowing at least two hours at the
destination and home by 22:00, returned `verified`. It included MNR, an
estimated Grand Central walk, LIRR, and the reverse. The computed arrival at
Jamaica was 10:54, latest return departure 19:24, and arrival home 21:43:19.
This is test evidence for the downloaded archives, not a promise of operation
or a guaranteed station transfer.

## Unresolved services

- **Peter Pan:** imported under the owner's explicit doctrine exception of 2026-11-15, labelled unofficial/stale. The [MassDOT-listed GTFS download](https://www.mass.gov/lists/mbta-and-transit-data-for-developers) remains stale (its `feed_info.txt` ends on 2024-12-31) and Peter Pan publishes no timetable PDFs, so the Atlas imports the Peter Pan agencies (IBG agency_ids 40 and 71) from the third-party UTEL-UIUC Intercity Bus GTFS (2025; Peter Pan rows compiled from Transcor Data Services platform data) under the standard regional clip: 59 routes / 242 trips / 56 stops, including direct Hartford → Worcester service. The official feed replaces this source as soon as a current edition is published; see the exception record in `DECISIONS.md`.
- **Greater Hartford Transit District:** [GHTD Link](https://www.ghtdlink.com/) is an on-demand service in Enfield/East Windsor; its actual pickup depends on booking. [ADA paratransit](https://www.hartfordtransit.org/ada-paratransit-services/) has eligibility and reservation requirements. Neither can be represented as a fixed scheduled leg without a booking/availability integration.
- **CTtransit Flex:** The current CTtransit GTFS archive and [developer listing](https://www.cttransit.com/about/developers) did not identify a service by that name. Operator identity and authoritative schedule or booking source need confirmation.
- **Other CT/MA districts:** Greater Bridgeport Transit's GTFS is now imported (see the GBT row above): the archive its vendor Trillium publishes is registered in the Mobility Database (mdb-530) and passed the 2026-11-15 freshness gate. Norwalk Transit District's GTFS is likewise imported (see the Norwalk row above): the agency-hosted InfoPoint archive the FTA NTD weblink lists passed the same gate the same day. HART / HARTransit's GTFS is likewise imported (see the HART row above): the Passio-hosted archive the FTA NTD weblink lists for Housatonic Area Regional Transit passed the same gate the same day. River Valley Transit's GTFS is likewise imported (see the River Valley row above): the Trillium archive the Mobility Database registers for the merged Middletown Area Transit + 9 Town Transit agency (mdb-551) passed the same gate the same day; its duplicate Trillium URL is deliberately not configured. [Windham Region Transit District publishes fixed-route schedules and separately booked Dial-A-Ride](https://wrtd.org/), but no official GTFS download was verified in this session. No comprehensive source audit or successful import exists for every regional transit district. Prioritize official current GTFS where available, then source-backed reviewed schedules. Missing agencies remain `unknown`, never proof of no service.

## Reproduce locally

Use a fresh checkout or worktree so existing `data/` files remain untouched.
`python3 scripts/prepare_data.py` downloads the configured feeds and rebuilds
the ignored SQLite database. Then run:

```sh
python3 scripts/check_data_integrity.py --database data/atlas.sqlite
python3 -m unittest discover -s tests -q
python3 scripts/external_smoke.py
python3 scripts/external_smoke.py --regional --date 2026-11-16
python3 scripts/run_local.py
```

Open the printed loopback URL. The map's Connecticut buttons zoom to major
cities; choose a confirmed origin and use Outings to verify a selected stop.
The current LIRR/Metro-North/Greyhound test used a disposable six-feed import
because the active user database has the older schema. It was not activated.
The regional smoke passed against those downloaded archives on 2026-11-15;
the fixed date is an evidence checkpoint and will cease to be valid when
publisher service periods move forward. Select a newly covered date and
reverify the exact stops for a later run.
The desktop browser was unavailable for a visual click-through in this session;
HTTP smoke, JavaScript syntax, tests, and direct scheduled routing were run.
