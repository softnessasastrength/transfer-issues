# Step 9: Android compile and golden parity verification

User chose A: finish Android build and cross-language parity validation before expanding features.

## Step 8 CI diagnosis

The latest Step 8 CI run `43305387290` had a successful Python routing job. Android successfully executed `:app:assembleDebug`, but `:app:compileDebugUnitTestKotlin` failed because `RoutingGoldenParityTest.kt` attempted to destructure a ten-element Kotlin `List<String>`. Kotlin List destructuring exposes only `component1` through `component5`.

## Fix

Replace the unsupported ten-field destructuring with explicit indexed extraction `p[0]` through `p[9]`, retaining the existing ten-column fixture length assertion and all 13 shared golden cases.

## Acceptance gate

GitHub Actions must complete **both** `python-routing` and `android-debug` successfully on the Step 9 PR head. The Android job runs `:app:assembleDebug` and `:app:testDebugUnitTest`, including `RoutingGoldenParityTest` and all other native JVM tests. A successful APK compile alone is insufficient.

## Limits

A green synthetic suite does not prove real GTFS correctness, live schedules, offline device installation, street network completeness or performance. The Kotlin compiler currently emits nullable smart-cast warnings in routing modules; those are not asserted to be resolved by this PR. No changes to prior route architecture or user-selected packs, no merges.
