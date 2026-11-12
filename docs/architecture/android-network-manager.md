# Android offline network manager: Decision 003 (C)

Status: **draft implementation, uncompiled and not device-verified**.

The existing Android LAN download screen now defaults to **no agencies selected**, parses the existing `transit-atlas-lan-v1` catalog, and builds a dependency-aware, deduplicated review plan before showing an explicit confirmation dialog. It displays actual catalog bytes, version and scope, and reports unavailable selected agencies instead of fabricating coverage. The plan rejects unknown dependencies, invalid package metadata, cycles and unapproved additional agencies. The download path retains existing streamed SHA-256 verification, SQLite integrity check, staging and one-version rollback. The app's offline planner remains independent of the LAN server once real agency SQLite packs have been installed.

**Important scope limit:** this is an incremental *in-app LAN network manager*, not yet an internet-hosted, authenticated, production-grade package service. The current server offers only four agency IDs and does not serve shared basemap/graph dependencies. A manifest advertising new shared dependencies must not be considered installable until the server endpoint and installer support them. Existing SHA-256 values are delivered by the same unauthenticated LAN server, so they detect accidental corruption but **do not authenticate a publisher**. Use only a trusted private LAN. No HTTPS hosting, signed catalog, public URL, auto-updater, background jobs, progress/resume, multi-package atomic transaction, complete offline basemap, or reliable disk-pressure recovery is claimed.

This work deliberately does not enable automatic network updates or add any new transit agency without user confirmation. PVTA remains unavailable unless an actual verified pack exists. Real offline readiness requires licensed map packs, path graphs, current timetables, and physical-device airplane-mode tests.

## Synthetic tests

`android/app/src/test/java/org/southernnewengland/transitatlas/NetworkDownloadPlanTest.kt` covers empty selections, selected-only installation, shared-dependency deduplication, unavailable PVTA, rejected extra agencies, missing dependencies, cycles and malformed hashes. Run `gradle :app:testDebugUnitTest :app:assembleDebug` in `android/` or review the CI job. **No Gradle or Android device execution has been performed in this authoring environment.**

## Next acceptance gates

1. Inspect the PR and review the exact UI, selection and catalog behavior.
2. Run CI, fix any Kotlin/Gradle failures, and install the resulting debug APK.
3. Validate the catalog and network selection against the development Mac mini server.
4. Confirm cancel/empty selection never downloads, and missing PVTA is clearly labeled.
5. Test download interruption, corrupt SQLite, rollback, storage pressure, app restart and airplane mode on an Android device.
6. Before enabling internet-hosted distribution: establish signed manifests or an equivalently authenticated trusted HTTPS distribution channel, version/schema compatibility checks, a shared-dependency package endpoint, transactional activation and recovery.

No PR is authorized to merge automatically.
