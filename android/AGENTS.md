# Android agent instructions

Read root `AGENTS.md`, `docs/agents/README.md`, `android/README.md`, and `ios/OFFLINE_POC.md`.

Scope: `android/` and shared offline-pack schema/tests when explicitly needed. Kotlin Android project with native SQLite/routing, a geographic stop/shape preview and explicit agency-pack downloads. Per-agency atomic file activation and legacy-gap recovery have JVM tests; this does not establish device correctness, full package/schema parity, licensed offline basemap or GPS. See `docs/architecture/android-pack-activation-recovery.md`.

Priorities: (1) validated versioned local pack and checksum verification, (2) offline route/stops/timetable browser, (3) offline journey engine and calendar correctness, (4) licensed offline vector map and path graph, (5) opt-in location, (6) exploration UI, (7) optional online overlays. Map-first exploration is a primary product requirement.

Do not request broad permissions or background location without a concrete tested need. No embedded secrets, signing material or live service assumptions. Test Gradle sync, emulator and physical-device airplane mode when available; otherwise explicitly report untested. Do not promise Play Store readiness before actual release checks.
