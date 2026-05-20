# Quickstart

Get System Admin MCP running in 2 minutes.

## Prerequisites

- **Windows 10/11** (this is a Windows-only server)
- **Python 3.12+** — [Download](https://python.org)
- **uv** — `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Administrator privileges** — required for disk ops, services, file recovery

---

## The Elevation Problem

This server calls Windows APIs that need admin rights (disk operations, service management, file recovery). How you provide elevation is up to you:

| Setup | Elevation method |
|-------|-----------------|
| **Run Claude Desktop as Admin** (easiest) | Right-click → Run as Administrator. Server inherits elevation via stdio. **Everything works.** |
| **HTTP mode** | Run server elevated in a terminal, Claude connects via SSE. |
| **Elevated Service** (advanced) | SYSTEM-level Windows service + named-pipe bridge. |

---

## Option A: Run Claude Desktop as Administrator (Easiest)

Right-click Claude Desktop → **Run as Administrator**. Then use the standard stdio config:

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "uvx",
      "args": ["system-admin-mcp"]
    }
  }
}
```

The server inherits Claude's elevated token — every operation works, no extra steps.

> **Note:** Some Claude features (clipboard, file access) may behave differently when elevated. Test once; if that bothers you, use HTTP mode instead.

---

## Option B: HTTP Mode

### 1. Start server elevated

```powershell
# Run this terminal AS ADMINISTRATOR
cd system-admin-mcp
uv run system-admin-mcp --http
# → Server listens on http://127.0.0.1:10861/mcp
```

### 2. Configure Claude Desktop

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "cmd.exe",
      "args": ["/c", "echo", "connect via SSE"],
      "url": "http://127.0.0.1:10861/mcp",
      "type": "sse"
    }
  }
}
```

### 3. Verify

```
system_admin(operation="health_check")
system_admin(operation="list_services", filter_status="running")
```

---

## Option B: Claude Desktop stdio (Partial)

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "uvx",
      "args": ["system-admin-mcp"]
    }
  }
}
```

**What works without elevation:** health_check, get_performance_metrics, get_hardware_info, get_os_info, get_installed_software, list_processes, analyze_process, get_taskbar_settings, find_taskbar_blocking_processes.

**What needs elevation:** list_services, start_service, stop_service, scan_volume, recover_file, get_permissions, set_permissions, take_ownership, check_disk_health, disk_cleanup, defragment_disk, optimize_ssd, kill_process.

For those, you'll get `"error": "Administrator privileges required"`.

---

## Option C: Elevated Service Bridge (Advanced)

Install the elevated Windows service once (requires admin one time), then run the MCP server **unelevated** normally.

### 1. Install the service (run this once as Administrator)

```powershell
# Run this terminal AS ADMINISTRATOR
cd system-admin-mcp
uv run python src/system_admin_mcp/elevated_service/service.py install
uv run python src/system_admin_mcp/elevated_service/service.py start
```

### 2. Run MCP server unelevated

```powershell
# Normal user terminal — no admin needed
uv run system-admin-mcp
# Privileged operations go through the named-pipe bridge
```

The service runs as SYSTEM and handles elevated calls via `\\.\pipe\SystemAdminMCP`. The `UserBridge` client forwards ops automatically.

> **Note**: Currently only `get_file_owner`, `get_disk_usage`, and `get_process_info` use the bridge. Other tools still check `IsUserAnAdmin()` directly. The bridge coverage will expand.

---

## First Commands

Once connected, try:

```
system_admin(operation="health_check")
system_admin(operation="get_system_info")
system_admin(operation="get_performance_metrics")
system_admin(operation="list_processes", sort_by="cpu")
system_admin(operation="list_services", filter_status="running")
system_admin(operation="get_volume_info", drive="C:")
system_admin(operation="check_disk_health", drive="C:")
```

See [README](../README.md) for the full operation list.

---

## Web Dashboard

```powershell
# Terminal 1 — backend API (as Administrator)
cd system-admin-mcp
uv run system-admin-mcp --web

# Terminal 2 — frontend
cd system-admin-mcp/web_sota
npm install
npm run dev
```

Open http://localhost:10860

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Administrator privileges required" | Run terminal as Admin, or use HTTP mode |
| Module not found | `uv sync` |
| Port conflict | Set `WEBAPP_PORT=10862` and `MCP_PORT=10862` |
| Server starts then dies | Check stderr for import errors |
| Named pipe not found (bridge) | `uv run python src/system_admin_mcp/elevated_service/service.py start` as Admin |
