#!/bin/sh
# Build the transit-atlas Debian package from this repository checkout.
#
# Usage:
#   PERCIVAL_DIR=/path/to/percival packaging/build_deb.sh [VERSION]
#
# VERSION may also be supplied through the VERSION environment variable.
# With neither, the nearest git tag (vX.Y.Z) is used. The version is
# stamped into DEBIAN/control and into the launcher's `version` output;
# nothing else in the repo needs a manual bump to cut a release.
#
# PERCIVAL_DIR is REQUIRED: since 0.0.2 the package bundles Percival
# Core (softnessasastrength/percival) next to the Atlas. The tree at
# PERCIVAL_DIR must be a checkout of the ref pinned in
# packaging/PERCIVAL_PIN; it is staged whole under
# /usr/lib/percival-core with a BUILD_INFO recording the pin. A build
# without it would silently produce the wrong artifact, so the script
# refuses. The release workflow checks out the pinned ref itself.
#
# Output: dist/transit-atlas_<VERSION>_all.deb
#
# The layout reproduces the hand-built transit-atlas packages (0.0.1):
# the whole checkout under /usr/lib/transit-atlas with `data` symlinked
# to /var/lib/transit-atlas/data, the launcher at /usr/bin/transit-atlas,
# configuration at /etc/transit-atlas/percival.conf, systemd units for
# both services, and maintainer scripts that create the transit-atlas
# system user without any network I/O. The GTFS database is never
# bundled; it is built on the target machine by `transit-atlas prepare`.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

VERSION=${1:-${VERSION:-}}
if [ -z "$VERSION" ]; then
  if git -C "$REPO_ROOT" describe --tags --abbrev=0 >/dev/null 2>&1; then
    VERSION=$(git -C "$REPO_ROOT" describe --tags --abbrev=0)
  else
    echo "build_deb.sh: no version argument, no VERSION env, no git tag" >&2
    echo "usage: packaging/build_deb.sh X.Y.Z" >&2
    exit 1
  fi
fi
VERSION=${VERSION#v}
case "$VERSION" in
  ''|*[!0-9.]*)
    echo "build_deb.sh: suspicious version '$VERSION'" >&2
    exit 1
    ;;
esac

command -v dpkg-deb >/dev/null 2>&1 || {
  echo "build_deb.sh: dpkg-deb not found (install dpkg-dev)" >&2
  exit 1
}

# --- Percival Core input: the pinned second tree this package bundles.
PERCIVAL_PIN=$(grep -v '^#' "$SCRIPT_DIR/PERCIVAL_PIN" | tr -d '[:space:]')
case "$PERCIVAL_PIN" in
  ''|*[!0-9a-f]*)
    echo "build_deb.sh: packaging/PERCIVAL_PIN does not hold a commit SHA" >&2
    exit 1
    ;;
esac
PERCIVAL_DIR=${PERCIVAL_DIR:-}
if [ -z "$PERCIVAL_DIR" ]; then
  echo "build_deb.sh: PERCIVAL_DIR is not set" >&2
  echo "  The bundle needs a checkout of softnessasastrength/percival at" >&2
  echo "  the ref pinned in packaging/PERCIVAL_PIN ($PERCIVAL_PIN), e.g." >&2
  echo "  PERCIVAL_DIR=/path/to/percival packaging/build_deb.sh $VERSION" >&2
  exit 1
fi
if [ ! -f "$PERCIVAL_DIR/scripts/run_local.py" ] || [ ! -d "$PERCIVAL_DIR/src/percival_core" ]; then
  echo "build_deb.sh: PERCIVAL_DIR ($PERCIVAL_DIR) does not look like a" >&2
  echo "  Percival Core checkout (scripts/run_local.py / src/percival_core missing)" >&2
  exit 1
fi

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT INT TERM
APP="$STAGE/usr/lib/transit-atlas"
mkdir -p "$APP" "$STAGE/DEBIAN"

