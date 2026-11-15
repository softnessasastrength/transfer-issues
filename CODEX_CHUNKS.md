# Transit Atlas — Luna-sized Codex chunks (scoped items 1, 3, 4, 5)

These chunks decompose the scoped big items in `CODEX_HANDOFF.md` — item 1
(M0.1 PDF fallback ingestion), item 3 (Metro-inspired map UI build-out),
item 4 (API v1 contract completion), and item 5 (M0.R rail / New Hampshire
expansion) — into pieces a mid-tier coding model can complete in one
sitting without frontier-level design judgment. They are work orders, not
new architecture and not permission to widen scope.

Item 2 (plan/bubble latency) is **not** in this file: it is already
pre-cut as chunks L2.1–L2.4 in `CODEX_HANDOFF.md`. Work those first, per
the cook list.

**ROADMAP discipline:** M0.1 is authorized. M1 (Apache/macOS), M2 (PWA),
and M3 (native iOS) are DEFERRED and require explicit owner authorization
— nothing in this file touches them, and no chunk may be read as
authorization for them. Never fabricate transit service: no invented
stops, times, geometry, fares, or seat availability, in code, fixtures,
or docs.

## How to consume a chunk

1. Take the earliest chunk whose dependencies are complete. Do not
   combine chunks merely because they touch the same file.
2. Read the chunk card, the linked current code, `AGENTS.md`,
   `ROADMAP.md`, and the relevant entries in `DECISIONS.md` before
   editing.
3. Keep the implementation inside the listed files. The codebase is
   Python standard library + SQLite; do not add third-party
   dependencies.
4. A chunk is **done** only when all of the following are true:
   - its acceptance test passes;
   - the full suite passes: `python3 -m unittest discover -s tests`;
   - for chunks touching `web/`, `node --check web/app.js` passes and
     the browser smoke (`tests/browser_smoke.cjs`) still passes where
     the environment can run it;
   - a dated `DECISIONS.md` entry records the chunk ID, material design
     choices, tests run, environment, and any residual limit.
5. Fixtures use small synthetic feeds/documents built by the tests.
   Tests must not require network access or a real agency download
   unless the chunk explicitly says so.

## Stop-and-report rule

Stop the chunk and report the blocker instead of improvising if:

- the acceptance test cannot be made concrete without changing an
  earlier chunk's contract;
- the work needs a file or subsystem outside the card's bounds;
- it needs a new dependency, a credential, a paid service, a
  deployment, or a live external side effect;
- it would require inventing a stop, time, fare, or geometry value to
  make a test pass;
- it drifts into deferred M1/M2/M3 territory;
- an existing test fails for an unrelated reason; or
- the card's factual premise no longer matches the code.

The report should name the chunk, the exact failed premise, the
evidence, and the smallest decision needed from Ember or the owner. A
stopped chunk is useful information, not a failed sitting.

## Consumption order

A-01 → A-02 → A-03 → A-04 → A-05; A-06 after A-02; A-07 after A-01;
A-08 after A-07; A-09 and A-10 independent; A-11 → A-12; A-13 after
A-11; A-14 → A-15; A-16 after A-14; A-17 independent. Independent
branches may be taken in ID order when their listed dependencies are
met. Ordering note: item 4's chunks (A-07–A-10) precede item 3's
(A-11–A-13) because the handoff states the contract statuses originate
in ingestion (item 1) and the map UI renders them; item 5 (A-14–A-17)
comes last because the handoff queues M0.R behind stabilized ingestion
and routing.

---

## Item 1 — M0.1 PDF fallback ingestion (resilience for no-GTFS agencies)

Framing, per the 2026-11-14 status change in `CODEX_HANDOFF.md`: PVTA
is no longer the motivating case — its GTFS imports since the
User-Agent fix. This build is resilience work (a feed endpoint or UA
filter could cut an agency off again) and the route for agencies that
genuinely publish no GTFS. ROADMAP M0.1 acceptance items 2, 3, 6, 7 are
the target.

### A-01 — Source registry: PDF/no-GTFS source entries

