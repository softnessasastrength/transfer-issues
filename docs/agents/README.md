# Multi-agent handoff

Read root `AGENTS.md`, then `ROADMAP.md`, `DECISIONS.md`, and the nearest directory `AGENTS.md` before changing code. Root instructions always apply. The roadmap may contain historical status notes: verify current code and branch before treating any note as current.

## Mission

Build an **offline-first, map-first regional transit explorer**: explore an entire network out of curiosity or plan reliable trips. Initial offline target: Connecticut and PVTA; wider Southern New England and Amtrak/NH expansion remain staged. The reference "trains.fyi, but for regional transit" is a *conceptual* comparison, not permission to clone designs, branding or code. See `docs/launch/product-vision.md`.

## Work selection

1. Inspect current branch, repository status, open PR stack, and actual code.
2. Choose the smallest authorized task that advances source integrity, offline capability, or exploration UX.
3. Define input, output, acceptance criteria, and dependencies before coding.
4. Use a feature branch, commit focused changes, and open a draft PR; do not merge without explicit instruction.
5. Record evidence of tests and unresolved blockers in PR; update `DECISIONS.md` for significant decisions and `ROADMAP.md` for scope/status changes.
6. Leave a concise handoff using the template below.

## Current architecture

- Python stdlib GTFS ingestion, SQLite, routing and HTTP API in repo root.
- Browser/Leaflet UI in `web/`; `atlas.sh` launches Mac/Linux/Termux server.
- iOS SwiftUI + WKWebView skeleton in `ios/`, currently requires a reachable backend.
- Android Kotlin/SQLite client in `android/` includes native timetable/transfer routing, a street-graph reader and planner UI. Local JVM tests and debug build passed on 2026-11-13; device and full airplane-mode acceptance remain unverified.
- `scripts/build_offline_poc.py` exports selected CT/PVTA SQLite data and a provenance manifest; not yet a complete statewide or fully offline app.
- Crostini developer dashboard in `developer_center/` wraps fixed `crostini-dev.sh` commands with private local logs/history and APK checksums; see `docs/development/developer-command-center.md`.
- Exported agency packs are checked by `scripts/verify_lan_catalog.py` and `scripts/pack_validation.py`; the read-only Command Center P panel uses the same gate. This is not Android installer parity or complete offline certification.
- Proposed branding and Play Store content in `docs/launch/` are **drafts**, not release-approved claims.

## Required quality gates

- Never invent schedules, connections, route geometry, agency coverage, service validity or live data.
- PVTA ingestion is not verified; fail visibly and record missing feeds. Do not silently mark partial packs complete.
- Keep generated databases, GTFS archives, signing keys, API keys, personal data, caches and build outputs out of Git.
- Offline acceptance means cold start and functional maps, schedules and routing in airplane mode, not merely opening the shell.
- Do not add an internet dependency to essential offline features.
- Do not assume Android Studio/Xcode/device tests passed when only source was edited.
- Respect map and transit data licenses and provider bulk-download policies.
- Never force-push, merge major PRs, publish to stores, alter billing, or set up recurring tasks without authorization.

## Handoff template

```markdown
### Agent handoff — YYYY-MM-DD
- Branch / PR:
- Scope and user authorization:
- Files changed:
- Tests run and results:
- Tests NOT run:
- Data sources / freshness / coverage:
- Remaining blockers:
- Next smallest safe step:
```

## PR stack caution

Feature PRs are stacked and generally unmerged. Confirm actual current branch ancestry before rebasing or cherry-picking. Never assume `main` contains the browser, iOS or Android work. Inspect live GitHub state before modifying.
