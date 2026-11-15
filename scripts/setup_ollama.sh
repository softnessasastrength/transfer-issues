#!/bin/sh
# setup_ollama.sh — install Ollama and pull the configured Percival model.
# Explicit, on-purpose setup step (the package never downloads at install
# time). Pinned to an official release with its published SHA-256 digest.
set -e
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
mkdir -p /usr/local/lib/ollama
tar --zstd -C /usr/local/lib/ollama --strip-components=1 -xf "$TMP/ollama.tar.zst"
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
