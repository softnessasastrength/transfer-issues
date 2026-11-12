# Termux phone-only Transit Atlas development

Owner authorized three stages in **separate draft PRs**, with no merge.

## Stage 1: local backend and offline pack installation (this PR)

The debug Android client already accepts a user-entered HTTP server origin and the existing server supports `/api/v1/packs/catalog` and `/api/v1/packs/download/<agency>`. Android debug manifest allows development HTTP traffic. Termux shares Android's loopback interface, so the phone can serve its own data without a Mac mini.

1. Install Termux from its supported distribution, then `pkg update && pkg install python git sqlite`.
2. Clone the private repository using your own GitHub SSH credentials; do not paste credentials into chat. Check out this branch.
3. From repo root, run `bash termux-atlas.sh prepare` while online. This invokes existing official-first ingestion and can take time; check output for missing feeds. If `data/atlas.sqlite` already exists, skip preparation.
4. Run `bash termux-atlas.sh serve` in Termux. This exports only available agency packs and starts the unauthenticated dev server bound to **127.0.0.1:8000**. Keep Termux running.
5. In a second Termux session, run `bash termux-atlas.sh check`. Confirm the catalog reports actual available/missing agencies.
6. In the installed **debug** APK, enter `http://127.0.0.1:8000`, check only networks you want, tap **Review selected downloads**, verify the offered byte count, and explicitly confirm. The Android app validates each pack's byte count, SHA-256 and SQLite integrity before activation.
7. Open native journey planner; search stops. After successful installation, stop the Termux server, enable airplane mode and reopen the native planner to test the offline data path.

Do not expose the Termux server to LAN or internet: no authentication or trusted manifest signatures. Never use public port forwarding. Do not install unverified agency data; no data is bundled. The catalog may have zero available agencies. Do not assume physical device success before user reports it. Android may reject localhost cleartext if debug manifest/network policy changes.

## Stage 2: GTFS acquisition and packaging

Next separate draft PR: inspect `scripts/prepare_data.py` and official source registry; implement explicit source-selection, freshness/coverage reporting, resumable or retryable import as justified, and a deterministic end-to-end fixture test from GTFS ZIP to verified Android-compatible catalog. Preserve source provenance and user-approved agency selection. Do not auto-download or auto-install extra networks.

## Stage 3: Termux development and debugging

Next separate draft PR: optional developer bootstrap, Python tests, Git status checks, wireless ADB logcat capture and crash triage, with opt-in Android debugging and privacy-preserving log handling. Prefer GitHub Actions for APK builds; do not commit signing keys or personal logs.

## Acceptance and limitations

Stage 1 source-level tests: `python3 -m unittest tests.test_termux_entrypoint tests.test_lan_packs -v`; `bash -n termux-atlas.sh`. Live GTFS import, Termux startup, Android HTTP access, and physical device airplane-mode routing require manual checks and are **not yet verified**. The planner has no licensed offline street basemap; GTFS service availability is not real-time data.
