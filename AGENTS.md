# AGENTS.md — System Admin MCP

## Project Identity

- **Name**: system-admin-mcp
- **Version**: 0.4.0
- **Purpose**: FastMCP 3.2 server for elevated Windows system administration — NTFS file recovery, security/ACL management, disk maintenance, service/process orchestration, system diagnostics
- **Language**: Python 3.12+ (backend), TypeScript/React (webapp)
- **Ports**: 10860 (webapp frontend), 10861 (API backend / MCP HTTP)
- **License**: MIT
- **Admin required**: YES — run terminal as Administrator. Many operations (disk, services, file recovery) check `IsUserAnAdmin()` internally and return an error if not elevated.

## FastMCP 3.2 Capabilities

| Feature | What it provides |
|---------|-----------------|
| **`ctx.sample()`** (SEP-1577) | Tools `agentic_system_workflow` and `autonomous_system_troubleshooter` use `ctx.sample()` to orchestrate multi-step diagnostics without client round-trips. The server borrows the client LLM to analyze system data and recommend actions. |
| **Prompts** (4) | `@mcp.prompt()` templates: `system_diagnostics_expert`, `security_hardening_expert`, `system_troubleshooter`, `volume_maintenance_expert`. Parameterized with focus modes. Registered in `prompts.py`. |
| **Skills** (1) | `skill://system-admin-expert/SKILL.md` via `SkillsDirectoryProvider`. Contains safe-mode patterns, diagnostic sequences, agentic workflow recipes. |
| **Prefab UI** (4 cards) | `@mcp.tool(app=True)` returning `ToolResult` with `structured_content=PrefabApp`: `system_health_card`, `top_processes_card`, `list_services_card`, `volume_status_card`. |
| **Dual transport** | stdio (default for Claude Desktop) + streamable-http (`MCP_TRANSPORT=http`) on port 10861. |

## Architecture

```
src/system_admin_mcp/
├── app.py                 # FastMCP 3.2 instance + lifespan (SkillsDirectoryProvider, Prefab)
├── main.py                # Entry point (--web flag for HTTP, else stdio)
├── server.py              # FastAPI backend (15+ REST endpoints at /api/*)
├── transport.py           # Dual transport (stdio/streamable-http) via MCP_TRANSPORT env
├── prompts.py             # 4 @mcp.prompt() templates (diagnostics, security, troubleshooting, volume)
├── tools/
│   ├── portmanteau.py     # system_admin (40+ ops) + manage_filesystem_watch
│   ├── system_ops.py      # list_volumes, get_file_owner, recover_file, ping, etc.
│   ├── implementations.py # 25+ real implementations (file recovery, ACLs, disk ops, WMI/WMI)
│   ├── services_and_tasks.py  # Services, processes, startup, taskbar (1003 lines)
│   ├── agentic_system_workflow.py  # SEP-1577 sampling-driven workflows
│   ├── monitoring.py      # FileWatcherManager (watchdog singleton)
│   └── prefab/            # Prefab UI cards (health, processes, services, volumes)
├── elevated_service/      # Named-pipe elevated service bridge
├── user_bridge/           # UserBridge client for elevated service
├── __init__.py            # Package marker, __version__ = "0.4.0"
├── __main__.py            # python -m support
└── prompts.py             # 4 prompt templates
web_sota/src/
├── App.tsx                # React Router v7
├── pages/                 # 14 page components (dashboard, processes, services, volumes, etc.)
└── components/            # Layout + UI primitives (shadcn-style)
mcpb/                      # MCPB packaging for Claude Desktop
├── manifest.json          # v0.2 standard
├── server/__main__.py     # MCPB entry point
└── assets/prompts/        # system.md, user.md, examples.json + 4 domain guides
skills/
└── system-admin-expert/   # SkillsDirectoryProvider skill
    └── SKILL.md
```

## Tools

### Portmanteau Tool (default, single-tool mode)

| Tool | Operations (40+) |
|------|-----------------|
| `system_admin` | scan_volume, recover_file, validate_recovery, batch_recover, get_permissions, set_permissions, remove_permission, take_ownership, audit_permissions, modify_acl, check_disk_health, analyze_disk_usage, disk_cleanup, defragment_disk, optimize_ssd, get_volume_info, get_hardware_info, get_os_info, get_installed_software, get_performance_metrics, get_event_log, get_recent_event_errors, health_check, check_system_health_status, get_top_resource_processes, audit_network_ports, analyze_top_folder_sizes, get_comprehensive_diagnostics, list_services, get_service_stats, get_service_info, start_service, stop_service, set_service_startup, list_processes, analyze_process, kill_process, list_startup_programs, add_startup_program, remove_startup_program, find_taskbar_blocking_processes, kill_taskbar_blocking_processes, get_taskbar_settings, set_taskbar_autohide |

### Standalone Tools

