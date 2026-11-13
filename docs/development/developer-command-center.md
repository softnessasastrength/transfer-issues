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
