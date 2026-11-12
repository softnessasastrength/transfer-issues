# iOS agent instructions

Read root `AGENTS.md`, `docs/agents/README.md`, `ios/README.md`, and `ios/OFFLINE_POC.md`.

Scope: `ios/` and documented shared data-pack contracts. Existing SwiftUI/WKWebView app is a **server-connected shell**, not an offline native router.

Priority: native SQLite pack loading/validation, schedule and route exploration, offline routing, licensed offline map renderer, native Core Location permissions, and airplane-mode tests. Keep browser-shell fallback explicit until native offline features are real. Never assume HTTP localhost on iPhone reaches a Mac, or that WKWebView geolocation is tested.

Do not commit generated Xcode projects, provisioning profiles, certificates, secrets or user data. Validate signing/ATS/permissions in Xcode on a real device when possible; otherwise document gaps.
