# Southern New England Transit Atlas

An independent, local-first transit exploration project for Connecticut, Massachusetts and Rhode Island, with priority attention to Hartford, Springfield, Enfield, Windsor Locks, Manchester, Holyoke, Chicopee, Westfield, New Haven and Worcester.

**Status: desktop proof of concept implemented; browser acceptance is blocked in the build environment. Not a completed or travel-ready atlas.** This repository preserves the work already underway. Read [ROADMAP.md](ROADMAP.md) for authoritative priorities and acceptance criteria, and [DECISIONS.md](DECISIONS.md) for implementation evidence and unresolved issues.

## What exists

- Original `prototype.html`: a standalone interactive **schematic**, not geographic routing or a timetable.
- Python standard-library GTFS importer and a generated local SQLite database, with feed metadata, checksums and basic validation reports.
- Separate database queries, an initial connection-scan router, and `/api/v1/` HTTP endpoints.
- Desktop controller for geographic route/stop browsing, timetables, outbound/return/latest/reachability searches, source cards, browser-local bookmarks/journal and JSON backups; Leaflet 1.9.4 is vendored.
- Authoritative roadmap and persistent agent/workflow instructions.

**Not yet implemented or accepted:** automatic/current-PDF source discovery, PDF-to-stop review tooling, unified PDF/GTFS activation and version rollback, complete source discovery, comprehensive validation, browser acceptance and macOS hardware checks. The first reviewed-PDF registry and non-routing normalized tables now exist; Apache/macOS production hosting, PWA, native iOS and the New Hampshire/intercity expansion remain later milestones.

For same-phone Android hosting in Termux, see [TERMUX.md](TERMUX.md). Device validation remains pending.

## Try the desktop proof of concept

On your Mac mini, use a checkout of the `feature/browser-proof-of-concept` branch and Python 3.11 or newer. In Terminal, inside this repository:

```bash
python3 --version
# First run only: downloads official feeds and creates the local database.
python3 scripts/prepare_data.py
# Subsequent launches reuse your existing database without downloads.
python3 scripts/run_local.py
```

Open **http://127.0.0.1:8000** in your desktop browser. Stop the server with Control-C. No Apache, Node, paid hosting or cloud backend is required to run it. This is a portable local launch procedure, not a verified macOS deployment package.

Start with **Browse routes → 905**, select a trip for its timetable, or click **Hartford** to zoom to published stops. For a rail example, choose **HARTFORD [hartford:6]** to **SPRINGFIELD [hartford:9]**. Pick a date within the downloaded feed's service period (see Data & sources); expired feeds may correctly yield no trips. The `2026-11-12` example was checked directly against the development database, not as a live service guarantee. Network access is needed for street tiles, but official shape/stop layers are local. Missing tiles show a visible notice.

To request a specific sequence such as **905 → 30** or **905 → 24**, open **Browse routes**, use **+ chain** on each loaded route in order, then return to **Plan a journey**. Reorder or remove chain chips before searching. Route numbers are feed-qualified because agencies reuse numbers; an unavailable route such as 24X will not be invented. The planner only accepts a published itinerary that follows the chain; it still applies scheduled transfer buffers and does not guarantee the real-world connection.

Bookmarks and journal entries are device/browser/origin-local; use **My discoveries → Export my data** before clearing browser storage or moving machines. Import appends entries to preserve existing records. No personal records are committed to Git.

A failed agency download can leave coverage incomplete. An empty result is not proof that no real journey exists. Reservation/seat availability and fares are not checked.

## Feed coverage at the checkpoint

