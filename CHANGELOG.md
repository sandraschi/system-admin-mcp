# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