| Tool | Purpose |
|------|---------|
| `manage_filesystem_watch` | Background directory monitoring (watchdog) |
| `get_comprehensive_diagnostics` | Full health + processes + events + volume audit |
| `agentic_system_workflow` | SEP-1577 sampling-driven multi-step admin workflow |
| `autonomous_system_troubleshooter` | 3-phase autonomous diagnosis |
| `list_volumes` | All system volumes |
| `get_file_owner` | File/directory owner + SID |
| `recover_file` | NTFS file recovery |
| `get_disk_usage` | Path disk usage |
| `get_process_info` | Process by PID |
| `ping` | Connectivity check |
| `get_system_info` | OS + hardware summary |
| `help` | Usage documentation |
| `status` | Server status |
| `list_startup_programs` | Windows startup entries |
| `add_startup_program` | Add to startup (HKCU/HKLM) |
| `remove_startup_program` | Remove from startup |
| `get_taskbar_settings` | Autohide/lock status |
| `set_taskbar_autohide` | Toggle autohide |

### Prefab UI Tools (app=True)

| Tool | Content |
|------|---------|
| `system_health_card` | CPU/RAM/disk card |
| `top_processes_card` | Top N processes by CPU/memory |
| `list_services_card` | Windows services with filtering |
| `volume_status_card` | All volumes with bar charts |

## Key Rules for Agents

### Portmanteau Pattern
- All admin operations go through `system_admin(operation="<op>", ...)` — the single portmanteau tool
- Standalone tools exist for filesystem watches, agentic workflows, volume listing, and file ops
- Prefab tools return `ToolResult` with `structured_content=PrefabApp(...)` for rich in-chat UI
- Tool mode is always portmanteau (no env toggle — single-tool dispatcher pattern)

### Connection & Privilege
- No external service connection needed (unlike DVR/Resolve) — tools call Windows APIs directly
- Admin elevation checked via `ctypes.windll.shell32.IsUserAnAdmin()`
- Some operations (file recovery, defrag, service management) require admin
- Named-pipe `elevated_service/` for operations requiring SYSTEM context

### File Patterns
- New ops: add to `tools/implementations.py` (core logic) or `tools/services_and_tasks.py`, then register in `tools/portmanteau.py` dispatch table + `Literal` type
- New prefab: create function in `tools/prefab/system_cards.py`, register in `tools/prefab/__init__.py`
- New prompt: add `@mcp.prompt()` in `prompts.py`
- New pages: create `web_sota/src/pages/<name>.tsx`, add route in `App.tsx`, add nav in sidebar
- New REST endpoint: add to `server.py` with `_run_tool("system_admin", operation="<op>", ...)` pattern

### Kill Process Pattern
- To kill a process: `system_admin(operation="kill_process", pid=<N>, force=false)`
- Always verify PID with `system_admin(operation="analyze_process", pid=<N>)` first
- Prefer `force=false` (SIGTERM) before `force=true` (SIGKILL)
- For bulk kills by name, use `list_processes(filter_name="<name>")` to collect PIDs, then iterate

### Linting & Quality
- Python: `just lint-python` or `just fix` (ruff check + format)
- Webapp: `just lint-web` (Biome ci) or `just fix-web` (Biome check --write)
- Run `just check` (lint + test) before committing
- No console.log in webapp (Biome enforces)
- No print in core handlers (Ruff T201)
- Docstrings: NO `Args:` blocks — use `Annotated[T, Field(description="...")]` per SOTA docstring protocol
- Use `## Return Format` and `## Examples` in tool docstrings

### CLI Commands
```
just                    # SOTA Industrial Dashboard
just dev                # MCP stdio (Claude Desktop)
just serve              # MCP HTTP on MCP_PORT (default 10861)
just web                # FastAPI backend on WEBAPP_PORT (default 10861)
just web-frontend       # Vite dev server on 10860
just build              # uv sync
just test               # pytest tests/
just test-cov           # pytest with coverage
just lint               # ruff check + Biome ci
just fix                # ruff --fix + format + Biome --write
just mcpb-pack          # Build MCPB bundle to dist/
just clean              # Remove build artifacts
just check-sec          # Bandit security audit
just audit-deps         # Safety dependency audit
```

### Dependencies
- Python: `uv sync` or `just build`
- Webapp: `npm install` in `web_sota/`
- Dev extras: `uv sync --all-extras` or `just build-dev`
- Core deps: `fastmcp[tasks]>=3.2.0,<4`, `pywin32`, `psutil`, `wmi`, `prefab-ui>=0.14.0`, `fastapi`, `uvicorn`, `watchdog`

### Testing
- Tests in `tests/` — pytest with `conftest.py` fixtures
- Run `pytest tests/ -v` or `just test`
- Coverage: `pytest --cov=system_admin_mcp --cov-report=html`
- Windows-only tests; some require admin elevation

### MCPB Packaging
- Manifest: `mcpb/manifest.json` (v0.2)
- Build: `just mcpb-pack` or `uv run python mcpb_build.py`
- Bundle output: `dist/system-admin-mcp-v0.4.0.mcpb`
- Prompts included: system.md, user.md, examples.json + 4 domain guides
- Exclusion: `.mcpbignore` follows MCPB_PACKAGING_STANDARDS.md