| Feed | Local import | Scope / caveat |
|---|---|---|
| CTtransit | Successful | 184 routes; loaded service periods vary by division |
| CTrail / Hartford Line | Successful | 2 feed routes; planned schedule, not live arrivals |
| WRTA | Successful | 24 routes; exception-date calendars |
| Amtrak | Successful | Whole official feed: 64 routes / 645 stops / 2,461 trips; no geographic clip |
| MBTA | Successful locally after expanded rebuild | 366 selected routes / 113,694 trips / 7,604 stops across MBTA bus, subway/light rail and commuter rail; geographic clip and feed-published calendars apply |
| PVTA | Successful | 62 routes; service period 2026-11-02 to 2026-12-19 in the 2026-11-14 import. Earlier HTTP 403s were a User-Agent artifact in the downloader, fixed 2026-11-14 |
| RIPTA / other CT, MA, RI agencies | **Not imported** | Required expanded coverage remains pending |

These are initial import counts, not proof of full correctness or current service. Downloaded GTFS, generated SQLite and validation reports are **not committed**. Re-run ingestion to produce local data. No schedules from unofficial or historical sources have been substituted for missing current feeds.

## Architecture

```text
Official GTFS ZIP -> import_gtfs.py -> local SQLite
                                    |
                              database.py
                                    |
                               routing.py
                                    |
                          server.py /api/v1/
                                    |
                        web/ (desktop controller)
```

- `import_gtfs.py`: CSV/ZIP parsing, calendar and exception normalization, basic validation.
- `database.py`: read-only SQLite access, active service calculation, connections and timetables.
- `routing.py`: earliest arrival, geographic transfer estimates, latest-start search.
- `server.py`: development HTTP server and versioned JSON endpoints; see [API.md](API.md).
- `config/feeds.json`: checked-in official source URLs; no generated feed content or secrets.
- `config/coverage.json`: explicit per-feed geographic and route/agency selection policy; MBTA is no longer hard-coded to rail-only.
- `data/`: ignored raw archives, source metadata, validation output and normalized SQLite.
- `tests/`: isolated synthetic unit tests; these do not establish full transit correctness.

The server defaults to loopback. Apache/macOS production deployment, launchd, PWA/offline support and native iOS remain deferred until explicitly authorized. The core uses no cloud runtime or paid services.

## Local development

Requires Python 3.11+ and an internet connection for initial official feed downloads. The backend uses only the standard library. Work from the repository root:

```bash
python3 scripts/prepare_data.py
python3 -m unittest discover -s tests -v
python3 server.py
# From a normal terminal, start and test the server automatically:
python3 scripts/external_smoke.py
# Add --routing to exercise a Hartford scheduled query as well.
```

The server warms its stop network and selected service-day connection list
before accepting requests. Set `ATLAS_DATE=YYYY-MM-DD` to select a date;
otherwise startup uses today's date. Both remain cached in the server process.

The first command seeds `data/sources.json` only if missing, downloads feeds and rebuilds `data/atlas.sqlite`. Downloads may be blocked by agency websites. It does not create recurring jobs. **The current refresh implementation overwrites local archives and database rather than retaining audit versions. Back up `data/` before refreshing an existing installation; versioned refresh/rollback is an open core requirement.** Stop the server before rebuilding because its connection cache is process-local.

Open `http://127.0.0.1:8000/api/v1/meta` to inspect the API. The page at `/` is the desktop proof of concept. Open `prototype.html` directly for the original schematic only.

For an existing database, the server accepts `ATLAS_DATA_DIR=/absolute/data/path`; the importer currently writes to the repository's `data/` folder. Do not expose this development server on an unsecured remote interface.

The core planner excludes optional networks by default. To download and import the optional MTA LIRR feed, run `python3 scripts/prepare_data.py --include-optional`; then use the planner's **Include optional MTA rail network** control. The feed is official scheduled data, not live service.

### Expanding the atlas

The importer is feed-configured. Add an agency to `config/feeds.json`, give it an official GTFS URL and `official_page`, then add only the coverage policy it needs in `config/coverage.json`: geographic `bounds` for a regional clip, `whole_network: true` for a compact network feed such as Amtrak, and optional `agency_ids` or `route_types` filters when the archive contains multiple operators. The schema and routing engine do not need a new agency-specific branch. Run `python3 scripts/prepare_data.py` (or `--include-optional`) and inspect `data/validation.json` before treating the network as loaded.

