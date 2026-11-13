# Transit Atlas Developer Command Center

## Purpose and scope

This is a local, opt-in developer interface for the existing Crostini launcher.
It does not replace the transit application or the Termux TUI. The first increment
provides repository telemetry, tool availability, disk space, APK discovery and
checksums, recorded build/test results, and four existing operations. It does not
install packages, alter SDK configuration, fetch feeds, start a server, manipulate
Git branches, clean builds, install APKs, or configure recurring tasks.

Run from the checkout root with Python 3.11 or newer:

```bash
bash crostini-dev.sh command-center
python3 -m developer_center --status
python3 -m developer_center --run doctor
python3 -m developer_center --run test
python3 -m developer_center --run android-test
python3 -m developer_center --run android-build
```

The menu uses arrows, Enter, R to refresh, and Q to quit. Enter explicitly starts
an operation. During execution the terminal leaves curses and reports the log
location. Output goes to the log, not a live scrolling panel; the menu returns when
the operation ends. Ctrl+C interrupts the foreground operation. No detached build
session is created. A forced shutdown can leave a partial log without a result;
this is deliberately not represented as success. Gradle daemon lifecycle remains
under Gradle's control. No terminal or physical Chromebook accessibility
certification is claimed. The JSON interface supports non-interactive automation
and screen-reader workflows without requiring curses navigation.

## Architecture and dependency choice

- `developer_center/adapters.py`: fixed argv command registry, subprocess boundary,
  typed execution record, read-only Git inspection and streamed SHA-256 calculation.
- `developer_center/__main__.py`: argument parsing and terminal presentation.
- `crostini-dev.sh`: existing source of build command/toolchain policy.
- `tests/test_developer_center.py`: isolated adapter regression tests.

Python's standard-library curses is a mature terminal framework already used by
`scripts/termux_tui.py`. It avoids adding a package installation or network
requirement to this small increment. Textual/Rich can be reconsidered for concurrent
panels and asynchronous operations when those requirements justify a dependency.
The backend remains standard-library-only; no transit routing code was changed.

## Records, artifacts and privacy

Default records live in ignored `build/developer-center/`. Override with
`--output /absolute/local/path` or `ATLAS_DEV_OUTPUT`. Use a private local directory;
external paths may require filesystem approval. Each run has a unique log and
JSON result recording action, UTC start, elapsed seconds, exit code, full starting
commit, starting Git status and log path. Files are created with mode 0600. JSON
results are atomically renamed into place. Separate per-run files avoid concurrent
history writers overwriting a shared index. Logs are not rotated or deleted.

The dashboard shows the ten most recent records. Historical success is not a
certification of the current tree; commit and starting changes are retained to make
this visible. A dirty-tree record is not a content snapshot. Malformed JSON is
reported visibly. APKs are read from Android's normal output tree, hashed in chunks,
and reported with path and size. Hashes prove byte identity, not signing trust or
that the APK corresponds to the current checkout. Concurrent builds can change
artifacts while the dashboard reads them; use a completed build for review.

The `--run` exit code reflects the operation (127 for launch failure, 130 for
interruption). Unknown actions are rejected before files are created. No input is
interpolated into a shell. Logs may contain private paths and build diagnostics;
review before sharing. Credentials and device logs are not intentionally collected.
Storage errors are fatal and visible rather than silently losing evidence.

## Verification and recovery

```bash
python3 -m unittest discover -s tests -p test_developer_center.py -v
bash crostini-dev.sh test
bash crostini-dev.sh android-test
bash crostini-dev.sh android-build
```

A sandbox denial of Gradle native-cache writes or loopback sockets is an executor
restriction, not evidence of a broken Crostini installation. Run with authorised
host access instead of reinstalling functioning dependencies. Missing Gradle/SDK
requirements remain explained by the underlying launcher. ADB is optional and is
not installed by this tool. On interruption, inspect the saved log and run the
operation again; test and incremental build commands preserve source and data.

## Remaining design stages

Installed-pack provenance/validation should reuse the existing catalogue verifier,
with consent and source-freshness semantics reviewed before exposing modifications.
Device discovery must precede any explicit APK-install confirmation. Clean builds
need a concrete target preview and confirmation. PR/CI integrations must tolerate
missing authentication and run only on demand. A virtual environment is optional
for the present standard-library implementation and was not created merely to
provide another directory to maintain.

