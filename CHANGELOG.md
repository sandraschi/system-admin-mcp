
## [Unreleased] — 2026-10-08 (webapp gap fill Phase 1)

### Added
- **Metrics card** on status page (`GET /api/metrics`: net I/O + load avg).
- **One-click Ollama install**: shared `InstallOllamaButton` (POST install +
  status polling) on the dashboard onboarding-cue and the Ollama provider card.
- **Legacy decisions**: `/api/chat` kept + tested (422 contract);
  `/api/v1/diagnostics` documented as test-only.

## [Unreleased] — 2026-10-08 (cloud providers + dual-GPU)

### Added
- **Cloud provider stack** (fleet §VI.10): vendored `llm_providers.py`
  (16 providers: 3 local + 13 cloud), 0600 keystore (`data/llm_keys.json`,
  env wins, `SYSTEMADMIN_LLM_KEYSTORE` test override), full endpoint set
  (`providers/models/test/settings/chat+stream/onboarding/install/gpus/
  ollama-state`), verified live against Ollama (chat + SSE verbatim).
- **Dual-GPU placement + resident-first** (§VI.8/9): target-GPU select,
  VRAM-filtered dropdowns, `llm_gpu` persistence, `/api/ps`-aware defaults.
- **Frontend**: `lib/llm.ts` (streamChat), provider cards with key save/test/
  clear, dashboard `onboarding-cue`, chat migrated to streaming SSE.
- **Tests**: `tests/test_llm_stack.py` (21 tests incl. live-Ollama stream,
  no-key-leak, key roundtrip). New `docs/LLM.md`.

## [Unreleased] — 2026-10-07 (assfix final: bun + zustand + tauri)

### Fixed
- **Bun migration (Phase 1)**: `bun.lock` committed, `package-lock.json` deleted;
  justfile/CI/build.ps1/start.ps1 on bun (fleet engine `PackageManager: bun`);
  Node stays for Vite/Tauri CLIs. `bun run dev` + `bun run build` verified.
- **Zustand LLM store**: new `store/llm.ts` + `lib/provider.ts`; chat + settings
  share provider/model/detection/GPU state (persisted `llm_provider`/`llm_model`).
- **Tauri audit**: dedicated operator ports (native 11239/11240, side-by-side
  rule); `BACKEND_PORT=11240`; api.ts Tauri branch baked to operator port;
  `run_server.py` frozen stderr guard + eager `_strptime`/`mcp.types`;
  spec gains `joserfc*` + `mcp` metadata; build.ps1 size gate (5 MB) + frozen
  smoke test; `main.rs` child `wait()`.
- **Strict tsc fixes**: narrowed `tool.parameters`, `stats.uptime`, tool filter.

## [Unreleased] — 2026-10-07 (assfix follow-up)

### Fixed
- **Coverage gate green**: 9.5% -> 42.9% via `tests/test_assfix_coverage.py`
  (58 hermetic tests: transport, prompts, monitoring, system_ops, full REST
  surface, minidump parsers, dispatch, main, lifespan, resources).
- **Annotated+Field migration (tool surface)**: all 59 `@mcp.tool` signatures now
  `Annotated[..., Field(description=...)]`; `Args:` blocks removed; added
  `pydantic>=2.0` dependency. Schemas verified live (descriptions + hints).
- **Tool annotations**: 59/59 tools carry `ToolAnnotations` (34 read-only,
  destructive on recovery/ACL/cleanup/defrag/startup/portmanteau).
- **CORS-absolute URL (missed HIGH, self-found)**: `lib/api.ts` is now
  same-origin except behind a Tauri gate — 14 pages fixed by the one-line root.
- **Fleet Apps Hub**: new `GET /api/fleet/apps` (registry + listener scan);
  `apps.tsx` rewritten as live discovery (loading/error/empty/refresh).
- **MCP resources**: `systemadmin://status` + `systemadmin://config`.
- **Settings**: loading/error states, GPU row + no-LLM opportunity prompt.
- **Dashboard**: Tauri `backend-status` listener with HTTP-poll fallback.
- **renovate.json** (fleet standard); `is_admin()` returns real `bool`;
  `just build` uses `--all-extras` (plain `uv sync` pruned pytest).
- Removed PS7-only legacy scripts blocking the 5.1 gate (in history).

### Deferred (open, with reasons)
- npm -> bun; Zustand LLM store (per-page state works; migration needs both
  chat+settings moved atomically); `help.tsx` is static (no async state to guard).

### Fixed
- **CI valid again**: Pyright step de-indented (was invalid YAML — type gate never ran); `actionlint` clean.
- **Ruff S110/S112/T20 enforced**: dropped `S110`/`S112` from ignore, added `T20`; 30 silent
  `except: pass/continue` now `logger.debug(..., exc_info=True)`; `__main__`/CLI prints covered by
  per-file-ignores (`user_bridge/bridge.py`, `elevated_service/service.py`).
- **Pyright 1 -> 0 errors**: `None` guard on minidump `csd` string (`implementations.py`).
- **Justfile**: all recipe bodies `;`-joined (lone `Set-Location` lines never applied); fixed broken
  `setup` recipe (mixed indent — `just --list` failed); `e2e`/`e2e-install` use joined `Set-Location`.
