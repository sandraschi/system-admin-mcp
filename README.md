# System Admin MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

**Windows system administration, through AI.** File recovery, security, disk maintenance, diagnostics, services, processes — all accessible via MCP (Claude Desktop, Cursor, etc.) and a React web dashboard.

> **⚠️ Administrator privileges required.** Disk operations, service management, file recovery, and permission changes need elevation. Run your terminal as Administrator before starting the server.

```json
# Claude Desktop — right-click → Run as Administrator, then:
"mcpServers": { "system-admin-mcp": { "command": "uvx", "args": ["system-admin-mcp"] } }
```

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/system-admin-mcp
cd system-admin-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:
# Run terminal AS ADMINISTRATOR first, then:
uvx system-admin-mcp
See [Quickstart](docs/quickstart.md) for full setup.

## What You Can Do

| Area | Operations |
|------|-----------|
| **System Health** | CPU/RAM/disk metrics, event logs, hardware inventory, installed software |
| **File Recovery** | Scan NTFS MFT, recover deleted files, validate integrity |
| **Security** | View/set/audit NTFS permissions, take ownership, network port audit |
| **Disks** | SMART health, defrag (HDD), TRIM (SSD), cleanup, folder size analysis |
| **Services** | List/start/stop, change startup type, paginated |
| **Processes** | List/sort/analyze/kill, paginated, sortable by CPU/Memory/Name/PID |
| **Startup & Taskbar** | Manage startup programs, toggle autohide, find blockers |
| **Agentic** | Let AI autonomously diagnose and fix issues (SEP-1577 sampling) |

All operations go through a single `system_admin` tool — one tool, 40+ operations.

---

## FastMCP 3.2 Capabilities

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

A 14-page React SPA on ports **10860** (frontend) / **10861** (backend):

```powershell
just web              # Backend API
just web-frontend     # Frontend dev server
```

Pages: Dashboard, Status, Processes (paginated, sortable), Services (paginated), Volumes, File Owner, File Recovery, Logs, Tools, Apps, Elevated, Chat, Settings, Help.

---

## Justfile Commands

| Command | What it does |
|---------|-------------|
| `just dev` | Start MCP server (Claude Desktop) |
| `just serve` | Start MCP via HTTP |
| `just test` | Run tests |
| `just lint` | Check code quality (ruff + biome) |
| `just fix` | Auto-fix everything |
| `just mcpb-pack` | Build MCPB bundle |
| `just build` | Install dependencies |
| `just web` | Start FastAPI backend on 10861 |
| `just web-frontend` | Start Vite frontend on 10860 |

---

## Project Map

```
├── AGENTS.md           # Instructions for AI agents
├── justfile            # Task runner (SOTA Industrial Dashboard)
├── pyproject.toml      # Python project config (FastMCP 3.2)
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
