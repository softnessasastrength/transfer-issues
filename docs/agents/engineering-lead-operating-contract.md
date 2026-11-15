# Engineering lead operating contract

Established 2026-11-13 by the repository owner. This document governs delegated Transit Atlas work; it does not supersede `AGENTS.md`, `ROADMAP.md`, offline-storage policy, or network-consent requirements.

## Delegated authority
- Independently inspect repository state, dependencies, source and CI evidence.
- Implement focused changes on new feature branches; write deterministic tests and documentation; open and maintain **draft** pull requests.
- Investigate CI failures, review logs, and rerun failed jobs when safe.
- Keep a concise evidence-based handoff with exact tests executed, results, limitations, and dependencies.
- Ask the owner for major architectural decisions rather than assuming them.

## Reserved for explicit owner approval
- Any merge into `main` or integration branches; enabling automatic merge.
- Destructive changes, branch deletion, force pushes, history rewrites, and removal of user data.
- Public releases, distribution, production signing, credentials, repository visibility, billing, and security-policy changes.
- New major architecture, trust boundaries, external network exposure, or automatic agency installation.
- Changes to project priorities that conflict with the authoritative roadmap.

## Mandatory PR acceptance checklist
1. Confirm base and head ancestry; identify stacked dependencies and unrelated modifications.
2. Preserve existing work and user-selected data; never commit downloaded GTFS, generated SQLite, secrets, or personal records.
3. Provide a clear scope, test commands, actual observed outcomes, and honest unverified areas.
4. Verify CI for the **specific head SHA** before describing it as green.
5. Distinguish synthetic fixtures from real agency feeds, Android hardware, airplane-mode and Chromebook/Termux acceptance.
6. Preserve explicit agency selection and approval for downloads; offline capability outranks pack-size minimization.
7. Leave PR in draft until owner-approved review/merge decisions; never auto-merge.

## Initial audit checkpoint (2026-11-13)
- Repository: private `softnessasastrength/transfer-issues`; default branch `main`; write access available through the GitHub integration.
- `main` README describes a Python/SQLite desktop proof of concept, not a certified travel-ready atlas.
- Existing open draft proposals include #31 (Kotlin CI repair), #32 (experimental APK release), #35 (Termux pack verification), #36 (Termux debugging), #37 (Crostini), #38 (Termux TUI), and #40 (parallel-track plan).
- #38 is stacked on earlier Termux work; #37 is independently based on main and currently reports a non-mergeable state. Do not infer that either is ready to merge.
- The README reports PVTA unavailable and broader source coverage incomplete. Do not treat absent feed data as absent service.
- This is a **partial metadata/source audit**. Workflow-job status, latest head SHA, live device execution, full branch ancestry and test results have **not** yet been verified.

## Next execution order
1. Inspect open draft PR head/base SHAs and dependency graph; compare against `main` and current Android integration.
2. Read current workflow runs and jobs; identify actual green or failing checks per SHA.
3. Repair the smallest blocking CI/test defect in its own draft PR without bypassing checks.
4. Validate Termux stages #34–#36 before TUI #38; validate Crostini #37 independently.
5. Advance offline pack consent, provenance and routing parity with synthetic tests, then real-feed and hardware acceptance when available.
6. Review experimental release #32 separately; publishing requires explicit owner approval.

## Reporting format
For each workstream report: **Observed / Changed / Tested / Blocked / Owner decision required**. A successful commit or draft PR is not proof of a passing build or a working device.
