# Mac mini ↔ Android LAN proof of concept

**Status:** experimental code, not yet compiled or tested on Android hardware. No cloud account or remote hosting required.

## Start on the Mac mini

1. Check out the stacked feature branch `feature/lan-android-offline-poc`. Install Python 3.11+.
2. Ensure `data/atlas.sqlite` contains already-imported authoritative GTFS. If absent, use `bash atlas.sh` once to import (initial feed downloads require internet).
3. Run `bash atlas-lan.sh`. It builds per-agency local SQLite packs and starts the Python HTTP server on port 8000.
4. Get the Mac mini's **private LAN IP** from macOS network settings (for example `192.168.1.10`), not its public IP. Phone and Mac must be on the same trusted Wi-Fi, with client isolation disabled and firewall allowing inbound TCP 8000.
5. In Android Studio, open `android/`, sync with JDK 17 / SDK 35, build the **debug** variant, and install on your phone. Enter `http://MAC-LAN-IP:8000` in the app.
6. Select CTtransit, CTrail Hartford Line (`hartford`), PVTA and/or Amtrak; tap **Review selected downloads**. Review actual byte count and missing agency list, then confirm. Only available selected packs are downloaded. PVTA may be missing.
7. Tap **Open Mac mini atlas (LAN)** to use the existing browser map and server-side journey planner from your phone.
8. Tap **Explore installed offline map** to display locally installed GTFS route shapes and stops. Turn on airplane mode to verify that this **native geographic preview** still renders; the LAN browser planner will not.

`atlas-lan.sh` intentionally listens on `0.0.0.0`, meaning all Mac network interfaces. This is an **unauthenticated development server**: never forward port 8000, expose it to the internet, or run it on an untrusted network. The launcher doesn't open the firewall or configure startup jobs. Ctrl+C stops it. Normal `atlas.sh` remains loopback-only.

## Components

- `scripts/build_lan_packs.py`: per-agency SQLite exporter from existing GTFS, provenance-preserving IDs, no fake feeds, checksums and manifest.
- `lan_server.py`: existing Atlas web UI/API plus `GET /api/v1/packs/catalog` and `GET /api/v1/packs/download/{cttransit|hartford|pvta|amtrak}`. Server never starts a download on the phone.
- `android/MainActivity.kt`: native selection/review/verified download; embedded WebView for LAN backend; native offline route-shape-and-stop geographic preview.
- Debug-only cleartext HTTP permission; release variant retains the original cleartext prohibition.
- Existing `offline_packages.py`: local Python package-manager backend remains separate and available for test harnesses.

## Honest limitations

- **No offline street basemap or pedestrian/cycling graph yet.** The native offline map is a rough coordinate plot of official GTFS shapes/stops, not a full street map, interactive tiled map or street-aware router.
- **No offline native journey planner yet.** The existing Python journey planner works over LAN from the Android WebView; it needs the Mac mini running. Offline phone mode only shows installed route geometry.
- Initial import, package refresh, and LAN pack downloads require connectivity to the Mac mini; once packs are installed the native preview does not.
- No signed package catalog or authenticated transport; HTTP LAN is vulnerable to malicious network peers even with checksums from the same server. Use only a trusted LAN; production needs signed manifests/HTTPS and stronger validation.
- Native Android currently stores separate agency SQLite files; no unified cross-agency local routing. It retains a previous file for rollback but lacks robust crash transaction journaling and download resume.
- Browser Leaflet base tiles may require internet; its route geometry still comes from the local Mac server. The native offline preview uses no tile provider.
- No Android emulator/device build, airplane-mode device test, performance profiling, or macOS live network test has been performed in this session.
- App defaults to four selected checkboxes as a **proposed choice**. No network calls occur until user taps Review. Auto-update policy is not yet scheduled or activated on Android.
- For real offline navigation, next work: licensed basemap packs, pedestrian graph, local route engine and device validation.

## Test commands

```bash
python3 -m unittest tests.test_lan_packs tests.test_offline_packages -v
python3 -m py_compile lan_server.py scripts/build_lan_packs.py offline_packages.py
```

Only synthetic tests. Do not mistake source inspection for executed tests.
