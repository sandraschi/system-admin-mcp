# Build Log — system-admin-mcp (NSIS)

Running record for native builds (fleet NSIS gate requires this file).

## 2026-10-07 — full pipeline green (Goliath)

Command: `powershell -NoProfile -ExecutionPolicy Bypass -File native/build.ps1`
Result: **PASS**, exit 0. Full log: `C:\Users\sandr\AppData\Local\Temp\opencode\nsis.log`
(volatile scratch; key lines mirrored below).

- [1/4] Frontend (web_sota): `bun install` + `bunx tsc --noEmit` + `bun run build`
  (Vite 7.3.1, 1830 modules, CSS 37 kB). First build caught 3 strict-tsc errors
  from the zustand typing pass (`tool.parameters?`, `stats.uptime`,
  `t.description ?? ""`) — fixed, rebuilt clean.
- [2/4] PyInstaller backend: used `.venv\Scripts\pyinstaller.exe` (project env,
  not the global uv-tool env pitfall). Output `dist/system-admin-mcp-backend.exe`
  **32.7 MB** (Gate 0: ≥ 5 MB pass).
- [3/4] Embed + frozen smoke test: backend booted on scratch port **11999**,
  `GET /api/health` → 200 (proves the `run_server.py` frozen stderr guard,
  eager `_strptime`/`mcp.types` imports, and `joserfc` hiddenimports).
  Bundled `.env.example` (never `.env`).
- [4/4] `npx @tauri-apps/cli build --bundles nsis` (Tauri finds NSIS makensis):
  `native/target/release/bundle/nsis/System Admin MCP_0.1.0_x64-setup.exe`
  (**34.86 MiB**), staged to `dist/`. Stray `target/release/*-backend.exe`
  cleaned by the script.

Audit fixes that made this build compliant (same day, pre-build):
- Dedicated operator ports claimed: native frontend **11239** / backend **11240**
  (`system-admin-mcp-native` rows in WEBAPP_PORTS.md); `BACKEND_PORT=11240`
  in `native/src/backend.rs` (was dev port 10861 — side-by-side violation);
  `lib/api.ts` Tauri branch baked to 11240.
- `system-admin-mcp-backend.spec`: `joserfc*` + `mcp.types` hiddenimports,
  `mcp`/`opentelemetry` dist-info preserved.
- `main.rs`: `child.wait()` after `kill()` on exit.

Known non-blockers:
- Backend runs on 10861 in dev; port is currently squatted by a stale
  2026-10-06 backend (not this repo's; access-denied to kill). Installed app
  uses 11240, so no conflict.
- `pyi-smoke.log` in `dist/` is 0 bytes on success (kept as success marker).
