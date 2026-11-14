# Project instructions
Read ROADMAP.md at the start of every work session. It is the authoritative implementation plan. Preserve current priorities. Record new feature requests and dependencies there. Do not implement deferred milestones without explicit authorization. Verify acceptance criteria before changing status to complete. Never fabricate missing transit service or treat feed provenance as a live-service guarantee. Do not configure recurring tasks.

## Resource policy
Routine: docs/simple processing/small edits. Moderate: GTFS/SQL/API/UI/integration. Complex: routing/reconciliation/architecture/hard debugging. Use efficient settings where selectable; escalate for complexity or demonstrated failures. If switching is unavailable, say so and recommend appropriate reasoning before unusually expensive work. Never claim a setting change without control. Prefer included allowance; purchased credits only under account settings. Do not buy credits, enable reloads or alter limits. Keep DECISIONS.md with major decisions, failed approaches and completed work. Correctness takes priority over usage savings.

## Git workflow
The authorized project repository is private `softnessasastrength/transfer-issues`. Preserve files and inspect status/remotes/history first. Never replace unrelated remote work or force-push main. Use feature branches, focused commits and pushed work for substantial changes. Open PRs with tests and known limitations; do not automatically merge significant PRs. Low-risk documentation commits may go directly to main if rules permit. Review staged changes for secrets, personal records and oversized/generated files. Keep downloaded feeds, PDFs, SQLite, caches, artifacts and credentials out of Git. At session start, inspect repository rules as well as these instructions.

## Multi-agent handoff and directory instructions

Read `docs/agents/README.md` for the project mission, architecture, scope, quality gates and handoff template. Read the nearest directory `AGENTS.md` before editing `web/`, `android/`, `ios/`, `scripts/` or `tests/`. The user's current product vision is a map-first, offline-first regional transit explorer (conceptually "trains.fyi for regional transit", **not** a clone); see `docs/launch/product-vision.md`. Explore and Travel are equally important.

The CT + PVTA offline proof of concept and Android/iOS skeletons are authorized work in progress, **not completed offline applications**. Verify source data and actual code rather than relying on stale historical roadmap entries. Keep agent instructions and handoffs updated as architecture changes. Do not publish, merge, claim device tests or certify full coverage without evidence.

## Offline capability outranks storage size

Read `docs/architecture/offline-storage-policy.md` before proposing data packaging, maps, routing, caching or download changes. The owner explicitly accepts multi-gigabyte local datasets. Do not trade away airplane-mode functionality, detail or coverage to reduce storage footprint. Internet is optional for core operation; no arbitrary app-imposed pack size limit, and no silent pruning of user-selected regions. Verify real offline behavior rather than claiming that a local database alone constitutes a full offline app.

## User-controlled transit network installation

Read `docs/features/choose-transit-network.md` before implementing onboarding, downloads, package manifests, updates, offline data management or agency discovery. The user selects agencies and explicitly approves initial downloads and any newly required coverage. Auto-update authorization applies only to installed selected networks and disclosed dependencies; never silently add another agency. Shared maps/routing dependencies require a transparent review. Do not claim PVTA or other feed coverage without verified data.
