# Crostini reconciliation — 2026-11-13

## Source and target
- Source: PR #37, `feature/crostini-chromebook-dev` at `3dc017740299f22d04341d774d7a72a0e44c46da`.
- Target: current `main`, with existing Termux and Android work preserved.
- The original PR diverged from `main` and was non-mergeable.
- This replacement branch is created from current `main`; it copies the three Crostini-specific files verbatim, rather than overwriting shared `ROADMAP.md` or `DECISIONS.md` with stale versions.

## Files preserved
- `crostini-dev.sh`: opt-in developer commands, local backend, test runner, pack export, optional Gradle and ADB inspection.
- `docs/development/chromebook-crostini.md`: setup and safety guidance.
- `tests/test_crostini_dev.py`: synthetic CLI and safety tests.

## Merge and acceptance constraints
- No modification to existing Termux TUI or Android code.
- No automatic downloads, network exposure, Android pairing or signing.
- CI on this **new** branch must be checked separately. Prior PR #37 CI success is not proof for the replacement.
- Execute on real Chromebook and verify Android SDK/Gradle only when hardware is available.
- No merge without explicit owner approval.