- **Webapp**: added `@tauri-apps/api ^2.2.0` (required with `native/`); `tsc` + `biome` green.
- **MCPB**: `scripts/mcpb-pack.ps1` shim → canonical fleet pack script (`just mcpb-pack` works again).
- **Tool docstrings**: `## Return Format` + `## Examples` on all 3 portmanteau wrappers.
- **Docs**: new `docs/CONFIGURATION.md`, `DEVELOPMENT.md`, `TOOLS.md`, `TROUBLESHOOTING.md`,
  `docs/ONBOARDING.md`; `glama.json` tools count 44 -> 63; fleet pre-commit template
  (`.pre-commit-config.yaml` + hook installed) and `.gitattributes` (LF) vendored.
- **Fleet launcher**: `mcp-central-docs/starts/system-admin-mcp-start.bat` created (README row existed).

### Deferred (open, with reasons)
- Coverage gate red (9.5% vs `--cov-fail-under=20`): needs a test-writing pass, not a config tweak.
- `Args:` -> `Annotated+Field` docstring migration: signature-level refactor, see `docs/TOOL_DOCSTRING_MIGRATION.md`.
- Tool `annotations=` (READ_ONLY/MUTATING): per-tool judgment call, follow-up run.
- npm -> bun migration: repo is consistently npm+package-lock; switch risks lock churn.
- Zustand LLM store, fleet `/api/fleet/apps` discovery, Tauri `backend-status` listen, GPU prompt,
  page error/empty states: webapp follow-up batch.

## [Unreleased] — 2026-08-07 (assfix re-run)

### Fixed
- **pyright clean (149 → 0 errors)**: awaited `ctx.info`/`ctx.report_progress` calls in agentic
  workflows; `ctx.sample()` positional `messages` + `cast(Any, ...)` for `SamplingResult`;
  `os.getloadavg` via `getattr` (Windows); `CREATE_NEW_CONSOUSE_WINDOW` typo → `CREATE_NEW_CONSOLE`;
  `asyncio.TimeoutExpired` → `TimeoutError` (dup except removed); `wmi` module bound as `Any`;
  unbound `tool_name`/`log_dir`/`command`; `dict[str, Any]` annotations for mixed-value results;
  pywin32/prefab stub gaps silenced with typed ignores (pyright codes).
- **CI**: pyright step flipped to blocking (was non-blocking with 149 errors).
- **Coverage gate**: `--cov-fail-under=20` added (total 22.8%).
- **justfile**: added `cua-nsis-test` + `cua-webapp-test` recipes (fleet CUA scripts committed).
- Removed 10 stale `.bak` page files from `web_sota/src/pages`.

### Remaining (deferred, MEDIUM)
- data-testid density (<3/page on several pages), `text-xs` x67, low-contrast
  `text-slate-400/500` x111, `print()` in bridge/service debug paths, `@mcp.resource()` absent.

## [Unreleased] — 2026-08-01

### Fixed
- Tests: `UserBridge` missing `get_disk_usage`/`get_process_info` methods; `win32con.FILE_*`
  constants missing from pywin32 (now local constants); `cpu_percent(percpu=True)` mock shape;
  `is_admin` test now patches the module attribute; live-system edge-case tests marked
  `integration` (excluded from default run — no more hangs); tool-registration tests use the
  public `mcp.list_tools()` API.
- `recover_file` placeholder replaced with a real bridge-backed implementation returning
  structured errors instead of raising.
- Tool modules now imported from `app.py` — registration happens on package import, not only
  via `main.py`.
- Chat page was a fake echo placeholder; now wired to a real `POST /api/chat` (Ollama/LM Studio).
- Dashboard was fully static; now live KPIs + hero section.
- Removed the fabricated "Elevated Operations" page (hardcoded counts + fake console telemetry).
- CORS: added fleet `allow_origin_regex` + Tauri origins.
- httpx/log spam silenced in the ring buffer.

### Added
- `POST /api/chat`, `GET /api/llm/discover`, `GET /api/skills`, `GET /api/v1/diagnostics`,
  `POST /api/shutdown` REST endpoints.
- Skills page + sidebar entry; LLM provider/model selectors with `data-testid` on Chat + Settings.
- Session context injection: `.claude-plugin/plugin.json` + `hooks/hooks.json`,
  `## Session Context` in `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`,
  `.opencode/skills/session-context/SKILL.md`.
- MCPB prompts expanded to 3-4-100: system.md 3969 words, user.md 4135 words (examples.json 110).
- pyright dev dependency (149 pre-existing type errors — adoption in progress, CI non-blocking).

### Changed
- CI: python 3.12 (was 3.11), biome + tsc + pyright gates, pytest/ruff now blocking,
  triggers on push/PR. actionlint clean.
- `glama.json` refreshed: FastMCP 3.4.4, 44 tools, streamable-http transport.
- `.gitignore`: `.env`, `node_modules/`, `*.mcpb`, `*.bak`, `reports/`; tracked `.bak` files removed.
- pytest.ini: `-m "not integration"` default.

## [Unreleased] — 2026-06-14

### Added
- Tauri native wrapper (native/ directory) with bundle.resources + std::process::Command
- CUA-NSIS: just cua-nsis-test recipe, scripts/cua-smoke.py, scripts/cua-nsis-config.json
- Tauri CORS: tauri://localhost origins for WebView API access
- NSIS installer at dist/ and native/target/release/bundle/nsis/

### Changed
- Frontend API calls use absolute http://127.0.0.1:{port} URLs in production build
- CORS middleware includes allow_origin_regex for tauri.localhost
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