# --- Application tree: the whole checkout, as in the hand build.
# tar is used so dotfiles (.github/, .gitignore, ...) come along.
# Excluded: VCS metadata, this script's own output directory, Python
# bytecode caches, any local data/ directory (replaced by the
# /var/lib symlink below), and ./percival-input — the release
# workflow's checkout of the Percival input tree, which is staged
# separately under /usr/lib/percival-core and must not be swallowed
# into the Atlas tree as well.
( cd "$REPO_ROOT" && tar -cf - \
    --exclude='./.git' \
    --exclude='./dist' \
    --exclude='./data' \
    --exclude='./percival-input' \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    . ) | ( cd "$APP" && tar -xf - )

# import_gtfs.py resolves ./data relative to the app tree while the rest
# of the stack honours ATLAS_DATA_DIR; the package bridges the two with
# a symlink into the state directory (as the hand build did).
ln -s /var/lib/transit-atlas/data "$APP/data"

# --- Percival Core tree: the whole pinned checkout, as with the Atlas.
# Excluded: VCS metadata and Python bytecode caches. BUILD_INFO records
# exactly which Percival the package carries.
PC="$STAGE/usr/lib/percival-core"
mkdir -p "$PC"
( cd "$PERCIVAL_DIR" && tar -cf - \
    --exclude='./.git' \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    . ) | ( cd "$PC" && tar -xf - )
{
  echo "repo: softnessasastrength/percival"
  echo "ref: $PERCIVAL_PIN"
  echo "package: transit-atlas $VERSION"
  echo "built: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$PC/BUILD_INFO"

# --- Packaging overlay: launcher, systemd units, config, docs.
mkdir -p "$STAGE/usr/bin" \
         "$STAGE/lib/systemd/system" \
         "$STAGE/etc/transit-atlas" \
         "$STAGE/usr/share/doc/transit-atlas"
sed -e "s/@VERSION@/$VERSION/g" \
    -e "s/@PERCIVAL_SHA@/$PERCIVAL_PIN/g" \
  "$SCRIPT_DIR/files/usr/bin/transit-atlas" > "$STAGE/usr/bin/transit-atlas"
cp "$SCRIPT_DIR/files/lib/systemd/system/transit-atlas.service" \
   "$STAGE/lib/systemd/system/transit-atlas.service"
cp "$SCRIPT_DIR/files/lib/systemd/system/percival.service" \
   "$STAGE/lib/systemd/system/percival.service"
cp "$SCRIPT_DIR/files/etc/transit-atlas/percival.conf" \
   "$STAGE/etc/transit-atlas/percival.conf"
cp "$REPO_ROOT/README.md" "$STAGE/usr/share/doc/transit-atlas/README.md"

# --- Control file (version-stamped) and maintainer scripts (verbatim).
sed "s/@VERSION@/$VERSION/g" \
  "$SCRIPT_DIR/DEBIAN/control" > "$STAGE/DEBIAN/control"
cp "$SCRIPT_DIR/DEBIAN/postinst" "$SCRIPT_DIR/DEBIAN/prerm" \
   "$SCRIPT_DIR/DEBIAN/postrm" "$STAGE/DEBIAN/"

# --- Modes and ownership.
# The hand-built package carried the build workspace's shared-directory
# modes (most files 0660). The script normalises instead: directories
# 755, plain files 644, and 755 for the launcher, the maintainer scripts
# and every file git records as executable, so the package is the same
# no matter whose checkout built it. Ownership is forced to root:root.
find "$STAGE" -exec chmod a-st {} +
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +
chmod 755 "$STAGE/usr/bin/transit-atlas" \
          "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/prerm" "$STAGE/DEBIAN/postrm"
chmod 755 "$PC/scripts/run_local.py"
find "$APP" -name '*.sh' -type f -exec chmod 755 {} +
if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # Restore the executable bit for every file git records as executable
  # (the MCP servers and tools the launcher invokes via python3 keep the
  # bit they carry in the repo).
  git -C "$REPO_ROOT" ls-files -s \
    | sed -n 's/^100755 [0-9a-f]* [0-9][0-9]*\t//p' \
    | while IFS= read -r path; do
        [ -f "$APP/$path" ] && chmod 755 "$APP/$path"
      done
fi

OUT_DIR="$REPO_ROOT/dist"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/transit-atlas_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT"
echo "Built $OUT"
