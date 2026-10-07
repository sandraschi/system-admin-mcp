# Development — system-admin-mcp

## Prereqs (Windows 11, Admin terminal)

- Python 3.12+, `uv` (`C:\Users\sandr\.local\bin\uv.exe`), Bun 1.3+ (`~/.bun/bin/bun.exe`, Node 22+ stays for Vite/Tauri CLIs), Tauri: Rust/Cargo for `native/`.
- Run the terminal **as Administrator** — disk/service/recovery ops check elevation at runtime.

## Setup

```powershell
uv sync --all-extras          # or: just build-dev
cd web_sota; bun install      # or: just web-install
uv run pre-commit install     # hooks: ruff, biome (web_sota), ps51-parse, hygiene
```

## Daily loop

```powershell
just dev            # MCP stdio (Claude Desktop path)
just serve          # MCP HTTP on 10861
just web-frontend   # Vite on 10860 (proxy /api -> 10861, /api/logs -> 11066)
just lint           # ruff check + biome ci
just test           # pytest tests/ (note: default run enforces --cov-fail-under=20)
just e2e            # Playwright smoke (web_sota/e2e/smoke.spec.ts)
```

## Layout rules

- New op: logic in `tools/implementations.py` (or `services_and_tasks.py`) → register in
  `tools/portmanteau.py` dispatch + `Literal` op name → REST route in `server.py` via
  `_run_tool("system_admin", operation="<op>", ...)` → webapp page under `web_sota/src/pages/`.
- New page: component in `web_sota/src/pages/<name>.tsx` + route in `App.tsx` + nav in sidebar.
- New prompt: `@mcp.prompt()` in `prompts.py` + `register_all_prompts`.
- New prefab card: `tools/prefab/system_cards.py` + register in `tools/prefab/__init__.py`.
- Tool docstrings: `## Return Format` + `## Examples` required; params via
  `Annotated[T, Field(description=...)]` (see `docs/TOOL_DOCSTRING_STANDARD.md` —
  full `Args:`→`Annotated` migration still pending, tracked as deferred assfix item).

## Gates (must be green before commit)

`ruff check src/` (incl. T20/S110/S112 — no ignores), `ruff format --check src/`,
`pyright src/` (0 errors), `pytest tests/ -q`, `bunx tsc --noEmit` + `bun run biome:ci`
in `web_sota/`, `actionlint .github/workflows/ci.yml`, `just --list` (justfile parses).
