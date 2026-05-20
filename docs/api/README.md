# REST API Reference

The FastAPI backend runs on `WEBAPP_PORT` (default 10861). All endpoints are prefixed with `/api`.

## Health & Status

### `GET /api/health`

```json
{ "status": "ok", "timestamp": "...", "service": "system-admin-mcp" }
```

### `GET /api/status`

System info + service uptime + CPU/memory/disk metrics.

```json
{
  "service": "system-admin-mcp",
  "version": "0.4.0",
  "status": "healthy",
  "uptime": 3600,
  "system": { "cpu_usage_percent": 23, "memory": {...}, "disk": {...} },
  "timestamp": "..."
}
```

### `GET /api/metrics`

CPU count, load average, network bytes.

### `GET /api/tools`

Lists all registered MCP tools with schemas (uses `mcp.list_tools()`).

## Processes

### `GET /api/processes`

Query params: `filter_name`, `filter_user`, `sort_by` (cpu|memory|name|pid).

```json
{ "processes": [{ "pid": 1234, "name": "chrome.exe", "cpu_percent": 12.5, "memory_mb": 340.2, "status": "running" }] }
```

### `GET /api/processes/{pid}`

Detailed process info via `analyze_process`: threads, handles, open connections, children.

```json
{ "status": "success", "process": { "pid": 1234, "name": "...", "connections": [...], "children": [...] } }
```

## Services

### `GET /api/services`

Query params: `filter_status` (running|stopped|all), `filter_name`, `include_system` (bool).

```json
{ "services": [{ "name": "Spooler", "display_name": "Print Spooler", "status": "Running", "startup_type": "Automatic" }] }
```

## Volumes & Disk

### `GET /api/volumes`

List all drives with type.

```json
{ "volumes": [{ "drive": "C:\\", "type": 3 }, ...] }
```

### `POST /api/disk_usage`

Body: `{ "path": "C:\\" }`

Returns total, used, free bytes.

## File Operations

### `POST /api/file_owner`

Body: `{ "path": "C:/Windows/notepad.exe" }`

```json
{ "file": "...", "owner": "BUILTIN\\Administrators", "sid": "S-1-5-..." }
```

### `POST /api/recover_file`

Body: `{ "original_path": "...", "output_dir": "..." }`

## Logs

### `GET /api/logs`

Query params: `tail` (default 200), `file` (specific log file).

Reads from `%LOCALAPPDATA%\SystemAdminMCP\Logs\`.

## MCP Tool Bridge

### `POST /api/tools/call`

Execute any MCP tool by name. Body: `{ "name": "system_admin", "arguments": { "operation": "health_check" } }`

```json
{ "status": "success", "result": { ... } }
```
