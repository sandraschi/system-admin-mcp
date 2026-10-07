# Troubleshooting — system-admin-mcp

## Backend looks healthy but dashboard says unreachable

curl/`Invoke-WebRequest` to localhost proves nothing about browser tabs. The frontend
uses same-origin `/api` (Vite proxy) — verify both paths:

```powershell
Invoke-WebRequest "http://127.0.0.1:10860/api/v1/health" -UseBasicParsing        # vite proxy
Invoke-WebRequest "http://127.0.0.1:10861/api/v1/health" -UseBasicParsing `
  -Headers @{ Origin = "http://goliath:10860" } | % { $_.Headers["Access-Control-Allow-Origin"] }
```

If the second returns nothing, a tab on `http://goliath:10860` is CORS-dead. Fix the
URL (same-origin + Tauri gate), never widen origins to cover dev hostnames.

## Port already in use / zombie backend

`start.ps1` clears zombies before bind. Manual: find the PID on 10861 and stop it —
never kill an NSSM child (none here; this repo runs as a user process).

## `pytest` fails on coverage, tests pass

Default run enforces `--cov-fail-under=20` (`pytest.ini`). `transport.py` (0%) and
`user_bridge/bridge.py` (16%) drag the total under 20. Run `pytest --no-cov -q` for a
pure behavior check; raising coverage needs a dedicated test-writing pass (open item).

## Elevation errors on disk/service/recovery ops

Re-run the terminal **as Administrator** (right-click → Run as Administrator).
Ops check `IsUserAnAdmin()` and return `status: error` when not elevated — by design.

## `just <recipe>` fails with weird cwd errors

Fixed 2026-10-07: every recipe body is now `;`-joined on one line (just runs each
*line* as a separate `powershell.exe`, so a lone `Set-Location` line never applied).
Validate with `just --list` after editing the justfile.

## CI red on `actionlint` / Pyright step missing

Fixed 2026-10-07: the Pyright step was over-indented (invalid YAML). After editing
`.github/workflows/ci.yml`, run `actionlint` locally
(`C:\Users\sandr\.local\bin\actionlint.exe`) before pushing.

## LLM chat says "unavailable"

Start Ollama (`:11434`) or LM Studio (`:1234`); Settings → providers shows detection.
Chat posts to the backend proxy (`POST /api/llm/chat`) — keys never leave the server.

## Minidump/WMI fields missing (`null`)

Best-effort probes by design: unparseable streams log at `debug` and continue with
partial data. Re-run with `LOGLEVEL=DEBUG` (or check `logs/`) for the skipped reason.