**Objective:** Extend the source registry so an agency or document
without usable GTFS can be registered with full provenance: publisher,
official document URL, retrieval date, effective/service period,
source type (`gtfs`, `structured`, `pdf`, `html`), and review status
from a fixed vocabulary (`unreviewed`, `reviewed`, `ambiguous`,
`expired`, `historical`). GTFS entries in `config/feeds.json` keep
working unchanged; PDF-source entries live in the same registry shape
so `database.sources()` consumers see one list.

**Files:** `config/feeds.json`; `database.py` (registry read path
only); `tests/test_source_registry.py` (new).

**Acceptance:** A validation test loads the registry and asserts every
entry — GTFS and PDF — carries publisher, URL, retrieval date, source
type, and a review status from the fixed vocabulary; an entry missing
a field or using an off-vocabulary status fails the test. Existing
suite green, including the current `meta`/`coverage` tests. Run the
targeted test file, then the full suite.

**Depends on:** None.

### A-02 — Normalized PDF schedule tables in SQLite

**Objective:** Add the storage layer for reviewed PDF schedules,
coexisting with the GTFS tables without modifying them: tables for
PDF-sourced routes, directions, timepoints (ordered stop times), and
calendars, every row carrying source ID, document page, confidence,
and review status. Raw extracted text is stored separately from
normalized records (ROADMAP raw/normalized separation). Schema is
created by a new `pdf_ingest.py` module; the GTFS importer is not
touched.

**Files:** `pdf_ingest.py` (new); `tests/test_pdf_ingest.py` (new).

**Acceptance:** Against a temporary database, create the schema,
insert one synthetic route with two directions, ordered timepoints,
and a calendar; read back and assert exact round-trip including
provenance fields. Assert the GTFS tables' schemas are byte-identical
before and after (compare `sqlite_master` SQL for the eight existing
tables). Run the targeted test file, then the full suite.

**Depends on:** A-01.

### A-03 — PDF text extraction with explicit OCR provenance

**Objective:** Add the extraction step: given a PDF file, produce its
embedded text layer using only the standard library (FlateDecode
stream decoding via `zlib`), and record an extraction-provenance
record per document: method (`embedded-text`, `ocr`, `manual`, or
`none`), tool/version note, and retrieval date. A PDF with no usable
text layer yields method `none` and **zero** extracted records — the
pipeline never guesses at scanned content it cannot read. OCR itself
is out of scope; an OCR-produced text file may be registered later as
method `ocr` with its tool named.

**Files:** `pdf_ingest.py`; `tests/test_pdf_ingest.py`.

**Acceptance:** The test builds a minimal fixture PDF with a text
layer in-test and asserts the extracted text matches and the
provenance record says `embedded-text`. A second fixture with no text
layer asserts method `none` and no extracted rows. Run the targeted
test file, then the full suite.

**Depends on:** A-02.

### A-04 — Review and confidence gate for PDF records

**Objective:** Implement the single gate that decides which PDF
records routing-facing queries may see: only records with review
status `reviewed`, confidence at or above the documented threshold,
and a service period covering the queried date are visible. All other
records remain stored and inspectable but invisible to routing. The
gate is one helper in `pdf_ingest.py`; no endpoint or routing code
bypasses it.

**Files:** `pdf_ingest.py`; `tests/test_pdf_ingest.py`.

**Acceptance:** Fixture records in each status (`unreviewed`,
`reviewed`, `ambiguous`, `expired`, plus a reviewed record outside
its service period and one below the confidence threshold) — the
gate's query returns exactly the one eligible record. Assert there is
no second code path in `pdf_ingest.py` that returns normalized
records without the gate. Run the targeted test file, then the full
suite.

**Depends on:** A-02.

### A-05 — GTFS + PDF coexistence fixture

