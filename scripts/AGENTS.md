# Data ingestion and packaging agent instructions

Read root `AGENTS.md`, `docs/agents/README.md`, `ROADMAP.md`, and `ios/OFFLINE_POC.md`.

Scope: data import/export scripts and relevant tests. Official GTFS and authoritative structured timetables take precedence; PDF extraction must preserve provenance, dates, exceptions and review status. Never substitute outdated or third-party data as verified current service.

Offline packs must be deterministic where feasible, versioned, validated, checksum-recorded, non-destructive and explicitly partial when any required agency/feed is missing. Do not mutate the active `data/atlas.sqlite` when exporting a pack. Exclude generated packs and source ZIPs from Git. Ensure calendar and transfers remain coherent after filtering. Add synthetic tests and record source coverage/freshness.
