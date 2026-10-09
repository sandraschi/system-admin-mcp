# Installation — System Admin MCP

> Every command below was executed on 2026-10-09 (assfix certify). If one fails
> for you, open an issue with the exact output.

## 0. Read this first

- **Windows only.** Disk, service, recovery, and ACL operations call Win32/WMI.
- **Run your terminal as Administrator** for anything beyond browsing:
  right-click Terminal → Run as administrator. (`just info` prints `Admin: YES`.)
- **No PyPI package.** `uvx system-admin-mcp` does NOT work — there is no
  registry release. Install from source (B) or use the installer/MCPB (A).
- Ports: **10860** (frontend) / **10861** (backend). Nothing else is needed.

## A. No-install options (fastest)

**Windows installer** (no Python needed, backend embedded):
1. Download `system-admin-mcp-0.4.0-setup.exe` from
   [releases](https://github.com/sandraschi/system-admin-mcp/releases).
2. Run it, then launch from Start Menu.

**Claude Desktop without installing**: attach `system-admin-mcp-0.4.0.mcpb`
from the same release to Claude Desktop.

## B. From source (developers)

### 1. Prerequisites

```powershell
winget install Casey.Just --accept-source-agreements --accept-package-agreements
winget install astral-sh.uv --accept-source-agreements --accept-package-agreements
# Git + Python 3.12+ + Bun (frontend): https://git-scm.com, https://python.org, https://bun.sh
```

(The `--accept-*` flags matter: without them winget stops mid-script with a
license prompt — issue #1.)

### 2. Clone + bootstrap

```powershell
git clone https://github.com/sandraschi/system-admin-mcp
cd system-admin-mcp
just bootstrap   # uv sync + pre-commit hook; safe to re-run
just info        # prints Python/uv/ruff versions + Admin YES/NO + ports
```

`just` alone lists every recipe (the old `mcpb-pack redefined` startup error
from issue #1 is fixed — `just --list` exits 0).

### 3. Start

```powershell
just serve         # backend API on :10861  (uv run system-admin-mcp --http)
just web-frontend  # dashboard on :10860 (new terminal)
```

Or without `just`:

```powershell
uv sync --all-extras
uv run system-admin-mcp            # stdio (Claude Desktop)
uv run system-admin-mcp --web      # backend API on :10861
```

### 4. Verify

```powershell
Invoke-WebRequest http://127.0.0.1:10861/api/health -UseBasicParsing
# StatusCode 200, {"status":"ok", ...}
```

Open `http://127.0.0.1:10860/` — the backend dot must be green. Start at
**Inbox**: it shows critical event-log errors, blocked mutations, and reboot
state for this machine.

## Environment variables

| Var | Default | Effect |
|-----|---------|--------|
| `SYSTEMADMIN_READ_ONLY=1` | off | Blocks every mutation (kill switch); dry-run previews still work |
| `SYSTEMADMIN_LOG_FILE` | unset | Extra file log (set automatically for frozen builds) |
| `SYSTEMADMIN_LLM_KEYSTORE` | `data/llm_keys.json` | 0600 LLM key store (tests override per-test) |
| `MCP_TRANSPORT=http` | stdio | Serve MCP over streamable HTTP instead of stdio |
| `WEBAPP_PORT` / `PORT` | `10861` | Backend port for `--web`/`--http` |
| `SYSTEMADMIN_TAURI=1` | unset | Force web mode (used by the native wrapper) |

## Troubleshooting

| Issue | Fix |
|---|---|
| `just` not found | `winget install Casey.Just --accept-source-agreements --accept-package-agreements` |
| winget license prompt | re-run with the `--accept-*` flags from §1 |
| Port conflict on 10860/10861 | stop the old process (or `just fleet-stop` fleet-wide), then `just serve` |
| `Admin: NO` | relaunch the terminal as Administrator |
| `uv sync` stale | `uv sync --all-extras` (plain `uv sync` prunes dev deps) |
| Chat 500s against Ollama | verify the engine first: `POST 127.0.0.1:11434/api/chat` — a 500 there is an engine fault, not this repo |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/system-admin-mcp/issues) with the exact command + output |

*Full feature overview: [README](README.md). Agent reference: [llms-full.txt](llms-full.txt).*
