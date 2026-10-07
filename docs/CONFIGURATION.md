# Configuration — system-admin-mcp

Single source of truth is the repo-root `.env` (never committed; copy `.env.example`).
The webapp has no separate `.env` — Vite vars are passed at launch by `start.ps1`
via the fleet engine (`fleet-start.config.ps1`).

## Environment variables

| Variable | Default | Used by | Purpose |
|---|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `transport.py` | `stdio` (Claude Desktop) or `http` (streamable-HTTP on 10861) |
| `MCP_PORT` | `10861` | `transport.py` | MCP HTTP port when `MCP_TRANSPORT=http` |
| `WEBAPP_PORT` / `PORT` | `10861` | `main.py --web` | FastAPI backend port (`--web` / `SYSTEMADMIN_TAURI=1`) |
| `WEB_PORT` | `10861` | fleet engine | Backend port injected at launch (`fleet-start.config.ps1`) |
| `MCP_BRIDGE_URLS` | _(empty)_ | `app.py` | Comma-separated remote MCP URLs proxied via `create_proxy` |
| `SYSADMIN_PREFAB_APPS` | `1` | `app.py` | `0` disables Prefab card tools (requires `prefab-ui`) |
| `SYSTEMADMIN_TAURI` | _(empty)_ | `main.py` | `1` forces FastAPI mode (used by the Tauri sidecar) |

## Ports (registry: `mcp-central-docs/operations/WEBAPP_PORTS.md`)

| Port | Service |
|---|---|
| 10860 | Vite frontend (`web_sota/`) |
| 10861 | FastAPI backend + MCP HTTP (`src/system_admin_mcp/server.py`, `transport.py`) |
| 11066 | Logging-backend proxy target (`/api/logs` in `vite.config.ts`) |

## Launch

- `start.ps1` (fleet engine + `fleet-start.config.ps1`) — canonical, clears port zombies, polls `/api/health`.
- `just serve` → MCP stdio-over-HTTP; `just web` → FastAPI; `just web-frontend` → Vite.
- `python -m system_admin_mcp` → stdio (Claude Desktop entry: `uv run system-admin-mcp`).
