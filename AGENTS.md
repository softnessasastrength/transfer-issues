# Project instructions
Read ROADMAP.md at the start of every work session. It is the authoritative implementation plan. Preserve current priorities. Record new feature requests and dependencies there. Do not implement deferred milestones without explicit authorization. Verify acceptance criteria before changing status to complete. Never fabricate missing transit service or treat feed provenance as a live-service guarantee. Do not configure recurring tasks.

## ButlerGPT persona
When operating as ButlerGPT, read and apply `docs/agents/BUTLER_PERSONALITY.md` for tone and reporting style. This persona is subordinate to the engineering and safety requirements here and to explicit user instructions. Other assistants may use a neutral voice. Repository updates do not automatically configure an external ButlerGPT runtime; its startup must load repository instructions.

## Resource policy
Routine: docs/simple processing/small edits. Moderate: GTFS/SQL/API/UI/integration. Complex: routing/reconciliation/architecture/hard debugging. Use efficient settings where selectable; escalate for complexity or demonstrated failures. If switching is unavailable, say so and recommend appropriate reasoning before unusually expensive work. Never claim a setting change without control. Prefer included allowance; purchased credits only under account settings. Do not buy credits, enable reloads or alter limits. Keep DECISIONS.md with major decisions, failed approaches and completed work. Correctness takes priority over usage savings.

## Git workflow

The authorized project repository is private `softnessasastrength/transfer-issues`. Preserve files and inspect status/remotes/history first. Never replace unrelated remote work or force-push main.

### Branch model (adopted 2026-11-15)

The only long-lived branches are `main`, `dev`, and `sandbox`. Do not create other permanent branches.

- `main` — stable. The released, known-good state of the project and the source for release tags and packages. Nothing lands on `main` directly: work reaches it only by promotion from `dev` through a PR with green tests/checks, or by an explicit owner instruction (for example a hotfix, or a documentation rule change like this one). Never force-push `main`.
- `dev` — integration. Day-to-day work branches off `dev`, and pull requests target `dev` by default. `dev` should always build and pass the test suite; if it breaks, fixing it outranks new work.
- `sandbox` — experiments. Spikes, prototypes and throwaway explorations live here or on short-lived branches off it. `sandbox` may be messy and may fall behind; it is never merged wholesale into `dev` or `main`. Work that proves itself graduates through a clean, focused PR (or a fresh implementation) into `dev`, not by merging `sandbox` itself.

All other branches are temporary PR branches: one focused change per branch, named for the work (for example `fix/...`, `feat/...`, `docs/...`, `chore/...`), branched from `dev` (or from `sandbox` for experiments), and deleted when the PR merges. The repository auto-deletes head branches on merge; do not recreate merged branches. If you find a branch that is not `main`, `dev`, `sandbox`, or the head of an open PR, treat it as leftover: before removing it, check whether its commits are already in `main` or preserved under an `archive/` tag, and never delete a branch carrying unmerged, unarchived commits.

Use focused commits and pushed work for substantial changes. Open PRs with tests and known limitations; do not automatically merge significant PRs. Review staged changes for secrets, personal records and oversized/generated files. Keep downloaded feeds, PDFs, SQLite, caches, artifacts and credentials out of Git. At session start, inspect repository rules as well as these instructions.

## Multi-agent handoff and directory instructions

Read `docs/agents/README.md` for the project mission, architecture, scope, quality gates and handoff template. Read the nearest directory `AGENTS.md` before editing `web/`, `android/`, `ios/`, `scripts/` or `tests/`. The user's current product vision is a map-first, offline-first regional transit explorer (conceptually "trains.fyi for regional transit", **not** a clone); see `docs/launch/product-vision.md`. Explore and Travel are equally important.

The CT + PVTA offline proof of concept and Android/iOS skeletons are authorized work in progress, **not completed offline applications**. Verify source data and actual code rather than relying on stale historical roadmap entries. Keep agent instructions and handoffs updated as architecture changes. Do not publish, merge, claim device tests or certify full coverage without evidence.

## Offline capability outranks storage size

Read `docs/architecture/offline-storage-policy.md` before proposing data packaging, maps, routing, caching or download changes. The owner explicitly accepts multi-gigabyte local datasets. Do not trade away airplane-mode functionality, detail or coverage to reduce storage footprint. Internet is optional for core operation; no arbitrary app-imposed pack size limit, and no silent pruning of user-selected regions. Verify real offline behavior rather than claiming that a local database alone constitutes a full offline app.

## User-controlled transit network installation

Read `docs/features/choose-transit-network.md` before implementing onboarding, downloads, package manifests, updates, offline data management or agency discovery. The user selects agencies and explicitly approves initial downloads and any newly required coverage. Auto-update authorization applies only to installed selected networks and disclosed dependencies; never silently add another agency. Shared maps/routing dependencies require a transparent review. Do not claim PVTA or other feed coverage without verified data.
