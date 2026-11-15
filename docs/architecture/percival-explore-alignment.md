# Percival Explore and Transit Atlas alignment

Date 2026-11-14. Scope covers the requested comparison and a proposed integration
slice. Implementation acceptance remains pending.

## Inspected revisions and preservation

| Repository | Revision | Evidence inspected |
| --- | --- | --- |
| Transit Atlas Android worktree | `16ae740f916c0eae70d946431eba1cc2072c01b0` | Routing, API, importer, browser, Android planner and tests |
| Transit Atlas upstream main | `6545f58570625a83c7d3ca24cfe206f6e821135c` | Merged Reachability Explorer specification from PR #52 |
| Percival source-smoke PR #18 | `27b60260df48a433568585d67fc17d948139ffaa` | Core/boards, bounded planner, selected-feed catalogue, tests and smoke artifacts |
| Percival PDF-priority PR #19 | `658d25dd22df9f5a1fa2c4e0f459d4dd54c13740` | Published timetable precedence and recorded discrepancies |

The original Android worktree remains on its existing branch. This report and its
roadmap entry live in a separate documentation worktree based on upstream main.
The inspected Android and Percival changes have open draft PRs. Main's Reachability
Explorer change is a merged product specification.

Sources are [Atlas PR #52](https://github.com/softnessasastrength/transfer-issues/pull/52),
[Percival PR #18](https://github.com/softnessasastrength/zero-cloud-documentation/pull/18),
and [Percival PR #19](https://github.com/softnessasastrength/zero-cloud-documentation/pull/19).

## Target Explore behaviour

The user chooses a private origin profile labelled Bright Meadow or Jewish Home,
a travel date, earliest leave time, latest same-day home-return time and minimum
stay. Explore lists destinations with a valid outbound, sufficient dwell and a
valid return. Evidence gaps produce `Unknown` with reasons. The requested service
families are Hartford Line, CTtransit 905/905W and 80/82/83/84, PVTA G5/R10/R14,
and verified NYP/BOS connections.

Both projects already call for deterministic round-trip evaluation, explicit
constraints, source provenance, offline operation and uncertainty. Atlas's new
`docs/features/reachability-explorer.md` makes this a primary feature. Percival's
`design/percival/mobility-first-charter-v0.1.md` adds named operational states and
privacy requirements for origins and shared experiences.

## Overlap and implementation gaps

| Requirement | Existing Atlas paths and behaviour | Percival overlap | Integration gap |
| --- | --- | --- | --- |
| Transit graph and transfers | `routing.py` `scan`, `plan`, `latest`, `transfer_edges.py`, `street_routing.py` | `transit/percival_transit/planner.py` supports direct or one same-stop transfer per leg | Reuse Atlas's wider connection scan and transfer graph for Explore |
| Calendar and exceptions | `database.py` `active_services` and `connections`, `import_gtfs.py` | `core.py` validates calendar/exception and timezone data and compiles dated events | Align agency-local date/DST semantics and evidence gating |
| Dwell and complete return | `server.py` `/api/v1/plan` accepts `return=1` and `visit`, then calls `plan`/`latest` for return | `planner.py` `round_trip` takes explicit outbound/return windows | Apply coupled constraints to every discovered destination and expose one destination status |
| Discovery map | `server.py` `/api/v1/reachability` returns outbound arrivals, `web/app.js` `reach()` renders reachable stops with a two-hour UI window | Percival supplies source-backed stop/trip patterns | Return filtering, dwell controls and per-destination explanations remain implementation work |
| Origin profiles | Browser `web/app.js` `resolve()` accepts known stop labels/IDs | `bus_smoke.py` finds candidate stop names near requested labels | Confirm profile-to-stop/entrance mappings and permitted access paths using user-local settings |
| Station identity | Feed-prefixed stop IDs in Atlas SQLite | `planner.py` aliases and declared child-platform handling, rail smoke reports actual source IDs | Keep aliases tied to source snapshot and operator identities |
| Source versions | `import_gtfs.py` records hashes and periods in `sources.json`, replaces active data on refresh | `core.py` stores immutable raw snapshots and preserves original acquisition metadata | Reuse immutable snapshot invariants and attach source references to each normalized event/leg |
| PDF timetables and notices | M0.1 plans reviewed PDF ingestion, current normalized tables contain GTFS schedules | PR #19 specifies applicable PDF precedence and unresolved-conflict handling | Implement reviewed dated PDF events, effective periods, exception/substitution notes and conflict resolution |
| Operational state | `routing.py` returns `found`, coverage warnings are attached separately | `core.py`/`planner.py` expose `Scheduled`, `Unknown` and bounded `Infeasible` | Add a common status/reason/evidence contract before presentation |
| Android reuse | `OfflineRouter.kt`, `OfflineStreetGraph.kt`, `OfflinePlannerActivity.kt` already compute local one-way journeys | Percival preview is Python-based | Carry shared Explore fixtures/results into Kotlin after the Python contract stabilizes |

### Executed comparison of current API semantics

A synthetic two-stop fixture with one outbound connection was injected through the
existing API entry points. `/api/v1/reachability` included destination `b`.
`/api/v1/plan?return=1` returned outbound `found=true` and nested return `found=false`.
This demonstrates that the existing reachability result requires an additional
round-trip filter. The exercise used anonymous fictional stops and timetable rows.

Exact current source locations are `routing.py:31`, `routing.py:76`,
`routing.py:82`, `server.py:44`, `server.py:49`, `database.py:11`,
`database.py:20`, `web/app.js:147`, `web/app.js:156`, and `web/app.js:158` in
revision `16ae740`. The Android planner currently calls a single-direction search
in `android/app/src/main/java/org/southernnewengland/transitatlas/OfflinePlannerActivity.kt:81`.

## Source evidence and route-level findings

Downloaded JSON artifacts from the successful Percival source-smoke run for
`27b6026` were inspected. Raw transit archives were left in the originating workflow.
Artifacts record official URLs, acquisition times, checksums, coverage bounds,
selected routes, source stop names and sampled boards. The evidence belongs to
those snapshots and query windows.

| Service | Artifact evidence | Mapping or acceptance still required |
| --- | --- | --- |
| Hartford Line Hartford/Windsor Locks | Official archive hash `03e8bc27defd6b3a501c760592ad0ed196b5b88db0a5380ba855e55c999f9d0d`, source stops `6` and `8`, earlier smoke returned 17 and 12 departures with HTTP 200 for its November 13 window | Apply the travel-date PDF, notices, operator restrictions and onward-destination checks |
| CTtransit 80/82/83/84 | Snapshot `90abd4b2002498bec2d5af9614640ac743c5713b8c1b1004242a7bc167c68631`, actual short names include `80`, `82`, `82/84`, `83`, `84` | Preserve the composite `82/84` identity and evaluate each actual trip's day and pattern |
| CTtransit 905/905W | Same snapshot, route ID `16545` has short name `905`, with a `905W - Windsor Locks Express` trip pattern ending at source stop `13577` | Model 905W as a verified pattern within 905 in this snapshot, an exact route-short-name lookup for 905W would miss it |
| Bright Meadow | CT source candidates include `7919`, `12239`, `12240`, the 905 pattern serves Bright Meadow and a separate shortened 905W pattern ends at Windsor Locks | Confirm the intended facility/entrance and usable access direction for the origin profile |
| PVTA G5/R10/R14 | Official PVTA snapshot `c7defae022053b4e2211cf159d54704838f66556647d69021a1b47f280795357`, actual route IDs/short names `G5`, `R10`, `R14`, reported bounds November 2–December 19 | Import/validate the exact source version into Atlas and review applicable PDFs, exceptions and return legs |
| Jewish Home | G5 route long name mentions Jewish Home, candidate stop `1862` is labelled `Jewish House` | Confirm the requested origin-to-stop mapping and first/last-mile access |
| NYP/BOS | Atlas config lists an Amtrak feed and has a queued intercity scope | Verify publisher station IDs, operators, full selected trip sequences, restrictions and dated return service |

The sampled 24-hour boards beginning at 04:00 local on November 14 contain zero
905 departures at the Bright Meadow candidates and zero G5 departures at MassMutual
Enfield, while the Windsor Locks 905 board and Jewish House G5 board contain entries.
This is a source-window observation. It demonstrates why agency/route presence and
station-level service cannot establish an origin's usable trip pattern.

Atlas's historical PVTA HTTP-failure notes need versioned reconciliation with the
successful Percival snapshot. Atlas `config/feeds.json` contains source seeds and
`server.py`/`web/app.js` have fixed PVTA-missing text. A source-aware presentation
should derive coverage from the activated Atlas snapshot and verification state.
This comparison found no local Atlas transit database available for route acceptance.

The current importer clips stops to latitude 40.9–43.1 and longitude -73.8–-70.5
at `import_gtfs.py:46`, and limits MBTA to regional rail. NYP/BOS onboarding requires
an explicit coverage-policy check and preservation of relevant whole trip sequences.
Missing stops and out-of-area interchanges need explicit evidence before a destination
can be offered as a complete return-capable outing.

Evidence is retained in [Percival source smoke 43645696751](https://github.com/softnessasastrength/zero-cloud-documentation/actions/runs/43645696751)
and [earlier rail/HTTP smoke 43644898840](https://github.com/softnessasastrength/zero-cloud-documentation/actions/runs/43644898840).

## PDF priority and known conflicts

Atlas M0.1 currently states GTFS-first followed by official structured data and
reviewed PDF fallback. Percival PR #19 gives the applicable official PDF preference
for verified schedule entries, with date-specific exceptions/notices applied first.
Record the requested Explore preference explicitly in the policy contract and
roadmap before runtime integration.

PR #19 records a November 13 PDF southbound Windsor Locks departure at 05:59 that
is absent from the corresponding GTFS smoke board. It also records an 08:49
northbound Windsor Locks entry continuing towards Springfield while the GTFS
headsign says “Northbound to Hartford.” Atlas currently copies raw headsigns into
routing legs and presentation. These are acceptance cases for source resolution
and onward-destination presentation. Applicable-period selection must exercise the
separate November 16 timetable boundary and published bus-substitution notes.

PR #19's PDF cross-check was read as recorded evidence. Full PDF interpretation,
all-route parity and current-date operator/exception applicability remain unverified
in this comparison. Both current runtimes continue to read GTFS schedules.

Percival's seven-day snapshot cutoff is an application policy. Atlas's offline
contract needs an explicit shared freshness decision based on source effective
periods, known exceptions and acquisition age. A universally copied cutoff could
prevent useful offline planning while published schedules remain applicable.

## Narrow proposed integration sequence

1. **One Explore evidence contract and regression set.** Define private origin
   aliases, date, leave-after, same-day home-by and minimum dwell inputs. Define
   `Scheduled`, `Unknown`, bounded `Infeasible` and solver-budget reporting with
   evidence references and rejection reasons. Add anonymous fixtures for outbound
   success with failed return, insufficient dwell, missing sources, ambiguous origin,
   exception-only service, midnight and PDF/GTFS conflicts. Freeze sample source
   versions as metadata and use synthetic normalized events in committed tests.
2. **One Python Explore orchestrator.** Reuse `routing.scan` once for outbound
   candidates and `plan`/`latest` for each candidate's allowed return window.
   Require both directions and dwell to satisfy the same travel-date boundaries.
   Couple latest outbound arrival to return departure minus dwell. Establish
   bounded candidate evaluation and measure runtime before optimizing reverse
   search. Expose an additive versioned endpoint after documenting compatibility
   with the existing `/api/v1/plan` and `/api/v1/reachability` contracts.
3. **Verified source adapter and scoped activation.** Reuse Percival snapshot,
   date/timezone and station-identity invariants. Extend Atlas normalization with
   source document/page/period, reviewed event and conflict references. Select
   applicable PDF and exception evidence for each leg. Keep unresolved required
   evidence `Unknown`. Start with Hartford/Windsor Locks and the requested CT/PVTA
   service patterns, then admit NYP/BOS when their evidence and trip coverage pass.
4. **Thin Explore presentation.** Reuse `web/app.js` map markers, itinerary cards,
   stop selection, source cards and local personal settings. Show destination,
   arrival, usable dwell, return options and reasons. Wire private origin profiles
   only after mapping confirmation. Carry the same fixtures and result contract to
   Kotlin. Graph-derived geographic surfaces follow the approved M0.RE sequence.

The first implementation PR should contain step 1 and a small deterministic step-2
service exercised by fixtures. Source-backed feasibility claims remain gated on
step 3. The existing Atlas CSA and Percival source compiler are the principal reuse
points. Avoid maintaining two independent planners with divergent operational states.

## Acceptance and open decisions

The slice succeeds when every displayed feasible destination has a checked same-day
outbound/return pair, minimum dwell, dated evidence and source-backed origin mapping.
Incomplete required evidence yields an explained `Unknown`. A complete bounded
search with adequate evidence may yield `Infeasible`. Verified route selection must
cover the 905W pattern and composite 82/84 label correctly. User-local origins and
source/profile sharing follow the existing privacy requirements.

Before connecting the runtimes, resolve the scope of PDF precedence and the shared
freshness policy. The proposed Explore policy prefers applicable reviewed PDFs and
exceptions, retains GTFS identities and indexing, and uses publisher applicability
plus explicit uncertainty for offline source validity. Acquisition timestamps remain
visible. These policy choices need a documented product decision during contract
review.

This report contains source inspection, hosted artifact inspection and one executed
synthetic Atlas API exercise. Production coverage, full return journeys from the
requested facilities, PDF ingestion and cross-client implementation remain open.
