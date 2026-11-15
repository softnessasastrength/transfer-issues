#!/usr/bin/env bash
# Build the Greater Springfield–Hartford offline base-map pack (PMTiles,
# OpenMapTiles schema) and install it into the Atlas data directory.
#
# OPERATOR-RUN ONLY. This script downloads ~1.5 GB of source data
# (Geofabrik state extracts, Natural Earth, OSM water polygons, the
# planetiler jar). The Atlas itself never downloads a pack: a pack exists
# only because someone ran this script on purpose. There is no background
# or silent fetching anywhere in the pack system.
#
# Requirements: curl, a JRE 21+ (java), osmium-tool, ~4 GB free disk,
# ~15 minutes.
# Usage: scripts/build_map_pack.sh [DATA_DIR]
#   DATA_DIR defaults to $ATLAS_DATA_DIR, else ./data (same rule as the app).
# The pack lands in DATA_DIR/packs/ with a packs.json manifest the server
# reads for the "Offline map packs" listing. Safe to re-run: downloads are
# skipped when the local file already has the expected size class, and the
# installed pack is replaced atomically at the end.
set -euo pipefail

PLANETILER_VERSION="0.10.2"
PLANETILER_SHA256="f310bd0413e2e4512b27f4046d418664e8e1d3bf31603c2a70e23de06c167e4d"
# Greater Springfield–Hartford: Springfield MA, Enfield, Windsor Locks,
# Hartford, Manchester CT, with margin. Format: west,south,east,north.
BBOX="-72.75,41.68,-72.42,42.18"
MINZOOM=8
MAXZOOM=16
PACK_ID="springfield-hartford.pmtiles"

DATA_DIR="${1:-${ATLAS_DATA_DIR:-./data}}"
BUILD_DIR="${MAP_PACK_BUILD_DIR:-./map-pack-build}"
mkdir -p "$BUILD_DIR/data/sources" "$DATA_DIR/packs"
cd "$BUILD_DIR"

fetch() { # fetch URL DEST — skip when a non-trivial file already exists
  if [ ! -s "$2" ]; then echo "Downloading $1"; curl -fSL --retry 3 -o "$2" "$1"; fi
}

fetch "https://github.com/onthegomap/planetiler/releases/download/v$PLANETILER_VERSION/planetiler.jar" planetiler.jar
echo "$PLANETILER_SHA256  planetiler.jar" | sha256sum -c -

# Geofabrik extracts are verified against their published MD5s: a
# truncated download once passed curl silently and produced hours of
# misleading planetiler failures downstream. Never skip this check.
fetch_osm() { # fetch_osm STATE — download (or re-download) until md5 verifies
  local url="https://download.geofabrik.de/north-america/us/$1-latest.osm.pbf"
  local expected
  expected=$(curl -fsSL "$url.md5" | awk '{print $1}')
  for attempt in 1 2 3; do
    if [ -s "$1.osm.pbf" ] && [ "$(md5sum "$1.osm.pbf" | awk '{print $1}')" = "$expected" ]; then return 0; fi
    echo "Downloading $url (attempt $attempt)"
    curl -fSL --retry 3 -o "$1.osm.pbf" "$url"
  done
  [ "$(md5sum "$1.osm.pbf" | awk '{print $1}')" = "$expected" ] || { echo "MD5 mismatch for $1.osm.pbf after retries" >&2; exit 1; }
}
fetch_osm connecticut
fetch_osm massachusetts
# planetiler's auxiliary sources, pre-fetched so the java step needs no
# network of its own (its downloader is only used with --download).
fetch "https://naciscdn.org/naturalearth/packages/natural_earth_vector.sqlite.zip" data/sources/natural_earth_vector.sqlite.zip
fetch "https://osmdata.openstreetmap.de/download/water-polygons-split-3857.zip" data/sources/water-polygons-split-3857.zip
fetch "https://github.com/acalcutt/osm-lakelines/releases/download/v12/lake_centerline.shp.zip" data/sources/lake_centerline.shp.zip

# planetiler 0.10.x silently honours only the LAST --osm-path, so the two
# state extracts are merged into one sorted PBF first (osmium merge;
# osmium-tool is a build requirement alongside the JRE). A naive byte
# concatenation is NOT equivalent: PBF elements must stay globally
# sorted (nodes, then ways, then relations).
osmium merge connecticut.osm.pbf massachusetts.osm.pbf -o ct-ma-sorted.osm.pbf --overwrite
java -Xmx4g -jar planetiler.jar \
  --osm-path=ct-ma-sorted.osm.pbf \
  --bounds="$BBOX" --minzoom="$MINZOOM" --maxzoom="$MAXZOOM" \
  --output="$PACK_ID" --force

SIZE=$(stat -c%s "$PACK_ID")
cp "$PACK_ID" "$DATA_DIR/packs/$PACK_ID.tmp"
mv "$DATA_DIR/packs/$PACK_ID.tmp" "$DATA_DIR/packs/$PACK_ID"
cat > "$DATA_DIR/packs/packs.json" <<JSON
{"packs": {"$PACK_ID": {"name": "Greater Springfield–Hartford", "region": "Springfield MA · Enfield · Windsor Locks · Hartford · Manchester CT", "source": "© OpenStreetMap contributors (ODbL) · Geofabrik extracts · planetiler/OpenMapTiles"}}}
JSON
echo "Installed $DATA_DIR/packs/$PACK_ID ($SIZE bytes, z$MINZOOM–z$MAXZOOM, bbox $BBOX)"
echo "Attribution: map data © OpenStreetMap contributors, available under the ODbL."
