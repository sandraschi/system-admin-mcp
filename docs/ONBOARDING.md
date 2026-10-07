# Onboarding — system-admin-mcp

## What this is

Windows system administration through AI: NTFS file recovery, ACL/security management,
disk maintenance, service + process orchestration, crash postmortem — via MCP tools
(Claude Desktop) and a React dashboard (ports 10860/10861).

## What you need

- **Windows 11 + Administrator terminal.** Disk ops, service management, file recovery
  and permission changes call elevated APIs. Without elevation the tools return
  `status: error` (nothing destructive happens silently).
- **No account, no API key, no money.** Everything runs locally (WMI, psutil, Win32 APIs).
- Optional: Ollama (`:11434`) or LM Studio (`:1234`) for the Chat page (backend proxy only).

## 5-minute path

1. Right-click terminal → **Run as Administrator**.
2. `git clone https://github.com/sandraschi/system-admin-mcp && cd system-admin-mcp`.
3. `just setup` (Python deps + webapp `npm install`), then `just bootstrap` (pre-commit hooks).
4. `.\start.ps1` — backend on 10861, dashboard on 10860. The dashboard hero shows a
   backend status dot: green = connected, pulsing = still starting, red = see TROUBLESHOOTING.
5. Safe first moves: Dashboard → `health_check`; Tools → `system_admin(operation="list_services")`;
   **dry-run first** on anything mutating (`disk_cleanup(..., dry_run=True)`).

## Sanity check

```powershell
Invoke-WebRequest "http://127.0.0.1:10861/api/health" -UseBasicParsing   # {"status":"ok"}
just test   # 99 passed expected (coverage gate may fail independently — see TROUBLESHOOTING)
```

## Pitfalls

- Non-admin terminal → elevation errors everywhere (re-launch elevated, don't debug further).
- Opening the dashboard via `http://goliath:10860` while the backend only allows proxied
  same-origin calls → use `localhost` or read the CORS section in TROUBLESHOOTING.
- `optimize_ssd` is SSD-only; `defragment_disk` is HDD-only. The tools don't stop you —
  know your drive type first (`get_volume_info`).
