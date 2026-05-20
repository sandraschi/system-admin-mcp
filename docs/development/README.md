# Development

How to hack on System Admin MCP.

## Setup

```powershell
git clone https://github.com/sandraschi/system-admin-mcp
cd system-admin-mcp
uv sync --all-extras
```

## Project Layout

```
src/system_admin_mcp/
├── app.py                 # FastMCP 3.2 instance — lifespan, providers, config
├── main.py                # CLI entry with --web flag
├── server.py              # FastAPI backend (15+ REST endpoints)
├── transport.py           # stdio / streamable-http transport
├── prompts.py             # @mcp.prompt() templates
├── __init__.py            # Package marker
├── __main__.py            # python -m support
└── tools/
    ├── portmanteau.py     # system_admin — the big dispatcher
    ├── implementations.py # Core logic: file recovery, ACLs, disk, diagnostics
    ├── services_and_tasks.py  # Services, processes, startup, taskbar
    ├── agentic_system_workflow.py  # SEP-1577 sampling workflows
    ├── monitoring.py      # Watchdog file watcher
    ├── system_ops.py      # Standalone tools (list_volumes, ping, etc.)
    └── prefab/            # Prefab UI cards
        ├── __init__.py
        └── system_cards.py
```

## Adding a New Operation

1. Add the implementation function in `tools/implementations.py` or `tools/services_and_tasks.py`
2. Add the operation name to the `Literal` type in `portmanteau.py`
3. Add the dispatch branch in the `system_admin()` function body
4. Add documentation examples

## Adding a Prefab Tool

1. Write the function in `tools/prefab/system_cards.py` returning `ToolResult` with `structured_content=PrefabApp(...)`
2. Register in `tools/prefab/__init__.py` via `mcp.tool(app=True)(fn)`

## Adding a REST Endpoint

1. Add the handler in `server.py`
2. Use `_run_tool("system_admin", operation="<op>", ...)` to delegate to the MCP layer
3. Follow existing patterns for error handling

## Code Quality

```powershell
just lint       # ruff + Biome check
just fix        # auto-fix everything
just test       # pytest
just check-sec  # bandit security audit
```

Rules:
- No `print()` in handlers (ruff T201)
- No `console.log` in webapp (Biome enforces)
- Docstrings: no `Args:` blocks — use `Annotated[T, Field(description="...")]`
- Type hints: `X | None` over `Optional[X]`, `dict` over `Dict`

## Transport Modes

| Mode | Env / Flag | Use Case |
|------|-----------|----------|
| stdio | `MCP_TRANSPORT=stdio` (default) | Claude Desktop |
| HTTP | `MCP_TRANSPORT=http` or `--http` | Web clients, testing |
| Port | `MCP_PORT=10861` (default) | HTTP binding port |

## Publishing

```powershell
just mcpb-pack      # Build MCPB bundle
# then upload to PyPI:
uv build
uv publish
```
