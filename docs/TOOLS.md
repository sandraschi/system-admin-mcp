# Tools — system-admin-mcp

63 `@mcp.tool` decorators total (`glama.json` count is authoritative — keep in sync).

## Portmanteau (primary surface)

| Tool | Operations |
|---|---|
| `system_admin` | 40+ ops: `scan_volume`, `recover_file`, `validate_recovery`, `batch_recover`, `get_permissions`, `set_permissions`, `remove_permission`, `take_ownership`, `audit_permissions`, `get_volume_info`, `check_disk_health`, `analyze_disk_usage`, `disk_cleanup`, `defragment_disk`, `optimize_ssd`, `analyze_top_folder_sizes`, `get_hardware_info`, `get_os_info`, `get_installed_software`, `get_performance_metrics`, `get_event_log`, `get_recent_event_errors`, `health_check`, `check_system_health_status`, `get_top_resource_processes`, `audit_network_ports`, `list_crash_dumps`, `get_bugcheck_history`, `analyze_minidump`, `windbg_analyze`, `audit_admin_toolbox`, `get_firmware_posture`, `audit_scheduled_tasks`, `get_update_status`, `audit_local_admins`, `audit_smb_shares`, `list_shadow_copies`, `audit_drivers`, `get_reliability_history`, `winget_outdated`, `audit_path_dross`, `list_services`, `get_service_stats`, `get_service_info`, `start_service`, `stop_service`, `set_service_startup`, `list_processes`, `analyze_process`, `kill_process`, `list_startup_programs`, `add_startup_program`, `remove_startup_program`, `find_taskbar_blocking_processes`, `kill_taskbar_blocking_processes`, `get_taskbar_settings`, `set_taskbar_autohide`, `list_taskbar_windows`, `list_tray_icons` |
| `manage_filesystem_watch` | `start` / `stop` / `list` / `get_events` (watchdog; experimental `auto_sample` via `ctx.sample()`) |
| `get_comprehensive_diagnostics` | health + top-5 processes + recent errors + primary-volume usage in one call |

## Agentic (SEP-1577 sampling)

| Tool | Purpose |
|---|---|
| `agentic_system_workflow` | Borrows client LLM via `ctx.sample()` to orchestrate multi-step diagnostics |
| `autonomous_system_troubleshooter` | 3-phase autonomous diagnosis (scan → sample → root cause) |

## Standalone (`tools/system_ops.py`)

`list_volumes`, `get_file_owner`, `recover_file`, `get_disk_usage`, `get_process_info`,
`ping`, `get_system_info`, `help`, `status`, startup/taskbar helpers. Thin wrappers kept for
direct tool-call ergonomics; new logic belongs in the portmanteau.

## Prefab UI (`@mcp.tool(app=True)`)

`system_health_card`, `top_processes_card`, `list_services_card`, `volume_status_card`
— `ToolResult` + `structured_content=PrefabApp(...)`. Disabled with `SYSADMIN_PREFAB_APPS=0`.

## Prompts (`prompts.py`, 5 registered)

`system_diagnostics_expert`, `security_hardening_expert`, `system_troubleshooter`,
`volume_maintenance_expert` (+1 domain prompt). No `@mcp.resource()` yet (open item).

## Safety conventions

- Destructive ops are dry-run-first (`dry_run=True` previews).
- Kill pattern: `analyze_process(pid)` → `kill_process(pid, force=false)` → `force=true` only if needed.
- Elevation-gated ops return `status: error` with a clear message instead of failing silently.
