# Experimental Android GitHub Releases

Owner authorized automatic APK publishing to the private repository's Releases tab after CI passes.

## Trigger and gates

The existing `.github/workflows/routing-verification.yml` now runs on pushes to `feature/**` branches, relevant pull requests, and manual dispatch. The release job runs only on a push or manual dispatch and **depends on both** `python-routing` and `android-debug` succeeding. Pull-request-only events run tests without publishing releases. The release job has scoped `contents: write` permission; other jobs remain read-only.

Each successful commit produces an experimental **prerelease** tag `atlas-dev-<12-character SHA>` with:
- `transit-atlas-debug-<SHA>.apk` from the same successful Android job;
- `SHA256SUMS.txt` for verification;
- notes identifying the branch, limitations, and debug-signing behavior.

Repeated runs for the same commit update the same tag's assets with `--clobber`. There is no deployment to Play Store, no automatic installation on phones, no source feed inclusion, and no merging.

## Download

Open the private repository **Releases** tab and choose the most recent experimental prerelease, then download the APK asset directly. Private GitHub authentication is required. The `Actions` artifact remains available for troubleshooting.

## Important experimental limitations

**Debug signing:** the Android Gradle plugin's default debug keystore is generated per CI runner. Two APKs from different runners may have different signing certificates. Android may refuse in-place upgrades; uninstalling the prior app will also delete its app-private installed transit packs. A stable signing keystore stored securely as GitHub Actions secrets and versionCode automation should be added before promising seamless updates. Never commit production signing material.

**Scope:** the build is an offline-first *shell* and prototype planner. No real feeds are bundled. The user must opt in to selected network downloads from a reachable Mac mini LAN server. Device launch, usability and airplane-mode behavior remain unverified until tested on a phone.

**Branch policy:** only `feature/**` pushes auto-publish experimental releases. Pull requests do not publish by themselves. If repo Actions permissions disallow creating releases, an owner must allow Actions to write repository contents. GitHub private repository access and retention policies still apply.

**Verification:** successful workflow results, and a release with attached APK, are required before claiming publishing is operational.
