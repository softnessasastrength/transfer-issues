# Decision 005: parallel experimental development plan

Date: 2026-11-12. Owner selected **E**: pursue transit, development infrastructure, Android UX and regional expansion in parallel. This is authorization to plan and implement focused draft PRs, **not** to merge, publish a release, silently install networks, or claim device validation.

## Verified starting evidence

- `main` README documents a Python/SQLite desktop proof of concept with incomplete source coverage and no certified offline basemap.
- Existing PRs include #31 (Kotlin CI repair), #32 (private prerelease proposal), #35 (pack verifier), #37 (Crostini tooling), and #38 (Termux TUI). These are *existing proposals*, not proof of successful CI or integration.
- Preserve the previously working Android APK as the regression baseline. Do not assume `main` contains unmerged Android code.
- ROADMAP.md, AGENTS.md, docs/agents/README.md, docs/architecture/offline-storage-policy.md and docs/features/choose-transit-network.md remain binding. Older roadmap status statements must be checked against branch content.

## Parallel tracks and first executable slices

| Track | First slice | Dependency | Acceptance evidence |
| --- | --- | --- | --- |
| A: Transit engine | Validate calendar, transfers, missing-agency disclosure and shared Python/Kotlin golden fixtures | Identify current integrated Android baseline and #31 lineage | Deterministic synthetic tests in both languages; explicit coverage and freshness |
| B: Developer infrastructure | Verify #34-#38 ancestry and CI; independently test Termux TUI and Crostini commands | Existing stacked branches; no blind merges | Clean CI, shell syntax/tests, manual phone and Chromebook smoke-test checklist |
| C: Android experience | Improve offline planner accessibility and failure/empty states without online dependencies | Verified Android branch; user-selected pack contract | Kotlin unit tests, emulator/device acceptance plan, airplane-mode cold-start evidence |
| D: Regional expansion | Source registry and fixtures for NH/Downeaster/Amtrak connectivity; no invented schedules | GTFS provenance and calendar correctness | Verified official-source metadata, explicit unavailable coverage, synthetic boundary tests |

## Integration sequence

1. Inspect PR ancestry, branch tips, checks and changed files. Reconcile overlapping Termux and Android work without force-pushing or rewriting history.
2. Keep each track on a dedicated branch and draft PR. Base on the actual dependency branch, not automatically on `main`.
3. Run source-level synthetic checks, Python tests, Kotlin/Gradle tests, then CI; report unexecuted checks separately.
4. Test Android cold start in airplane mode with a verified pack, interrupted/corrupt downloads, rollback, and no silent agency additions. Physical device results require actual owner/device execution.
5. Review integration PRs manually before any merge. Release automation must be independently approved and proven gated on green CI.

## Blocking questions to resolve from code, not guesses

- Which Termux stage branches are actually merged, and is PR #38 already included in the working phone build?
- Which Android branch produced the successfully launched APK, and are its checks green at current HEAD?
- Is #32 still excluded from `main`, and what release workflow is actually active?
- Which official transit feeds are valid for the requested service date? PVTA remains unverified until authoritative data is validated.
- Which offline map data can legally be distributed, and which map/geocoding features still require network?

## Guardrails

Never commit raw GTFS archives, generated SQLite packs, credentials, signing keys, or private records. No forced storage cap, silent pruning, unapproved agency downloads, unsafe remote Termux server exposure, auto-merge, store release, or fabricated transit service. The first planning PR changes documentation only and does not establish test or CI success.

## Agent handoff

- Branch: `planning/decision-005-parallel-tracks`
- Scope: cross-track execution plan only
- Files changed: this plan
- Tests run: none; documentation-only
- Tests not run: CI, Python, Gradle, shell, physical devices
- Remaining blockers: branch/CI inventory and actual offline/device acceptance
- Next smallest safe step: inspect current PR branch dependencies and implement one verified slice per track as separate draft PRs
