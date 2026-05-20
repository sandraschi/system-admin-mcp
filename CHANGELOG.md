# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-05-15

### SOTA Quality, Packaging & Prefab Expansion

- **justfile rewrite**: Full SOTA Industrial Dashboard per JUSTFILE_STANDARDS.md — added `test`, `build`, `check`, `dev`, `serve`, `web`, `web-frontend`, `mcpb-pack`, `mcpb-validate`, `clean`, `clean-all` recipes. Every mandatory SOTA recipe (test, check, build, default) present with categorized groups (Quality, Testing, Build, Development, MCPB, Housekeeping, Hardening).
- **MCPB packaging v0.2**: Fixed `manifest.json` to proper v0.2 standard with tools array (19 tool entries), correct `uv run system-admin-mcp` entry point. Created `mcpb/server/__main__.py` as runtime entry. Updated `.mcpbignore` per MCPB_PACKAGING_STANDARDS.md. Updated `mcpb_build.py` to include all prompts and examples. Created `mcpb/assets/prompts/user.md` (13-section tutorial guide, 4000+ words) and `mcpb/assets/prompts/examples.json` (100+ structured tool call mappings).
- **Prefab UI expansion**: Added `list_services_card` (rich card for Windows services with filtering) and `volume_status_card` (volume list with ASCII bar charts). Both registered via `@mcp.tool(app=True)` with `ToolResult` + `PrefabApp`. Removed redundant `prefab-ui` from `[apps]` optional extras (already a core dependency).
- **API endpoint fix**: `GET /api/services`, `GET /api/processes`, `GET /api/processes/{pid}` now correctly route through the `system_admin` portmanteau tool instead of calling non-existent standalone tools.
- **Version bump**: 0.3.0 → 0.4.0 (pyproject.toml, `__init__.py`, mcpb/manifest.json).

---

## [0.3.0] - 2026-04-09

### FastMCP 3.2 Full Conformance

- **SkillsDirectoryProvider**: New `skills/system-admin-expert/SKILL.md` at repo root, exposed via `skill://system-admin-expert/SKILL.md` (FastMCP 3.1+ skills provider). Replaces manual resource workaround. Registered in `app.py` lifespan.
- **Prompts module** (`prompts.py`): 4 high-quality `@mcp.prompt()` templates with `name=`, `description=`, `tags=` — `system_diagnostics_expert`, `security_hardening_expert`, `system_troubleshooter`, `volume_maintenance_expert`. Content derived from the existing `assets/prompts/` documentation. Registered in `main.py`.
- **Prefab UI tools** (`tools/prefab/`): `system_health_card` and `top_processes_card` with `@mcp.tool(app=True)` + `ToolResult` + `PrefabApp`. Optional — requires `uv sync --extra apps`. Guarded by `SYSADMIN_PREFAB_APPS` env var. Registered in `app.py` lifespan.
- **`prefab-ui` optional dep**: Added `[project.optional-dependencies] apps = ["prefab-ui>=0.18.0"]` to `pyproject.toml`.
- **`agentic_system_workflow.py`** — rewrote from scratch. Previous implementation was a simulation stub (fake `simulated_tool_call`, wrong `sample_step` API, implementation honesty violation). Replaced with real 2-tool module: `agentic_system_workflow` (multi-tool inventory + SEP-1577 sampling loop) and `autonomous_system_troubleshooter` (3-phase: health/events/processes → sampling → root cause). Both use `ctx.sample()` correctly.
- **`app.py`**: Added `version`, `instructions`, `strict_input_validation`, `mask_error_details`, `client_log_level` to `FastMCP(...)`. SkillsDirectoryProvider and prefab registration moved into lifespan.
- **`transport.py`**: `run_stdio_async()` / `run_http_async()` / `run_sse_async()` (removed in FastMCP 3.2) replaced with `mcp_app.run_async(transport=...)`.
- **`pyproject.toml`**: Build backend switched from `setuptools` to `hatchling`. Author placeholder replaced with real author. Added `starlette` dep. Added `[apps]` optional dep.
- **`__init__.py`**: Version synced to 0.3.0; stale FastMCP 2.13 reference removed.

---

## [0.2.0] - 2026-04-02

### Changed
- **Async Tool Resolution**: Refactored `server.py` to correctly `await mcp.get_tool(name)`, resolving `TypeError` when calling tools in FastMCP 3.1+.
- **Modernized Linting**: Replaced legacy linters (Black, isort, pylint, mypy) with **Ruff** for faster, unified linting and formatting.
- **Type Annotations**: Modernized type hints to Python 3.9+ standards (using `dict` instead of `Dict`, etc.) via `ruff --fix`.

### Fixed
- Resolved `RuntimeWarning: coroutine 'FastMCP.get_tool' was never awaited` which prevented tool execution.
- Fixed 157 linting and formatting issues across the codebase.
- Improved error handling in `_run_tool` with async resolution logic.

---

## [0.1.0] - 2025-10-21

---

## How to Update This File

When making changes, add them under the appropriate section:
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
