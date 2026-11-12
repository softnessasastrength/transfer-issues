# CI/CD: pull request tests and Android debug artifacts

Decision 001: **B — automated development builds, human-controlled merges**.

The workflow in `.github/workflows/pr-ci.yml` runs on pull requests and on explicit manual dispatch. It compiles Python, executes the repository's synthetic Python unit tests, runs Android Kotlin unit tests, and assembles a **debug** APK using JDK 17, Android SDK 35 and Gradle 8.9. The Android project currently has wrapper properties but no checked-in wrapper JAR/script; CI installs a pinned Gradle distribution rather than pretending `./gradlew` exists.

After a successful run, open **GitHub → Actions → Pull request validation and Android debug APK → run → Artifacts** to download the APK ZIP and extract the APK on your Android phone. GitHub authentication and permission to install the APK may be required. Artifacts expire after 14 days. Test reports are also uploaded (including on failed Android jobs when available).

## Safety and scope

- Read-only repository token; no signing keys, production credentials, GTFS downloads or transit datasets are bundled.
- No release publishing, Play Store upload, deployment, auto-merge or main-branch rewriting.
- A successful APK build does **not** establish real-device compatibility, offline dataset installation, map coverage, routing correctness or travel readiness.
- CI runs synthetic tests without importing live feeds. Device/airplane-mode and browser acceptance remain manual gates.
- This PR is based on `feature/android-visual-journey-planner`, because the Android source is not yet on `main`. Until the relevant feature branches are integrated, the workflow cannot provide Android APKs for unrelated main-only PRs. Rebase/retarget deliberately after feature integration.
- Repository administrators must configure branch protection or rulesets if merge blocking is desired; a CI workflow alone cannot enforce approval.
- Pull requests from forks are not granted write access or secrets. Artifact downloads may require GitHub sign-in.

## Verification checklist

1. Open a pull request targeting the Android feature branch and confirm both jobs start.
2. Confirm Python tests pass and Kotlin tests run; investigate failures rather than overriding them.
3. Confirm the debug APK artifact exists and installs on an actual Android device.
4. Verify app launch, locally installed transit packs, airplane-mode behavior, and no unintended network dependency.
5. Confirm the pull request remains draft/unmerged until manually approved.

This workflow has not yet been executed or validated by a GitHub-hosted runner at the time of authoring. Treat the first run as an acceptance gate.
