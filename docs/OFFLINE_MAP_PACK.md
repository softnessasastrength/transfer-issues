# Offline map packs (spike)

The Atlas's transit data has always been local; the street map underneath
it was not — the default base layer streams raster tiles from
tile.openstreetmap.org. This spike proves the base map can go fully local
for the owner's home region, and measures what that costs.

## The pack

- **Format:** PMTiles (single-file vector tile archive), OpenMapTiles schema.
- **Region:** Greater Springfield–Hartford — bounding box
  `-72.75, 41.68, -72.42, 42.18` (west, south, east, north), covering
  Springfield MA, Enfield, Windsor Locks, Hartford and Manchester CT with
  margin.
- **Zooms:** z8–z16. **Measured size: 64,943,623 bytes (~62 MiB)** for
  the full two-state build (planetiler run of 2026-11-15, 18m25s in the
  sandbox) — comfortably under the ~250 MB threshold that would have
  raised the z15-cap question, so no capped variant was needed. (An
  earlier Massachusetts-only intermediate measured 22,354,167 bytes;
  that is what a single-state pack costs, for reference.) The pack is
  data, not code, and is never committed to git.
- **Sources:** Geofabrik `connecticut-latest.osm.pbf` +
  `massachusetts-latest.osm.pbf` (downloaded 2026-11-15), Natural Earth,
  OSM water polygons, OSM lake centerlines.
- **Tool:** planetiler v0.10.2 (OpenMapTiles profile), jar SHA-256 pinned
  in the build script.

## Build recipe

`scripts/build_map_pack.sh [DATA_DIR]` — operator-run, downloads ~1.5 GB
of sources, runs planetiler, installs `packs/springfield-hartford.pmtiles`
plus a `packs.json` manifest into the data directory. **The Atlas never
downloads a pack by itself**; packs exist only because someone ran the
script (or an equivalent documented recipe) on purpose.

## Serving and rendering

- `GET /api/v1/packs` lists installed packs (name, region, size, source)
  from `DATA/packs/` + `packs.json`; the Sources page shows them.
- `GET /packs/<file>.pmtiles` serves a pack with HTTP Range support
  (206/Content-Range, suffix and open-ended ranges, 416) — PMTiles readers
  fetch byte ranges and Python's SimpleHTTPRequestHandler cannot, so the
  handler implements the minimum for this path only. Filenames are plain
  basenames; traversal is rejected.
- The web app gains a **Base map** switch (Online / Local pack) in the map
  controls. The Local option is disabled until a pack is installed. The
  local layer is rendered by vendored **protomaps-leaflet 3.0.1**
  (BSD-3-Clause; renders vector tiles to canvas with the vendored
  Leaflet), with a compact set of paint rules for the OpenMapTiles schema
  (water, waterways, landcover, landuse, buildings, roads). When the local
  pack is active the map attribution reads
  **© OpenStreetMap contributors (ODbL) · Local offline pack**.

## Limitations of the spike

- **No text labels** on the local layer yet: protomaps label rules need
  glyph fonts, which are a separate offline-packaging question. Stop and
  route overlays (the Atlas's own layers) carry the names that matter for
  planning. Follow-on: bundle a font with the pack or accept label-free.
- **One pack, one region.** The switch uses the first installed pack.
- **No in-app download manager.** Wiring pack downloads through the
  existing allowlisted `lan_server` pack mechanism is the named follow-on
  job; this spike stops at listing + switch, deliberately. Downloads stay
  user-approved, always.
- **WP10/EdgeHTML is not claimed.** Canvas vector rendering may or may not
  work in EdgeHTML; the emulator run decides. The documented fallback for
  WP10 is a capped-zoom (z15) **raster** pack rendered from the same data.

## Licences

- Map data © OpenStreetMap contributors, ODbL 1.0.
- planetiler: Apache-2.0. protomaps-leaflet and the PMTiles format:
  BSD-3-Clause (Protomaps). Leaflet: BSD-2-Clause (see web/vendor).