**Objective:** Prove ROADMAP M0.1 acceptance 3 end to end at fixture
scale: one SQLite database holding a small GTFS fixture feed and one
PDF-only fixture agency (reviewed records through A-04's gate), with
the departures path returning both and each result labelled by source
type so a consumer can distinguish GTFS-derived from PDF-derived
times.

**Files:** `database.py`; `server.py` (departures response labelling
only); `tests/test_pdf_ingest.py`; `tests/test_http.py`.

**Acceptance:** The fixture test asserts departures for a GTFS stop
and a PDF-agency stop in the same database, each carrying the correct
source-type label; flipping the PDF record's status to `unreviewed`
makes its departures disappear while the GTFS results are unchanged.
Run the targeted test files, then the full suite.

**Depends on:** A-04.

### A-06 — PDF record validation checks

**Objective:** Add validation for normalized PDF records, mirroring
the GTFS validation-report pattern: chronology (times increase along
a trip), stop ordering, duplicate timepoints, and calendar conflicts
are checked and written to a validation report; a record failing a
check is marked `ambiguous` with the failed check named — never
silently corrected.

**Files:** `pdf_ingest.py`; `tests/test_pdf_ingest.py`.

**Acceptance:** One fixture per failure class (non-increasing times,
duplicated timepoint, overlapping conflicting calendars) produces the
expected report entry and the `ambiguous` status; a clean fixture
produces an empty report and stays `reviewed`. Run the targeted test
file, then the full suite.

**Depends on:** A-02.

---

## Item 4 — API v1 contract completion

Target: the "Known contract gaps" list in `API.md` — unified PDF
confidence/validation statuses, per-trip provenance/expiry gates,
pagination, and full parameter validation. Coordinate with item 1:
the status vocabulary is A-01's.

### A-07 — Unified status vocabulary in API responses

**Objective:** Make `meta` and `coverage` responses expose each
source's type, review status, and validation state using exactly
A-01's vocabulary, for GTFS and PDF sources alike. Update `API.md`'s
endpoint table to document the new fields. No existing field is
removed or renamed.

**Files:** `server.py`; `database.py`; `API.md`;
`tests/test_http.py`.

**Acceptance:** HTTP fixture tests assert a GTFS source and a
PDF source both report `source_type`, `review_status`, and
`validation` fields with in-vocabulary values; existing response
fields are unchanged (the pre-existing HTTP tests pass unmodified).
Run the targeted test file, then the full suite.

**Depends on:** A-01.

### A-08 — Per-trip provenance and expiry gate

**Objective:** Add provenance to `trip` and `route` responses: feed,
source type, source service period, and review status for the
records behind the response. A trip whose source period does not
cover the requested date is reported with an explicit
`provenance_status: "outside_verified_period"` marker instead of
being silently presented as verified — the response shape stays the
same, the honesty becomes machine-readable.

**Files:** `server.py`; `database.py`; `API.md`;
`tests/test_http.py`.

**Acceptance:** Fixture tests assert provenance fields on an
in-period trip, and the explicit marker on an out-of-period trip;
in-period responses are otherwise byte-identical to current
behaviour. Run the targeted test file, then the full suite.

**Depends on:** A-07.

### A-09 — Pagination for meta and reachability-class responses

**Objective:** Add opt-in pagination to the list-bearing responses
(`meta` routes/stops lists and `reachability` results): `limit` and
`offset` parameters, validated like the existing `stops` endpoint's,
with `total` and `next_offset` fields present when pagination is
requested. When the parameters are absent, responses are exactly as
today, so the current UI and clients do not change behaviour.

**Files:** `server.py`; `API.md`; `tests/test_http.py`.

**Acceptance:** Fixture tests page through a list in two requests
and reassemble exactly the unpaginated list; `total` matches;
out-of-range `limit`/`offset` produce the standard 400 error shape.
Run the targeted test file, then the full suite.

**Depends on:** None.

### A-10 — Full parameter validation across endpoints

**Objective:** Close the "full parameter validation" gap: every
`/api/v1/` endpoint validates its documented parameters (presence,
format, and the ranges already stated in `API.md` — e.g. `time`
0..86399, `deadline` between `time` and 172799, `radius` 0..3000,
`buffer` 0..3600, `visit` 0..86400) and returns the standard
`{"error": "message"}` body with HTTP 400 for invalid input, instead
of the current mix of defaults and 500s.

**Files:** `server.py`; `API.md`; `tests/test_http.py`.

**Acceptance:** A table-driven test covers, per endpoint, at least
one missing-required, one malformed, and one out-of-range parameter,
each asserting HTTP 400 and the standard error shape; all valid
requests in the existing tests return unchanged responses. Run the
targeted test file, then the full suite.

**Depends on:** None.

---

## Item 3 — Metro-inspired map UI: mechanical substrate

Only the mechanical substrate is chunked here: data binding,
rendering of API-supplied classifications, aggregation, and control
wiring in the existing web UI. The visual and interaction *design* —
how the Metro-inspired interface should look and feel — is design
judgment and is listed under NOT CHUNKED. Hard rules for every chunk
in this section: render only published stop coordinates from API
responses; `unknown` is rendered visibly distinct from `unreachable`
and never with language or styling that reads as "no service";
missing data is not evidence of no service.

### A-11 — Bubble results as a geographic layer

**Objective:** Render a `/api/v1/bubble` response as a geographic
layer in the existing map UI: one marker per evaluated stop at its
published coordinates, classified `reachable`, `unreachable`, or
`unknown` directly from the response fields, with three visually
distinct marker treatments defined in `web/style.css`. The layer
replaces (not accumulates) on each new query.

**Files:** `web/app.js`; `web/style.css`; `web/index.html`;
`tests/browser_smoke.cjs`.

**Acceptance:** Extend the browser smoke with a stubbed bubble
response containing known counts per class; assert the rendered
layer contains exactly those counts, that `unknown` markers carry
the distinct unknown treatment, and that a second query replaces
the layer. Existing smoke assertions still pass. Run the full Python
suite and the browser smoke.

**Depends on:** None. (Consumes A-07's status fields when present,
but must work against the current bubble response.)

### A-12 — City-level summary panel

**Objective:** Aggregate the current bubble/plan results per
priority city (the `cities` list already served by `meta`) into a
summary panel: per city, counts of reachable / unreachable /
unknown stops from the most recent bubble response, rendered as a
plain list beside the map. Aggregation is computed from response
data only — no new endpoints, no inferred service.

**Files:** `web/app.js`; `web/style.css`; `tests/browser_smoke.cjs`.

**Acceptance:** With the A-11 stubbed response, the panel's per-city
counts equal hand-computed counts from the same fixture; a city
with no evaluated stops shows "not evaluated", never zero-service
language. Existing smoke assertions still pass. Run the full Python
suite and the browser smoke.

**Depends on:** A-11.

### A-13 — Time-scrub control wiring

**Objective:** Add the mechanical control only: a time input (range
slider plus numeric readout) bound to the bubble/plan query's
`time` parameter within the service day; moving it re-issues the
current query with the new time and re-renders the layer and
summary. No animation design, no playback behaviour — those are
design decisions, not this chunk.

**Files:** `web/app.js`; `web/index.html`; `web/style.css`;
`tests/browser_smoke.cjs`.

**Acceptance:** Browser smoke: setting the control to a new value
issues a request whose `time` parameter matches the control, and
the re-rendered layer corresponds to the stubbed response for that
time. Existing smoke assertions still pass. Run the full Python
suite and the browser smoke.

**Depends on:** A-11.

---

## Item 5 — M0.R regional/intercity rail + New Hampshire (queued)

ROADMAP M0.R: do not implement the expansion ahead of ingestion and
routing reliability; these chunks build only its architectural
accommodations. Verified sources only; distinguish Manchester CT
from Manchester NH everywhere; fares and seat availability stay
`unknown` unless an authoritative source explicitly supplies them.

### A-14 — Configurable coverage policy

**Objective:** Replace the importer's hard-coded geographic
rectangle (currently `40.9<=lat<=43.1 and -73.8<=lon<=-70.5` in
`import_gtfs.py`) and the hard-coded MBTA rail-only filter with a
documented configuration file, `config/coverage.json`, expressing
per-feed geographic bounds and mode filters. The shipped default
configuration reproduces today's behaviour exactly, so this chunk
changes no imported data.

**Files:** `import_gtfs.py`; `config/coverage.json` (new);
`tests/test_coverage_policy.py` (new).

**Acceptance:** Importing the fixture feeds with the default config
produces stop/route/trip counts identical to the hard-coded
baseline; a test config widened to include a synthetic New
Hampshire fixture stop admits that stop while the default config
clips it; a malformed config fails with a named error before any
table is written. Run the targeted test file, then the full suite.

**Depends on:** None.

### A-15 — Operator and ticketing metadata

**Objective:** Add optional structured operator/ticketing metadata
as a side table keyed by route: reservation requirement (one of
`required`, `optional`, `none`, `unknown` — default `unknown`),
booking/source URL, boarding restrictions, verified source, and
applicability note. Values come only from a curated config file
entries with a named source; nothing is inferred from route type or
operator name. API `route` responses include the metadata block
when present.

**Files:** `import_gtfs.py` (schema + load); `config/ticketing.json`
(new); `database.py`; `server.py`; `API.md`;
`tests/test_ticketing_metadata.py` (new).

**Acceptance:** A fixture route with a config entry round-trips its
metadata through import and the `route` response; a fixture route
with no entry reports `reservation: "unknown"` and no booking URL;
an entry without a named source is rejected at import. Run the
targeted test file, then the full suite.

**Depends on:** A-14.

### A-16 — State-qualified place discovery

**Objective:** Make place identity unambiguous in discovery: add a
documented place table (`config/places.json`) mapping priority
place names to city/state labels, and have `stops` search results
and `coverage` carry the state label for stops in listed places —
Manchester, CT and Manchester, NH must be distinguishable in API
output. Labels come from the curated table, never from coordinate
guesswork; unlisted places simply carry no label.

**Files:** `config/places.json` (new); `database.py`; `server.py`;
`API.md`; `tests/test_stops.py`.

**Acceptance:** Fixture stops in Manchester CT and Manchester NH
return distinct state labels; the existing stop-lookup tests
(Union Station, Court Square, nonsense query) pass unchanged; a
stop outside every listed place returns no label rather than a
guessed one. Run the targeted test file, then the full suite.

**Depends on:** A-14.

### A-17 — M0.R verified-source investigation register

**Objective:** Documentation only. Compile the source register for
the M0.R investigation — Downeaster and New Hampshire services
first, then the other ROADMAP-named Amtrak/intercity services —
recording for each: operator, official source URL (GTFS,
structured timetable, or official PDF), publisher, retrieval date,
and what the source does and does not establish. A service whose
official source cannot be located is listed as **unverified**;
nothing in the register asserts service that a cited source does
not establish.

**Files:** `M0R_SOURCES.md` (new).

**Acceptance:** Every service entry carries an official URL and a
retrieval date, or is explicitly marked unverified; the register
distinguishes direct-rail from bus-connected target places using
only cited sources; no fares, frequencies, or station claims
appear without a citation in the same entry. This chunk has no
code and no test-suite impact; the full suite still runs green.

**Depends on:** None.

---

## NOT CHUNKED — and why

- **Deferred milestones M1, M2, M3.** ROADMAP defers Apache/macOS
  self-hosting, the PWA, and the native iOS investigation behind
  explicit owner authorization. They are not chunked, scoped, or
  estimated here, and no chunk in this file is a step toward them.
- **The Metro map UI's visual and interaction design.** Layout,
  colour system, typography, iconography, how the three bubble
  classes should *look*, time-scrubbing playback/animation design,
  and city-summary presentation are design judgment against ROADMAP
  M0.D acceptance — an owner/design session, not a Luna sitting.
  A-11–A-13 build only the data-bound substrate that design will
  style.
- **Per-agency PDF layout parsers.** A-03 extracts text layers and
  A-02/A-04 store and gate normalized records, but each agency's
  timetable PDF layout differs; a parser for a specific layout can
  only be honestly chunked once a real target agency and document
  are chosen. Choosing the first real no-GTFS agency is an owner /
  source-availability decision, not a chunk.
- **Bubble correctness proof work.** Replacing the sampled
  cross-validation with an exhaustive reverse-scan-vs-plan agreement
  check (scoped item 2's correctness half) requires fixture-region
  design judgment about what "exhaustive" must cover; it belongs
  with the L2.x latency work in `CODEX_HANDOFF.md`, not here.
- **Which New Hampshire services to actually include.** A-14–A-17
  build the policy mechanism, metadata, labels, and source
  register. Deciding the coverage policy itself — which services
  and places enter the atlas — is an owner decision the register
  informs; no chunk pre-empts it.
- **Fares, seat availability, and through-ticketing claims.** No
  authoritative source currently supplies them; per ROADMAP they
  stay `unknown`. Any future chunk proposing otherwise must cite
  the authoritative source in its card before it is written.