### Optional live bus/train overlays

`GET /api/v1/live?provider=mbta&route=mbta:Red&stop=place-pktrm` queries the official MBTA V3 JSON API; `provider=cttransit` queries CTtransit's official JSON realtime feeds. These are informational overlays, not replacements for the published timetable: provider failures and unverified agencies return `status: "unknown"`, and live data never changes route feasibility. Set `MBTA_API_KEY` if you have one; the MBTA portal says keys are optional for experimentation. PVTA remains schedule-only until its public realtime feed contract is available.

Percival/MCP clients can call the same overlay through `atlas_live_status`. That makes a buses-first, trains.fyi-like product direction possible without mixing realtime claims into the schedule planner: add verified agency adapters one at a time, then build freshness, vehicle map, alert, and stop-board views on this contract.

For one terminal control panel, run `./scripts/atlas_tui.py`. It starts/stops the web app, prepares core or optional feeds, runs the smoke test, runs tests, shows feed status, checks Atlas/Ollama health, starts Ollama when needed, and launches **Percival**, the local transit companion. Its canonical character file is mirrored in [`personality.md`](personality.md) from the [`softnessasastrength/percival`](https://github.com/softnessasastrength/percival) repository.

On a Chromebook/Linux shell, the shortest local-AI flow is:

```bash
./scripts/atlas_tui.py
# press s: Start stack
# press c: Chat with Percival
# press a: Advanced controls
```

The default TUI is intentionally small: `s` starts Atlas and Ollama, `c`
opens Percival, `r` refreshes health, `a` opens engineering controls, and `q`
quits. Use `python3 scripts/atlas_tui.py --advanced` to go straight to the
full menu.

For a trusted Chromebook-to-phone setup, run the combined launcher explicitly
in LAN mode:

```bash
python3 scripts/percival_lan.py --lan
```

Open `http://<chromebook-lan-address>:8000` on the phone. Open WebUI can use
`http://<chromebook-lan-address>:8765/mcp`. LAN mode has no authentication;
use it only on a private network and stop it with Control-C when finished.

The same TUI is portable to Windows. Install Python 3.11+ and Ollama, make
sure both `python` and `ollama` are on PATH, then from PowerShell run:

```powershell
python scripts\atlas_tui.py
```

Choose **Start Percival stack**, then **Chat with Percival**. Windows uses the
same loopback ports (`8000` for Atlas and `11434` for Ollama); no Bash, WSL or
Unix permissions are required.

### MCP connector for local clankers

The repository includes a dependency-free MCP stdio server at
`scripts/atlas_mcp.py`. It lets an MCP-capable Ollama client or local agent
search stops, inspect coverage, list departures, calculate supported fares and
plan scheduled trips. It does not fetch live arrivals and it does not start
the web server for you.

In one terminal, start the Atlas API:

```bash
python3 scripts/run_local.py
```

Configure the MCP-capable client with this server command:

```json
{
  "mcpServers": {
    "transit-atlas": {
      "command": "python3",
      "args": ["/absolute/path/to/transfer-issues/scripts/atlas_mcp.py"],
      "env": {"ATLAS_URL": "http://127.0.0.1:8000"}
    }
  }
}
```

Ollama by itself is a model runner; the host must support MCP stdio. The
connector remains local, requires no credentials, and requires the Atlas HTTP
server to be running. Change `ATLAS_URL` for another local port.

If you only have the Ollama CLI, use the included bridge to supply the MCP
host:

```bash
python3 scripts/ollama_mcp_chat.py --model qwen3:1.7b
```

It requires Ollama (`ollama serve`, usually already running) and the Atlas
server (`python3 scripts/run_local.py`). For a one-shot prompt, append it to
the command. The bridge defaults to Qwen3 non-thinking mode for faster tool
calls; add `--think` when you want slower, deeper reasoning. The bridge tells
the model to resolve stop codes through Atlas before planning, and to ask for
a missing departure time rather than inventing one. Numeric route prompts also
receive a deterministic Atlas route lookup before the model answers, reducing
small-model hallucinations such as inventing an agency or destination.

For LibreChat, the current stdio connector can be configured directly in
`librechat.yaml`:

```yaml
mcpServers:
  transit-atlas:
    type: stdio
    command: python3
    args:
      - /home/brandenalgo/transfer-issues/scripts/atlas_mcp.py
    env:
      ATLAS_URL: http://127.0.0.1:8000
```

For Open WebUI, run the loopback HTTP adapter in a separate terminal:

```bash
python3 scripts/atlas_mcp_http.py
```

Register `http://127.0.0.1:8765/mcp` as a Streamable HTTP MCP server. The
Atlas API still needs to be running on port 8000. If Open WebUI runs inside
Docker, `127.0.0.1` refers to the container; use the host gateway/address
that the container can reach and keep both services firewalled to your local
machine.

Open WebUI validation checklist:

```bash
python3 scripts/run_local.py
python3 scripts/atlas_mcp_http.py
```

Then add the MCP server in Open WebUI, enable its tools for the selected
model, and ask: `Use Atlas tools to identify route 905, then report its feed
and source status.` The expected result names the loaded CTtransit route and
does not invent an MTA destination. The HTTP adapter is local single-user
infrastructure; it has no authentication and must not be exposed publicly.

Percival's optional preferences are explicit and device-local. The MCP tools
`percival_set_preferences`, `percival_get_preferences`, and
`percival_clear_preferences` store only values the user supplies, such as a
home stop, default origin/host, walking mode, radius, and time windows. The
file is ignored under `data/percival_preferences.json`; nothing is inferred or
synced to GitHub.

Trip planning uses a 12-hour AM/PM clock in the browser (`8:00 AM`, `11:59 PM`) while the API continues to use service-day seconds. This is schedule planning only; no recurring reminders or background jobs are configured.

## Important calculation limits

- Scheduled feasibility only; no real-time cancellations, alerts or delays.
- Ground links are straight-line distance × 1.3 at 4.5 km/h walking or 12 km/h scooter. They are not verified street paths, safe crossings, slopes, accessibility or scooter-carry permissions.
- The transfer radius applies per link, not to total journey distance or battery range.
- GTFS route/trip-scoped transfer constraints are not yet modeled. Parent-station handling, zero-duration connections and other edge cases require broader testing.
- Frequency trips and trips with invalid/missing times are excluded, not interpolated.
- Prior-day 24+ hour service and next-day connections are modeled, but midnight/DST and multi-agency correctness require further acceptance tests.
- Latest-start search has one-minute resolution and is bounded by the selected deadline and loaded feeds.
- The current importer is **not** a full GTFS specification validator. Unified provenance, conflicting publications, version rollback and reviewed PDF activation gates are still pending.

## Development workflow

Read [AGENTS.md](AGENTS.md), [ROADMAP.md](ROADMAP.md) and repository rules before starting. For substantial changes:

```bash
git fetch origin
git switch main
git pull --ff-only
git switch -c feature/descriptive-name
# implement and validate focused changes
git add <specific-files>
git diff --cached
git commit -m "Describe the verified change"
git push -u origin feature/descriptive-name
```

Open a pull request with tests and known limitations. Do not merge significant PRs automatically. Never force-push main or rewrite remote history. Keep the roadmap synchronized; deferred work requires explicit authorization. Small documentation fixes may be committed directly if repository rules permit.

Local CLI authentication is separate from the ChatGPT GitHub connection. At initialization the connector had repository write access, while `gh auth status` reported no authenticated hosts and direct Git HTTPS access could not obtain a username. Use your approved GitHub authentication method locally; never put credentials in source, remote URLs or chat.

## Third-party assets

Leaflet 1.9.4 is Copyright (c) 2010–2023 Volodymyr Agafonkin and 2010–2011 CloudMade, distributed under BSD-2-Clause; see `web/vendor/LEAFLET-LICENSE`. Transit data remains subject to the respective publishers' terms and is not relicensed by this project.
