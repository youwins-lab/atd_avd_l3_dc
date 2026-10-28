#!/usr/bin/env bash
# One-time per lab session: install Node.js 24 under ~/.local/node and eos-mcp-server (pinned).
set -euo pipefail
NODE_MAJOR=24
EOS_MCP_VERSION=0.6.1-beta
if ! "$HOME/.local/node/bin/node" --version 2>/dev/null | grep -q "^v${NODE_MAJOR}\."; then
  v=$(curl -s https://nodejs.org/dist/index.json | python3 -c \
    "import json,sys; print(next(r['version'] for r in json.load(sys.stdin) if r['version'].startswith('v${NODE_MAJOR}.')))")
  mkdir -p "$HOME/.local/node"
  curl -sL "https://nodejs.org/dist/$v/node-$v-linux-x64.tar.xz" | tar -xJ -C "$HOME/.local/node" --strip-components=1
fi
export PATH="$HOME/.local/node/bin:$PATH"
npm install -g "@aristanetworks/eos-mcp-server@${EOS_MCP_VERSION}"
"$(dirname "$0")/run-eos-mcp.sh" validate-inventory
