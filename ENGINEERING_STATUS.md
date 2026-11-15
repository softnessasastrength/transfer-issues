# Percival engineering checkpoint — 2026-11-15

## Evidence by maturity

- **Verified locally:** 95 Python tests pass, including HTTP handler, routing,
  Outings, and integrity fixtures. A loopback smoke verifies a scheduled
  Saturday Hartford Union Station → Berlin outing with a two-hour stay and a
  10 PM home deadline against the currently loaded database. The Outings
  browser smoke passes with synthetic API responses, including keyboard map
  selection and missing coverage. These are schedule checks, not live service.
- **Implemented, device untested:** the Android WebView shell and Metro Outings
  web interface. The iOS SwiftUI screen is on draft PR #73; no Xcode build or
  device run has been reported. Browser acceptance on this cloud desktop was
  blocked by the unavailable browser access host.
- **Partial:** PDF ingestion has a reviewed-manifest foundation but no active
  PDF routing. Outings candidate browsing evaluates a bounded subset and
  labels overflow incomplete. The local SQLite integrity checker detects
  dangling transfer endpoints in `data/atlas.sqlite`; a clean import has not
  yet passed it.
- **Planned or blocked:** versioned offline transit packs, authenticated LAN
  access, source activation/rollback, and production iOS/Windows Phone builds.
  PR #72 is Windows Phone toolchain research only. Windows Phone 8.1 device
  unlock/installation must be proven on hardware before client implementation.

## Independent engineering review

- Routing: partial route-chain labels could mask a complete journey. A staged
  state scan and adversarial tests fix this on draft PR #74.
- Interface: the Outings map now exposes status in text and keyboard focus.
  The top-level unknown response and next-day home deadline are handled. Draft
  PR #73's iOS Coverage tile and width-dependent tile sizing need review.
- Offline: draft PR #75 adds read-only database/catalog checks. The local
  database currently fails on transfer references to absent stops; this is a
  concrete import/coverage issue, not proof of corrupt timetable service.
- Quality/security: a one-second minimum-stay false positive was fixed in
  Outings with a regression. Failed searches are unknown when any listed feed
  is unavailable. The unauthenticated LAN MCP preference tools remain a
  high-priority security gap; do not expose that endpoint on untrusted networks.
- Legacy: PR #72's two Windows Phone toolchain paths are research. A minimal
  app install on the actual OS/hardware is the next evidence gate.

## Next sprint, in order

1. Fix dangling transfer references at import/coverage boundaries; rebuild
   and rerun `scripts/check_data_integrity.py` on a fresh database.
2. Protect LAN MCP with authentication and origin controls; add confirmation
   for preference clearing before broader device access.
3. Review the stacked routing/integrity/Outings draft PRs against current
   main, resolve conflicts, and run the browser/device acceptance checks.
4. Stabilize API provenance/expiry and PDF activation before native clients
   rely on v1. Keep offline packs behind integrity, version and rollback gates.
5. Prove iOS and Windows Phone toolchains on their required hardware before
   claiming compiled clients.

## Resume

Working branch: `feature/percival-outings`. Review draft PRs #74 and #75
first. Run `python3 -m unittest discover -s tests -v`,
`python3 scripts/external_smoke.py --outings --date 2026-11-14`, and the
Outings browser smoke in `tests/browser_outings.cjs` with the local server.
Inspect `git status --short --untracked-files=all` before staging; exclude
`android/.gradle`, downloaded data, databases, secrets and generated files.
No substantive PR has been merged.
