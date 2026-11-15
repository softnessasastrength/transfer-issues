# Chromebook Crostini development environment

**Status:** development bootstrap, not a claim of physical Chromebook or Android-device testing. ChromeOS Linux (Crostini) uses a Debian container and can run the Python backend, SQLite data preparation, tests, Git and optional Android build tooling.

## First-time setup

1. ChromeOS **Settings → Developers → Linux development environment → Turn on** (menu wording may vary). Allocate enough disk space for regional GTFS, Android SDK and build caches. Keep source inside the Linux home directory, not `/mnt/chromeos`, for better filesystem behavior.
2. In the Linux terminal:
   ```bash
   sudo apt update
   sudo apt install -y git python3 python3-venv python3-pip sqlite3 openjdk-17-jdk curl unzip adb
   ```
3. Authenticate to private GitHub using SSH or GitHub CLI, without storing tokens in source files. Clone `git@github.com:softnessasastrength/transfer-issues.git`. Check out `feature/crostini-chromebook-dev` for this draft PR.
4. Run `bash crostini-dev.sh doctor`, then `bash crostini-dev.sh test`. Tests are local and use synthetic fixtures.
5. To prepare real official-first feeds, run `bash atlas.sh` while online. The first import can take time and may lack agencies. Afterward `bash crostini-dev.sh serve` runs the browser backend on the Linux container's loopback interface. ChromeOS Chrome often forwards Crostini localhost ports; test `http://localhost:8000` in Chrome. The Android phone cannot use the container's `127.0.0.1` directly.
6. `bash crostini-dev.sh packs` exports and verifies Android-compatible agency packs when the Termux Stage 2 validator is present. **Dependency:** PR #35 introduces `scripts/verify_lan_catalog.py`; until it is integrated, use `python3 scripts/build_lan_packs.py` and check its output manually. Do not mistake an absent validator for an invalid feed.

## Optional local Android build

The repo's Android CI uses **JDK 17, Android SDK 35, build-tools 35.0.0 and Gradle 8.9**. Crostini's Debian `apt gradle` may be too old. Install a trusted Gradle 8.9 distribution and SDK command-line tools separately, accept SDK licenses, and set `ANDROID_HOME`. Then `bash crostini-dev.sh android-test` and `bash crostini-dev.sh android-build` invoke the same Gradle tasks as CI. APK output: `android/app/build/outputs/apk/debug/app-debug.apk`. For lower-powered Chromebooks or limited storage, use GitHub Actions to build and download the APK instead.

## Device debugging

ChromeOS supports Android debugging through its own settings and, on supported devices, ADB connectivity. `bash crostini-dev.sh adb-devices` only lists devices; it does not enable debugging or pair devices. For a separate Android phone, use its developer settings and explicitly pair/connect over a trusted network if supported. ChromeOS/Crostini USB passthrough and Android subsystem access vary by model and ChromeOS version. Never disable Play Protect, expose ADB to the internet, or paste private log output publicly.

## Security and offline boundaries

The script never starts services automatically, downloads agencies silently, merges PRs, installs packages, or exposes a LAN listener. User selection and Android pack confirmation remain explicit. ChromeOS browser localhost forwarding is for development; the app's phone-only Termux loopback path is separate. No live timetable coverage, Chromebook build success, or device installation is claimed.
