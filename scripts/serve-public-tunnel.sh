#!/usr/bin/env bash
# Serve RouteVault static v0 on :8765 and expose via Cloudflare quick tunnel.
# Note: trycloudflare URLs are ephemeral; prefer Cloudflare Pages for permanent URL.
set -euo pipefail
ROOT="/mnt/nas/agents/Projects/RouteVault/code/routevault-staging"
PORT="${PORT:-8765}"
CLOUDFLARED="${CLOUDFLARED:-/tmp/cloudflared}"
if [[ ! -x "$CLOUDFLARED" ]]; then
  curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o /tmp/cloudflared
  chmod +x /tmp/cloudflared
  CLOUDFLARED=/tmp/cloudflared
fi
cd "$ROOT"
if ! curl -sf -o /dev/null "http://127.0.0.1:${PORT}/"; then
  python3 -m http.server "$PORT" >/tmp/routevault-http.log 2>&1 &
  echo $! >/tmp/routevault-http.pid
  sleep 1
fi
exec "$CLOUDFLARED" tunnel --url "http://127.0.0.1:${PORT}"
