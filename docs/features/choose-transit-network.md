# Choose Your Transit Network — onboarding and offline package management

**Status:** product/architecture specification only; not implemented. **Decision:** 2026-11-12.

## User-approved initial selection

Onboarding selection example (not a claim that data is already installed):
- CTtransit
- CTrail Hartford Line
- PVTA
- Amtrak

**Update policy: automatic updates for already selected and installed networks.** This is not permission to install new agencies, expand geographical coverage, activate tracking, or silently download unrelated data.

## First-run experience

1. Welcome: explain that essential features run offline and that user controls which agency datasets occupy device storage.
2. **Choose Your Transit Network:** searchable agency picker grouped by region and mode. Offer CTtransit, CTrail Hartford Line, PVTA and Amtrak as this owner's selected initial agencies; no globally imposed default selection for other users. User may select none and browse a clearly labeled limited shell.
3. **Review downloads:** resolve a manifest dependency graph and display each selected agency's package, required shared basemap, offline routing graph, stop/transfer connections, address/POI index and source data. Show *actual manifest-based* estimated bytes, version, geographic extent, provenance, schedule effective date, and whether dependencies include adjacent territory. Never fabricate package sizes or completeness.
4. **Consent and install:** require explicit confirmation before the initial download, including shared dependencies. Make dependencies visible and allow user to deselect an agency or defer installation. If a requested agency cannot be supported by available authoritative data, say so instead of downloading a fake placeholder.
5. **Verify and activate:** download to staging, verify SHA-256, schema, package IDs, integrity and compatibility, then atomically switch active package set; preserve prior valid versions for rollback as storage permits.
6. **Offline-ready:** confirm installed coverage and last updated date; test essential map, route, timetable, transfer and address search locally. No account, cloud session or server ping is required to launch.

## Data-pack design

- Small Android app shell with local routing/search engine; no arbitrary app-imposed offline data-size cap. Allow multi-GB packages, bounded by device filesystem and actual free space.
- Versioned manifests with `package_id`, `agency_ids`, geographic bounds, dependencies, version/schema, source URL/provenance, source effective period, compressed/unpacked size, SHA-256 and licensing/attribution. Require trusted manifest distribution and reject tampered packages.
- Dependency resolver computes **minimal necessary closure** of selected agency packs plus shared maps, foot/cycle routing graph, transfer nodes, geocoding index and geographic buffers essential to make those selected services usable. Shared packs installed once with reference counts; show why each is required.
- Adjacent geography and cross-border transfers must be explained. Do not add an unselected agency's full dataset merely because of a nearby transfer; explicit additional agency install requires approval.
- Separate network coverage from package availability: official PVTA feed availability has been unverified in earlier work. Do not mark it installed or usable until validated source data is packaged.
- Relevant Amtrak services may require geographically broader segments and connections. Disclose their pack extents; do not silently install all national Amtrak coverage.
- Offline map rendering must use installed licensed local tiles/vector data, not a remote tile server. Offline pedestrian/cycling graph and local address lookup must not fall back silently to online APIs.
- Support manual import/sideload and full regional pack installation for advanced users, with the same manifest integrity and consent rules.

## Update policy: auto (selected networks only)

- Once a user opts into automatic updates, check for updates when connectivity is available and use safe network/battery constraints; do not require connectivity to operate. Expose a setting for Wi-Fi-only versus metered connections and allow pausing updates.
- Automatically update **only already installed user-selected agency packages and their previously disclosed shared dependencies**, within the approved geographic scope. If a new dependency or material footprint expansion is introduced, request explicit approval before download. A new agency is *never* auto-installed.
- Preserve prior validated data until a new complete package passes checks and activation. Handle interrupted downloads, checksum failures, version incompatibility, out-of-space errors and rollback without corrupting local data or user records.
- Updates must not delete historical journeys, saved destinations, mobility profiles or manually imported records. Separate user databases from replaceable official feed packs.
- User may switch to Ask or Manual updates at any time; disable auto-updates without losing existing data.
- Display schedule freshness and coverage warnings while offline. Never label old scheduled departures as live arrivals.

## Ongoing management

A **Manage Offline Networks** screen shows installed agencies, shared dependencies, package size, last verified update, source, schedule validity and coverage map. User can explicitly add agencies, remove agencies (with dependency impact preview), retry failed packages, repair/verify, export package manifest, and choose full-region packs. No automatic eviction, pruning or unrequested agency download.

Removing an agency must not delete personal journey history or other user-owned records; historical map segments may remain from user-owned geometry or be shown with an honest missing-map indicator.

## Acceptance tests

1. Initial onboarding selection CTtransit + CTrail Hartford Line + PVTA + Amtrak produces a reviewable dependency plan and does not download before explicit confirmation.
2. Selecting no agencies never initiates a download.
3. Package size and geographic scope come from validated manifests, not fabricated constants.
4. Shared map/graph/index dependencies appear once, with explanations and clear user consent.
5. A transfer near a state border does not silently install a neighboring unselected agency.
6. Auto-update refreshes only selected/installed networks and previously authorized dependencies; newly introduced dependencies require approval.
7. No new agency download occurs unless the user selects and confirms it.
8. Airplane-mode cold start, map, timetable, route search, transfers and saved history work using complete installed packs; test blocked features explicitly when a pack lacks necessary data.
9. Interrupted, tampered or checksum-failing download leaves previous validated pack usable.
10. Atomic update preserves user data and rolls back on incompatible schema or disk exhaustion.
11. Removal shows dependency impact, does not delete user history and does not automatically remove shared dependencies still needed by other agencies.
12. Update policy can change from Auto to Ask/Manual without loss of installed datasets.
13. PVTA unavailable/invalid feed is shown as unavailable, not falsely installed.
14. Offline freshness and scheduled-versus-live labeling are accurate.
15. Android device test on metered/Wi-Fi, storage pressure, interrupted download, process restart and airplane mode; record actual outcomes, not assumed results.

## Relationship to existing decisions

Follow `docs/architecture/offline-storage-policy.md`, `docs/features/privacy-first-journey-verification.md`, and root `AGENTS.md`. Offline completeness outranks size minimization. Package selection and auto-updates are distinct from GPS, sensor, history and analytics permissions. This PR creates **documentation only**, not an Android installer or verified offline packages.
