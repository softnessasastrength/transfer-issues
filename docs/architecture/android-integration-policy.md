# Android integration branch policy (Decision 002: B)

## Established baseline

`integration/android` was created directly from `feature/ci-pr-android-artifacts` on 2026-11-12. This **preserves** the existing feature ancestry; it does not merge or close any existing pull request. The initial baseline includes the Android offline shell, native offline router, native street graph, visual journey planner and proposed CI workflow. These are **draft/unverified**, not accepted production features.

Verified GitHub ancestry comparisons (ahead / behind):
- `feature/android-offline-shell` → `feature/android-native-offline-routing`: 75 / 0
- `feature/android-native-offline-routing` → `feature/android-native-street-routing`: 8 / 0
- `feature/android-native-street-routing` → `feature/android-visual-journey-planner`: 8 / 0
- `feature/android-visual-journey-planner` → `feature/ci-pr-android-artifacts`: 3 / 0
- `feature/unified-offline-network` → `feature/android-visual-journey-planner`: 45 / 0

These comparisons establish ancestry, **not** compatibility, tests passing, or readiness to merge into main.

## Integration rules

1. Create each new Android feature branch from `integration/android` after fetching its current tip.
2. Open a **draft** PR targeting `integration/android`. Do not push feature work directly to integration.
3. Require Python tests, Android Kotlin tests and debug APK build. Review APK and real-device offline behavior separately. Do not merge on CI alone.
4. Human reviewer must approve each PR before manually merging; configure GitHub rulesets/branch protection to enforce required checks, approvals and no force pushes. Workflow files alone cannot enforce this.
5. Keep `main` unchanged. Later, create a separate reviewed PR from `integration/android` to `main` after full browser, GTFS, physical Android and airplane-mode acceptance.
6. Retain source branch names, open PRs, notes, data provenance and prior work. Do not automatically merge, squash, delete branches or rewrite history.
7. Independently developed `feature/lan-android-offline-poc`, `feature/unified-offline-network`, `feature/offline-pack-manager-poc`, iOS and docs branches need dedicated compatibility review before being included. Shared ancestry does not prove feature integration.
8. Do not commit downloaded GTFS, SQLite, APKs, credentials or signing material.

## CI trigger detail

The accompanying workflow change adds a `push` trigger scoped to `integration/android`, in addition to PR and manual triggers. The updated workflow will only take effect for integration pushes **after this policy PR is manually merged**. PR validation already exists on the integration baseline. No automatic release or deployment occurs.

## Manual acceptance

- Inspect the proposed policy and CI trigger.
- Confirm CI jobs execute on this draft PR, and review failures.
- Verify Android APK artifact generation and device installation.
- Configure protected branch rules for `integration/android` separately.
- Do not mark integration or Android release-ready until actual acceptance tests pass.