## Historical result summaries (second increment)

Press **T** to toggle the reports view. Up/down scrolls this view; Enter cannot run
builds while viewing reports. Q exits and R refreshes. `--status` exposes the same
information under `test_results` and each artifact's `metadata`.

Python evidence comes from the newest `test` record among the dashboard's ten most
recent records and its sibling `.log` file. The record's arbitrary `log` field is
not followed. This also permits moving a complete history directory. The parser
streams logs and uses the last recognised unittest count/verdict. A nonzero command
exit overrides passing text; missing/incomplete/empty summaries never report passed.
If the newest test log is missing it does not fall back to an older green result.
Old records without commit information retain unknown provenance. Counts may include
skipped tests; this is a summary of unittest output, not an independent test runner.

Android evidence reads Gradle `TEST-*.xml` under
`android/app/build/test-results/testDebugUnitTest`. Suite counters are added across
reports; malformed XML, missing/negative/inconsistent counters or unsupported nested
suite structures make the aggregate invalid. A directory with no reports is
unavailable; an empty or entirely skipped result is `no-tests`. Simple `testsuite`
and flat `testsuites` documents are supported. Counters are publisher-provided,
not independently checked against individual testcase elements. Files may be from
different runs, branches or cached builds; per-file times are exposed, and no
current-checkout certification is inferred from them.

APK information is read from adjacent `output-metadata.json`, matched uniquely by
APK filename. It shows application ID, variant and version when present. Malformed,
missing and ambiguous metadata remain visible. This metadata is not extracted from
or cryptographically bound to APK contents. Use aapt/signature tooling separately
when identity/signing verification is needed.

All evidence includes `current_tree_verified: false`. Age is based on filesystem
modification time, clamped at zero for future clocks; copying files can change it.
Neither a recent timestamp nor an identical commit proves a clean, complete test
execution. Reading these summaries never launches builds or changes reports.

## Inspection panels and saved-log browser (third increment)

The dashboard now has direct navigation: **D** dashboard, **T** test evidence,
**G** Git, **E** environment, **L** logs and **H** (or ?) help. Q exits anywhere.
Up/down selects build operations on D and scrolls text on other pages. R refreshes
on demand. In L, left selects a newer log and right an older one; up/down scrolls
the current preview. Builds execute with Enter only on D. Returning to D is now
explicit; T selects evidence rather than toggling back.

Headless equivalents (mutually exclusive with --run/--status):

```bash
python3 -m developer_center --inspect git
python3 -m developer_center --inspect environment
python3 -m developer_center --inspect logs
python3 -m developer_center --inspect help
python3 -m developer_center --log EXISTING_FILENAME.log
```

`--output` / `ATLAS_DEV_OUTPUT` also select the log-browsing directory. A log preview
returns exit 1 when unavailable, and invalid filename input exits 2. The log list
includes all regular .log files in newest-first order, independent of result JSON,
so interrupted operations can still be inspected. Its full JSON output lists names,
byte counts and filesystem timestamps. The terminal displays a 64 KiB tail; the
complete file remains available locally. Long lines are clipped to terminal width;
use headless JSON or a trusted local editor for full lines. A tail can start in the
middle of a UTF-8 character; undecodable bytes are replaced, not treated as failure.

The reader rejects paths outside the selected directory, symlinks and nonregular
files (including FIFOs) and opens files without following the final symlink. It
uses bounded reads and strips nonprinting control characters to prevent saved
terminal escape sequences being replayed. It retains newline/tab layout; colour
sequences may remain as inert visible bracket fragments. No files are rotated,
truncated or deleted. A concurrent writer may mean a preview is incomplete.

Git inspection shows local branch/commit/status, local branch tips and the eight
most recent commit subjects. It never fetches, switches branches, exposes remote
URLs or changes Git configuration. The environment page checks Python/SQLite
versions, executable paths and the launcher-selected SDK environment's Android 35
platform/build-tools presence. These are presence checks, not SDK usability or
Gradle-build guarantees. It reads no arbitrary environment dump and installs
nothing. Interactive help explains operations, cache caveats and documentation
paths. This increment adds no new dependency or network operation.
