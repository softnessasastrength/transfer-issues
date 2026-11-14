# Engineering audit and next execution slices — 2026-11-13

## Scope and evidence boundaries

This audit accompanies the owner-requested Command Center feature blitz and standing
engineering directive. Repository baseline is merged main `db18760`; developer-tool
work is in separate unmerged drafts #44–#46. The new CI-coverage slice is based on
#46. No branches were deleted, rebased, force-pushed or merged. No feed download,
network installation, release or device operation was performed.

## Verified implementation and tests

- Python tests exercise calendars, transfers, shared routing fixtures, SQLite pack
  export/assembly, dependency consent, HTTP endpoints, Termux entrypoints and pack
  validation, Crostini launcher and developer adapters. Full suite after CI-contract
  additions: **90 passing tests** through `python3 -m developer_center --run test`.
  These are synthetic regressions, not live regional service verification.
- Five existing Android JUnit classes cover planner UI models, routing regressions,
  golden parity, offline router and street graph. Earlier fresh local run executed
  30 tests; this cycle's Python-only changes do not claim another local Android run.
- Draft #44 exact head `29c7141`: both CI jobs passed in run `43433186472`.
  Draft #45 exact head `59ef868`: both passed in run `43434668047`.
  Subsequent head results must be checked independently.
- Source/test Python compilation and root launcher Bash syntax passed locally.
- Termux pack verification fixtures cover a valid synthetic pack, checksum tamper,
  traversal and mixed-agency routes. Termux entrypoint tests check loopback and
  validation gates. This does not establish actual phone installation or routing.

## Offline routing and pack integration gaps

Observed in source, not inferred from older roadmap claims:

1. `OfflinePlannerActivity.kt` reads installed per-agency databases and optionally
   `streets.sqlite`; it uses native date-aware router and estimated transfer paths.
   It does not establish a licensed offline street basemap or local address index.
2. `MainActivity.kt` explicitly reviews selected downloads, stages files, hashes
   them, checks SQLite integrity and replaces agency files with backup handling.
   Activation is per agency, not a single atomic selected-network-set transaction.
   Interruption between renaming an active file and activating its replacement
   needs recovery tests. Checksums from an untrusted catalogue are not publisher
   authentication; no claim of trusted production manifest distribution is made.
3. `scripts/build_lan_packs.py` exports content-addressed agency databases and a
   catalogue. Its scope explicitly excludes street map/graph coverage. This path
   does not supply the full dependency/version/provenance contract specified by
   Choose Your Transit Network.
4. `scripts/verify_lan_catalog.py` checks format, allowed coverage, size/hash,
   SQLite integrity and agency route counts. It is not comprehensive schema,
   service-validity, dangling-reference or real-feed completeness validation.
5. `offline_packages.py` separately implements consent/dependency resolution and
   content-addressed staged activation in Python. That implementation is not a
   proof that the Android installer shares the same lifecycle or schema contract.
6. Android native routing exists; several older Android README/agent notes claiming
   it is absent or never compiled are historical. Keep device acceptance pending
   while consolidating current documentation in a future focused Android slice.

No source-data gap is interpreted as absence of actual transit. PVTA and full CT
coverage remain unverified in this cycle. No existing installed data was pruned or
limited to achieve smaller packs.

## CI and release audit

Only `.github/workflows/routing-verification.yml` exists in the inspected checkout.
It runs PR/manual Python regressions and Android debug build/JVM tests. No release
publication workflow is enabled here; experimental-release draft #32 is not proof
of an authorised or active release pipeline. Contents permission remains read-only.
No release, deployment, signing, visibility or branch-protection change was made.

The existing PR path filter omitted most Python modules, launchers and developer
package changes. The CI-coverage slice adds root Python/shell, scripts and developer
package paths. It compiles Python sources and checks launcher syntax before tests.
Python test output is captured with explicit Bash pipefail so tee cannot hide a
failing runner. Always-run uploads preserve the synthetic Python log and Android
JUnit XML; APK upload remains successful-build-only. Retention is seven days.
Missing reports after an early setup failure may produce an upload warning; that
never converts the failed verification job into success.

Hosted actions emit deprecation notices about Node runtimes/setup-java versions and
ubuntu-latest migration. Updating those action versions is queued separately;
existing functioning JDK/Gradle versions were preserved. No paid tools, scanner
subscriptions or recurring automation were introduced.

## Prioritised next slices

1. **Installer recovery and validation:** deterministic tests for interrupted
   activation, corrupt/incorrect schema and rollback before adding auto-update UX.
2. **Pack contract parity:** document actual Python/Android catalogue differences,
   source validity and selected-network dependency review; implement one compatible
   verified contract without silently adding agencies or replacing architecture.
3. **Android usability/accessibility:** current empty/error states, source freshness,
   accessible stop selection and keyboard/screen-reader behaviour, then device tests.
4. **Routing correctness:** resolve nullable queue-poll warnings, broaden calendar/
   overnight/restriction parity and measure representative network scaling.
5. **Offline acceptance:** acquire/validate authoritative selected feeds and licensed
   map/graph/address dependencies; test cold start and journeys on actual devices.

The Command Center can next expose read-only catalogue validation and on-demand CI
inspection. Downloads, shared dependencies, new agencies, device installations and
clean builds must retain their explicit approval boundaries. Geographic expansion
remains staged behind correctness and the authoritative roadmap.
