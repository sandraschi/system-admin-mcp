# System Admin MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

**Windows system administration, through AI.** File recovery, security, disk maintenance, diagnostics, services, processes — all accessible via MCP (Claude Desktop, Cursor, etc.) and a React web dashboard.

> **Download the installer:** [latest release](https://github.com/sandraschi/system-admin-mcp/releases) (`system-admin-mcp-0.4.0-setup.exe`) — no Python needed, backend embedded. For Claude Desktop without installing: attach `system-admin-mcp-0.4.0.mcpb` from the same release.
>
> **Claude Desktop only** — one-line install of the latest bundle:
> ```powershell
> irm https://github.com/sandraschi/system-admin-mcp/releases/latest/download/install.ps1 | iex
> ```

> **⚠️ Administrator privileges required.** Disk operations, service management, file recovery, and permission changes need elevation. Run your terminal as Administrator before starting the server.

```json
// Claude Desktop — from source (no registry package; see INSTALL.md):
{ "mcpServers": { "system-admin-mcp": {
  "command": "uv",
  "args": ["--directory", "D:\\Dev\\repos\\system-admin-mcp", "run", "system-admin-mcp"]
} } }
```

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/system-admin-mcp
cd system-admin-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start. Frontend deps install via Bun 1.3+ (`bun.lock` committed); Node 22+ stays for the Vite/Tauri CLIs.
### Manual Setup

If you don't have `just` installed:

# Run terminal AS ADMINISTRATOR first, then:
```powershell
git clone https://github.com/sandraschi/system-admin-mcp
cd system-admin-mcp
uv sync --all-extras
uv run system-admin-mcp         # stdio mode (for MCP clients like Claude Desktop)
uv run system-admin-mcp --web   # HTTP mode on :10861 (web dashboard backend)
```
Verify: `Invoke-WebRequest http://127.0.0.1:10861/api/health -UseBasicParsing` → 200.
See [INSTALL.md](INSTALL.md) for prerequisites, installer/MCPB options, and troubleshooting.

## What You Can Do

| Area | Operations |
|------|-----------|
| **System Health** | CPU/RAM/disk metrics, event logs, hardware inventory, installed software |
| **File Recovery** | Scan NTFS MFT, recover deleted files, validate integrity |
| **Security** | View/set/audit NTFS permissions, take ownership, network port audit, Defender/VPN/Tailscale posture, red-button Airgap |
| **Disks** | SMART health, defrag (HDD), TRIM (SSD), cleanup, folder size analysis |
| **Services** | List/start/stop, change startup type, paginated |
| **Processes** | List/sort/analyze/kill, paginated, sortable by CPU/Memory/Name/PID |
| **Startup & Taskbar** | Manage startup programs, toggle autohide, find blockers, taskbar buttons + tray icons with autostart flags |
| **AI Chat** | Local (Ollama/LM Studio) + 13 cloud providers via backend proxy, streaming, resident-first GPU placement |
| **Safety** | Read-only mode (`SYSTEMADMIN_READ_ONLY=1`), mutation audit log, confirm-gated Airgap (see `docs/SECURITY.md`) |
| **Agentic** | Let AI autonomously diagnose and fix issues (SEP-1577 sampling) |

All operations go through a single `system_admin` tool — one tool, 40+ operations.

---

## FastMCP 3.4 Capabilities

| Feature | What it provides |
|---------|-----------------|
| **`ctx.sample()`** (SEP-1577) | Server-side LLM calls for autonomous diagnosis. Tools `agentic_system_workflow` and `autonomous_system_troubleshooter` use `ctx.sample()` to orchestrate multi-step diagnostics without client round-trips — the server borrows the client LLM to interpret system data and recommend actions. |
| **Prompts** (4 templates) | Registered via `@mcp.prompt()`: `system_diagnostics_expert`, `security_hardening_expert`, `system_troubleshooter`, `volume_maintenance_expert`. Each has parameterized focus modes (e.g. performance vs events, ownership vs audit). Clients inject them as system instructions. |
| **Skills** (`skill://`) | `SkillsDirectoryProvider` exposes `skill://system-admin-expert/SKILL.md` — a portable expertise document with safe-mode patterns, diagnostic sequences, and SEP-1577 workflow recipes. Discoverable via `resources/list`. |
| **Prefab UI** (4 cards) | `@mcp.tool(app=True)` tools returning `ToolResult` with `structured_content=PrefabApp(...)`: `system_health_card` (CPU/RAM/disk), `top_processes_card` (sorted by CPU/memory), `list_services_card` (filtered services), `volume_status_card` (all volumes with bar charts). Rendered natively by capable hosts (Claude Desktop side-panel). |
| **CodeMode** | BM25 discovery for agentic tool selection. Enabled via `--agentic` flag. |
| **SkillsDirectoryProvider** | Registers `skill://` resources from `skills/` directory. |
| **Dual transport** | stdio (default for Claude Desktop) + streamable-http (`MCP_TRANSPORT=http`). |

---

## Web Dashboard

A 20-page React SPA on ports **10860** (frontend) / **10861** (backend):

```powershell
just web              # Backend API
just web-frontend     # Frontend dev server
```

Pages: Dashboard, Inbox (attention feed), Status, Processes (paginated, sortable), Services (paginated), Taskbar (buttons + tray + autostart), Volumes, File Owner, File Recovery, Logs, Tools, Apps, Elevated, Chat, Settings, Help.

---

## Justfile Commands

| Command | What it does |
|---------|-------------|
| `just dev` | Start MCP server (Claude Desktop) |
| `just serve` | Start MCP via HTTP |
| `just test` | Run tests |
| `just lint` | Check code quality (ruff + biome) |
| `just fix` | Auto-fix everything |
| `just certify` | Full gates: ruff + format + pyright + pytest + frontend build + biome |
| `just mcpb-pack` | Build MCPB bundle |
| `just build` | Install dependencies |
| `just web` | Start FastAPI backend on 10861 |
| `just web-frontend` | Start Vite frontend on 10860 |

---

## Stack

React 19 + Vite 7 + TailwindCSS 3 + Radix UI + Lucide + TanStack Query +
Zustand 5 (LLM/GPU store) + React Router 7. Backend: FastAPI + FastMCP 3.4
(`fastmcp[tasks]>=3.4.4,<4`) on Python 3.12+, `uv` managed. No Bootstrap,
no jQuery, no Redux.

## Environment

| Var | Default | Effect |
|-----|---------|--------|
| `SYSTEMADMIN_READ_ONLY=1` | off | Mutation kill switch |
| `SYSTEMADMIN_LLM_KEYSTORE` | `data/llm_keys.json` | 0600 LLM key store |
| `MCP_TRANSPORT=http` | stdio | Streamable-HTTP transport |
| `WEBAPP_PORT` / `PORT` | `10861` | Backend port |

Full install + troubleshooting: [INSTALL.md](INSTALL.md).

---

## Project Map

```
├── AGENTS.md           # Instructions for AI agents
├── justfile            # Task runner (SOTA Industrial Dashboard)
├── pyproject.toml      # Python project config (FastMCP 3.4)
├── src/system_admin_mcp/
│   ├── app.py          # FastMCP instance + lifespan (skills, prefabs)
│   ├── server.py       # FastAPI backend (20+ REST endpoints)
│   ├── transport.py    # stdio / streamable-http dual transport
│   ├── prompts.py      # 4 @mcp.prompt() templates
│   ├── tools/
│   │   ├── portmanteau.py          # system_admin (40+ ops dispatcher)
│   │   ├── implementations.py      # File recovery, ACLs, disk, WMI
│   │   ├── services_and_tasks.py   # Services, processes, startup, taskbar
│   │   ├── agentic_system_workflow.py  # ctx.sample() workflows
│   │   ├── monitoring.py           # Watchdog file watcher
│   │   ├── system_ops.py           # Standalone tools
│   │   └── prefab/                 # 4 Prefab UI cards
│   ├── elevated_service/           # Named-pipe elevated bridge
│   └── user_bridge/                # Service communication client
├── web_sota/           # React 19 + Vite dashboard
├── mcpb/               # MCPB packaging (v0.2 manifest)
├── skills/             # skill://system-admin-expert/SKILL.md
└── tests/              # Pytest suite
```

---

## Docs

| Document | For |
|----------|-----|
| [Quickstart](docs/quickstart.md) | End users — install, configure, run |
| [API Reference](docs/api/README.md) | Developers — REST endpoints |
| [Development](docs/development/README.md) | Contributors — hacking on the server |
| [AGENTS.md](AGENTS.md) | AI agents — architecture & patterns |

---

Built by [Sandra Schipal](https://github.com/sandraschi) in Vienna. MIT.
