#!/usr/bin/env bash
# Launch eos-mcp-server for the ATD lab. The lab passphrase is ephemeral per session, so it is read
# from code-server's config at launch time instead of being stored anywhere.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/node/bin:$PATH"
if [[ -z "${EOS_MCP_PASSWORD:-}" ]]; then
  EOS_MCP_PASSWORD="$(awk '/^password:/ {print $2}' /home/coder/.config/code-server/config.yaml)"
  export EOS_MCP_PASSWORD
fi
cmd="${1:-serve}"; shift || true
exec eos-mcp-server "$cmd" --config "$here/eos-mcp-server.yml" --inventory "$here/inventory.yml" "$@"
