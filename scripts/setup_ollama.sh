#!/bin/sh
# setup_ollama.sh — install Ollama and pull the configured Percival model.
# Explicit, on-purpose setup step (the package never downloads at install
# time). Pinned to an official release with its published SHA-256 digest.
set -e

# extract_ollama <archive> <install-dir>
#
# The release tarball's top level is bin/ + lib/: the binary is
# bin/ollama and its support files live under lib/ollama/ (llama-server,
# libggml*, cuda_v12/, cuda_v13/, vulkan/). Extract WITHOUT
# --strip-components so the tree lands intact under <install-dir> and
# <install-dir>/bin/ollama is the executable the service runs.
# (The v0.0.1/v0.0.2 packages shipped this extraction with
# --strip-components=1: bin/ollama became a regular FILE named
# "ollama" in the target root, and every lib/ollama/* member then
# failed with "Not a directory". The pinned digest verified fine —
# the script had simply never been run end-to-end. See DECISIONS.md.)
# The layout is asserted after extraction so a future upstream layout
# change fails loudly here instead of silently at inference time.
extract_ollama() {
  mkdir -p "$2"
  tar --zstd -C "$2" -xf "$1"
  if [ ! -x "$2/bin/ollama" ] || [ ! -f "$2/lib/ollama/llama-server" ]; then
    echo "setup-ollama: unexpected Ollama tarball layout — expected bin/ollama and lib/ollama/llama-server under $2" >&2
    exit 1
  fi
}

# Tests source this file with SETUP_OLLAMA_FUNCTIONS_ONLY=1 to exercise
# extract_ollama without running the install.
if [ "${SETUP_OLLAMA_FUNCTIONS_ONLY:-0}" = "1" ]; then
  return 0 2>/dev/null || exit 0
fi

OLLAMA_VERSION=v0.40.16
# Pick the release asset for this machine's architecture. Each SHA-256 is
# the digest published with the official Ollama release named above.
case "$(uname -m)" in
  x86_64)
    OLLAMA_ASSET=ollama-linux-amd64.tar.zst
    OLLAMA_SHA256=87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d
    ;;
  aarch64|arm64)
    OLLAMA_ASSET=ollama-linux-arm64.tar.zst
    OLLAMA_SHA256=e45b8e6dcb86cb9f3057396351655079c9a4879b4ced2678c9350d375dcbc224
    ;;
  *)
    echo "setup-ollama: unsupported architecture '$(uname -m)' — no ${OLLAMA_VERSION} Ollama build is pinned for it" >&2
    exit 1
    ;;
esac
OLLAMA_URL="https://github.com/ollama/ollama/releases/download/${OLLAMA_VERSION}/${OLLAMA_ASSET}"
CONF=/etc/transit-atlas/percival.conf
[ -f "$CONF" ] && . "$CONF"
MODEL="${OLLAMA_MODEL:-qwen3:1.7b}"
[ "$(id -u)" = "0" ] || { echo "setup-ollama needs root (sudo transit-atlas setup-ollama)" >&2; exit 1; }
command -v zstd >/dev/null || { echo "Installing zstd (needed to unpack Ollama)..."; apt-get install -y zstd; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
echo "Downloading Ollama ${OLLAMA_VERSION} (~1.5 GB, official GitHub release)..."
curl -fL --retry 3 -o "$TMP/ollama.tar.zst" "$OLLAMA_URL"
echo "${OLLAMA_SHA256}  $TMP/ollama.tar.zst" | sha256sum -c -
extract_ollama "$TMP/ollama.tar.zst" /usr/local/lib/ollama
ln -sf /usr/local/lib/ollama/bin/ollama /usr/local/bin/ollama
getent passwd ollama >/dev/null || adduser --system --group --home /usr/share/ollama --no-create-home ollama
mkdir -p /usr/share/ollama/.ollama && chown -R ollama:ollama /usr/share/ollama
cat > /etc/systemd/system/ollama.service <<'UNIT'
[Unit]
Description=Ollama local model service (for Percival)
After=network.target
[Service]
Type=simple
User=ollama
Environment=HOME=/usr/share/ollama
ExecStart=/usr/local/bin/ollama serve
Restart=on-failure
[Install]
WantedBy=multi-user.target
UNIT
if [ -d /run/systemd/system ]; then systemctl daemon-reload || true; systemctl enable --now ollama || true; fi
if ! curl -s http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
  echo "systemd not running the service; starting ollama serve in the background for this session..."
  su ollama -s /bin/sh -c 'HOME=/usr/share/ollama nohup /usr/local/bin/ollama serve >/var/log/ollama-setup.log 2>&1 &' || true
  sleep 3
fi
echo "Pulling the Percival model: ${MODEL} ..."
su ollama -s /bin/sh -c "HOME=/usr/share/ollama /usr/local/bin/ollama pull ${MODEL}"
echo "Done. Percival's local model is ${MODEL} (change OLLAMA_MODEL in ${CONF} to swap it)."
