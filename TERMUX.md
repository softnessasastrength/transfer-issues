# Run the atlas on an Android phone with Termux

The phone runs the existing Python/SQLite backend inside Termux. Chrome on the same phone opens its loopback URL. This reuses the desktop proof of concept and its existing responsive layout; it is not a native Android app or PWA. No root, Docker, Apache, Node or pip dependencies are required by the application.

Status: setup instructions prepared from official Termux/GitHub CLI documentation and inspected project code. Actual Android/Termux execution and phone browser acceptance remain unverified. The repository now also contains an early native Android WebView shell under `android/`; its APK build/device validation is still pending. Existing transit coverage and routing limitations still apply.

## 1. Prepare Termux

Use an installation supported by the [official Termux installation guide](https://github.com/termux/termux-app#installation). If Termux is already working, keep it; there is no need to uninstall it or change its source for this project.

Run in Termux:

```bash
pkg update
pkg upgrade
pkg install python git gh
python --version
python -c 'import sqlite3, ssl, zipfile; print("Python/SQLite/HTTPS ready")'
```

Python must be 3.11 or newer. Keep the checkout under Termux's own home directory, not Android's shared Downloads directory. Shared-storage permission is not required for this workflow.

## 2. Authenticate and obtain the private project

GitHub access in ChatGPT does not automatically authenticate Termux. Use the account with access to `softnessasastrength/transfer-issues`:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

Follow the displayed browser/device-code steps yourself. If a browser does not launch automatically, open the URL printed by `gh` in Chrome. Complete login before continuing; do not paste a token into chat or a clone URL.

For a new checkout:

```bash
cd ~
gh repo clone softnessasastrength/transfer-issues -- --branch feature/browser-proof-of-concept
cd transfer-issues
```

If you already have a checkout, do not clone over it. Inspect `git status`, then fetch and switch to `feature/browser-proof-of-concept` when your local changes allow it. The implementation is currently on this feature branch, not main; PR #1 remains unmerged.

## 3. Import feeds once, then start

On a new checkout without `data/atlas.sqlite`:

```bash
python scripts/prepare_data.py
```

Initial downloads and imports can take time, use substantial mobile data, and need space for archives plus SQLite. Use Wi-Fi for this first run if available. Agency download failures may leave incomplete coverage. (PVTA downloads successfully as of 2026-11-14; it previously returned HTTP 403 until the downloader sent an explicit User-Agent.) The current importer rebuilds data and does not retain rollback versions, so skip this command if you already have a database you want to preserve.

Check the backend and launch:

```bash
python -m unittest discover -s tests -v
python scripts/run_local.py
```

Leave that Termux session running. Switch to Chrome and enter exactly:

**http://127.0.0.1:8000**

Use HTTP, not HTTPS. This address refers to the same phone; it does not require your Mac mini to be running. The server stays on loopback rather than exposing itself to other devices.

For the first exploration, tap **Browse routes**, search **905**, and open a trip timetable. Or zoom into Hartford, tap published stop markers and choose start/destination stops. For a rail query, use `HARTFORD [hartford:6]` to `SPRINGFIELD [hartford:9]`. Choose a date inside the imported schedule period shown under **Data & sources**. If needed, turn the phone sideways for more room; dedicated mobile polish is still deferred.

### Use the Chromebook as Percival's LAN host

If the database and Ollama stay on the Chromebook, launch from the checkout:

```bash
python3 scripts/percival_lan.py --lan
```

Find the Chromebook's private LAN address, then open
`http://<chromebook-lan-address>:8000` on the phone. A local Open WebUI can
use `http://<chromebook-lan-address>:8765/mcp`. The MCP endpoint requires
the per-install bearer token (printed by the launcher at startup; stored
as `mcp_http_token` in the data dir): configure the client to send
`Authorization: Bearer <token>`. This is single-user development
infrastructure: keep both devices on a trusted
network and stop it after use. The phone does not need to run the Atlas
database or Ollama model in this arrangement.

## Later launches and stopping

```bash
cd ~/transfer-issues
python scripts/run_local.py
```

No feed download is needed for every launch. Stop the server with Control-C in Termux. Do not exit or force-stop Termux while using the atlas. Android may terminate background work, particularly during heavy imports; if the terminal reports signal 9 or Chrome stops connecting, check the Termux process before treating it as an application error. There is no automatic startup or recurring refresh.

## Data and troubleshooting

- `data/` contains imported schedules in the Termux checkout. Browser bookmarks and journal entries live separately in Chrome's storage for `http://127.0.0.1:8000`. Use **My discoveries → Export my data** to back them up. Keep using the same browser and URL; `localhost` and `127.0.0.1` have separate browser storage.
- **Connection refused:** check that the Termux command is still running and you used the exact HTTP address above.
- **Address already in use:** an earlier server may already be running. Try the page first; stop the earlier server before starting another.
- **Repository not found:** check `gh auth status` and the account's access to the private repository. Do not change repository visibility.
- **No imported database:** run first-time ingestion and read the final error if it fails. Repeated app launches do not download feeds automatically.
- **Missing street tiles:** transit stops and route shapes are local, but the street basemap needs internet. This is not an offline-map implementation.
- **No journey:** check source date ranges and missing agency coverage. A published timetable does not establish reservation availability or a guaranteed transfer.
- **Import interrupted:** the current importer retains an existing database until its replacement step, but downloaded archives/metadata may have changed. Avoid refreshing a valuable dataset without backing up the data directory first.

## Sources checked

- [Termux app and installation](https://github.com/termux/termux-app)
- [Termux package management](https://github.com/termux/termux-packages/wiki/Package-Management)
- [Official Termux package for GitHub CLI](https://github.com/termux/termux-packages/blob/master/packages/gh/build.sh)
- [GitHub CLI browser authentication](https://cli.github.com/manual/gh_auth_login)
