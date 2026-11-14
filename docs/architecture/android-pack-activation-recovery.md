# Android per-agency pack activation and interrupted-install recovery

## Problem and scope

The previous installer renamed the active database to its previous filename, then
renamed the verified download into the active filename. A process interruption
between those operations left no active database. A failed second rename attempted
rollback without checking whether rollback succeeded. Concurrent download threads
also shared staging filenames.

`AgencyPackStore.kt` now isolates this file lifecycle from UI/network logic and
provides deterministic JVM failure tests. It preserves the existing per-agency
filenames and explicit network-selection/download confirmation. This is a local
reliability improvement, not a new package system, auto-update policy or transaction
across a selected network set. It does not implement publisher authentication or
Android parity with the Python relational validator.

## Activation protocol

The caller must already have checked downloaded byte count, catalogue SHA-256 and
SQLite integrity. MainActivity retains those checks and syncs downloaded bytes
before activation. The helper requires a nonempty regular staged file and rejects
unknown agency names and relevant symlink paths.

For an existing agency:

1. Leave `agency.sqlite` in place while copying it to `agency.rollback-copy`.
2. Sync copied bytes and atomically replace `agency.previous.sqlite` with that copy.
3. Atomically replace `agency.sqlite` with `.agency.download`.

For a first install, only step 3 is needed. There is no delete-active/rename-active
fallback. Both moves use Java NIO `ATOMIC_MOVE` plus `REPLACE_EXISTING` within the
same app-private directory. If the filesystem/provider cannot perform the atomic
move, installation fails visibly instead of creating an active-file gap. Existing
JDK 17 / Android minimum API 26 tooling is unchanged.

| Interruption or failure | Active file | Previous file |
| --- | --- | --- |
| During download/verification | Existing active untouched | Existing previous untouched |
| During rollback copy or before its atomic move | Existing active untouched | Existing previous untouched |
| After rollback move, before new activation | Existing active untouched | Copy of existing active |
| After successful new activation | Verified incoming bytes | Prior active bytes |
| Legacy old-installer gap | Absent until recovery succeeds | Existing backup retained |

A successful update replaces the older rollback version with the just-replaced
active version, matching the existing one-previous-version policy. No unrelated
agency pack, user record, map/graph or selected region is deleted. Copying can require
substantial temporary space for large packs; no arbitrary size limit is imposed.
Out-of-space/copy/sync/move failures must leave the old active name intact. This is
process-interruption protection, not a power-loss/filesystem durability guarantee:
parent-directory metadata is not explicitly fsynced and device behaviour is untested.

## Legacy recovery and app startup

MainActivity performs recovery on a worker thread before enabling downloads and
offline entry buttons. LAN browsing is unchanged. For each recognised agency:

- If active exists, do not replace or revalidate it automatically.
- If active is absent and previous exists, copy previous to `agency.recovery-copy`,
  sync the copy, run the caller's SQLite integrity check, then activate atomically.
- Keep the original previous file even after successful recovery.
- If validation/copy/move fails, leave previous intact and display an actionable
  recovery message. Do not promote `.agency.download` or fetch replacement data.

An unfinished first install with no previous file remains uninstalled. Existing
active corruption is deliberately not silently replaced by an older timetable.
The recovery callback checks SQLite integrity, not source freshness, schema parity,
agency identity or a stored signature/hash. Those checks remain separate work.
Recovery may restore an older scheduled dataset; it cannot certify current service.
Startup recovery is wired to the launcher activity, not every possible direct
component launch. No process-death instrumentation or actual phone test is claimed.

## Concurrency and leftover files

One process-wide monitor serializes the entire download/stage/verify/activate block
across Activity instances and threads. Recovery uses the same monitor. Nested
activation calls are reentrant. UI work stays on the UI thread; filesystem/network
work stays on worker threads. This is not a cross-process file lock; external or
other-process modifications are outside the verified contract.

A failed copy may leave a `.rollback-copy`/`.recovery-copy` working file (without the
SQLite extension); a retry overwrites that working copy. These files never become
active without the subsequent checks/move. No automatic pruning or new cleanup
service is configured. Existing download-finally cleanup remains in place. The
helper does not delete active or previous files to make an operation succeed.

## Executed verification

`AgencyPackStoreTest.kt` contains 14 JVM tests using real temporary files and injected
move failures: first install, update/rollback bytes, backup copy/move failure,
activation failure and retry, unsupported atomic move, validated legacy recovery,
invalid recovery validation, recovery copy/move failure and retry, unpromoted partial
downloads, existing-active preservation, unknown agency rejection and serialization
across store instances.

```bash
bash crostini-dev.sh android-test
bash crostini-dev.sh android-build
python3 -m developer_center --run test
```

Observed locally: 44 Android JVM tests with zero failures/errors/skips (the 14 new
file-lifecycle cases plus 30 existing tests), fresh unit-test task execution and a
successful debug APK assembly. Android test command: Gradle reported 19 seconds;
debug assembly: 13 seconds. Full Python suite: 100 passed. JVM tests use fixture byte
strings and callbacks; they do not exercise Android SQLite APIs, UI lifecycle,
actual network interruptions, flash storage, app process death, device installation
or airplane mode. Hosted exact-head CI must be inspected separately.

## Next acceptance work

Implement compatible Android schema/reference validation, then exercise this flow
on an emulator/physical device with valid selected feeds: kill during backup and
activation, corrupt backup, storage exhaustion, Activity recreation, repeated
confirmation and cold start without network. Preserve explicit selection and
shared-dependency consent. Multi-agency atomic activation and signed manifests
remain separate architecture work, not implied by this per-file protocol.

Local debug artifact inspected after assembly: 937,674 bytes,
SHA-256 `37cb8c3a58ff2786ecbaf4cc260e8148b7913e8218b545ad35dc5365453f8990`.
This identifies that local APK's bytes, not reproducible-build equivalence or device
validation. Installed feed packs are treated as immutable SQLite files; this helper
is not a backup mechanism for arbitrary databases with concurrent WAL writers.
