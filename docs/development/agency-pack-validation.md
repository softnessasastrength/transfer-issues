# Relational validation of exported agency packs

## Purpose and commands

The Termux/Crostini catalogue verifier now rejects structurally unusable normalized
GTFS databases even when their byte count and SHA-256 match the catalogue. Validation
is read-only, standard-library-only and entirely local. It does not download,
install, update, repair or prune data.

```bash
python3 scripts/verify_lan_catalog.py --packs build/lan-packs
python3 -m developer_center --inspect packs --packs build/lan-packs
bash crostini-dev.sh command-center --packs build/lan-packs
```

Press P for the Command Center pack panel, up/down to scroll and D to return to the
operations dashboard. Enter never downloads or activates packs from this panel.
The catalogue directory defaults to `build/lan-packs`; `--packs` selects an existing
alternative directory. It does not change the default output of pack builders.

Direct verification exits 0 on success, 1 with an actionable message on malformed,
unreadable or invalid input. Headless inspection returns structured JSON and exits
0 only for `validated`; `invalid`/`unavailable` exit 1. The terminal remains open to
show failures. An empty export catalogue can be valid and still contain no usable
networks. Validation never establishes that a network is installed on Android.

## Validation boundary

`verify_lan_catalog.py` checks catalogue structure, recognised agency keys, duplicate
missing-agency declarations, safe filenames, positive integer byte/route counts and
lowercase SHA-256. Optional existing `id`, `agency` and `kind` fields must match the
catalogue key when provided; this retains compatibility with older local manifests
without inventing missing publisher identity. Package symlinks are refused. Paths
are encoded as SQLite file URIs, including directories containing ? or #.

The database is opened read-only, with query-only mode and untrusted-schema handling,
and explicitly closed on success or failure. SQLite integrity is checked first.
`pack_validation.py` then checks the current normalized format:

- All eight required objects are real tables: stops, routes, trips, times, calendar,
  exceptions, shapes and transfers. Required columns must exist; extra columns and
  tables remain permitted. Views cannot stand in for required data tables.
- Required logical keys are nonempty and unique, including trip/sequence pairs,
  exception service/date pairs and transfer endpoint pairs.
- Route and stop feed fields must match the package agency, including rejection of
  NULL feed fields. Route counts must agree with the catalogue.
- Every trip route exists; each stop time has a trip and stop; each trip has a
  calendar or exception service definition and at least one stop-time record;
  transfer endpoints must exist. NOT EXISTS checks reject NULL references too.
- Stop-time sequences and arrival/departure seconds are nonnegative integers;
  departure cannot precede arrival; later arrivals cannot precede earlier departure.
  Pickup/dropoff codes and transfer types are within supported normalized values.
  Transfer seconds are nonnegative integers.
- Calendar dates are real YYYYMMDD values, ranges are ordered, weekday masks contain
  seven binary digits, and exception dates/types are valid.

These rules describe the repository's normalized SQLite format, not every optional
GTFS feature or a full GTFS specification certification. Historical and expired
but structurally valid dates remain valid here; service applicability needs separate
source/freshness gates. Exception-only calendars, >24-hour times, empty optional
shape tables and noncontiguous stop sequences are preserved. No geometry, stop,
service or transfer is synthesized to make validation pass.

Output keeps `verified` and `missing`, adds per-table counts under each verified
agency, and adds `unreported` for recognised agency keys absent from both catalogue
lists. Missing/unreported means missing information about an export, never absence
of actual passenger service. Recognised agency keys are the existing four POC
choices, not a claim of complete Connecticut or regional operator coverage.

## Existing integration and failure behaviour

`termux-atlas.sh serve` and `crostini-dev.sh packs` already call this verifier; they
now receive the stronger checks automatically. Termux refuses server startup when
verification fails. Fix/re-export data deliberately; do not edit checksums or invent
records merely to bypass a failure. The verifier never rewrites the source database,
export catalogue, agency payload or installed app state. The existing exporter can
replace its own catalogue before verification; this work does not make export-set
activation transactional or change Android's installer lifecycle.

Command Center inspection invokes exactly the same verifier. This is an exported
local-catalogue panel, not the Android application's installed-network inventory.
It clearly reports the lack of publisher authenticity, freshness, basemap or
complete-offline certification. Validation can scan large tables and run SQLite
integrity checks; it runs on explicit inspection/refresh, with no size cap or
background task. Regional-scale performance remains unmeasured. Avoid inspecting
an export while another process replaces its files: checksums and SQL checks are
not a cryptographically locked snapshot of concurrent writers.

## Acceptance evidence and limitations

Synthetic tests exercise missing tables/columns, view substitution, empty/duplicate
keys, NULL and dangling references, invalid chronology/calendars/transfers, malformed
catalogue entries, checksum tamper, mixed agency data, symlinks, URI escaping and
CLI failure diagnostics. A positive exception-only overnight/gapped trip is checked
byte-for-byte after verification. Exporter integration verifies a newly generated
synthetic pack. Command Center reports distinguish unavailable/invalid/validated.

Commands executed:

```bash
python3 -m unittest discover -s tests -p test_termux_pack_validation.py -v
python3 -m unittest discover -s tests -p test_lan_packs.py -v
python3 -m developer_center --run test
```

Observed: 14 focused validator tests passed, exporter integration passed, and the
full Python suite passed 100 tests. Direct CLI and headless inspection validated a
synthetic pack in /tmp; terminal P/Q smoke was exercised. No current real agency
feed was downloaded or certified. No physical Android/Termux, emulator or airplane-
mode execution is claimed. Android's separate installer and unified assembler do
not yet invoke this helper; parity and interrupted-activation recovery remain next
steps. Parent-station references, shape-reference completeness, coordinate validity,
source effective periods and publisher authentication require further validation.
