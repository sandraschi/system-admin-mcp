import json
import logging
import os
from datetime import datetime
from typing import Annotated, Any, Literal

from fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from system_admin_mcp.app import mcp

# Fleet tool-annotation standard (TOOL_DESIGN_STANDARDS.md S9). The portmanteau
# fans out to destructive ops (kill/defrag/ACL), so it is marked destructive.
_DESTRUCTIVE = ToolAnnotations(destructiveHint=True)
_READ_ONLY = ToolAnnotations(readOnlyHint=True)
_MUTATING = ToolAnnotations()
from system_admin_mcp.tools.implementations import (
    airgap_disable,
    airgap_enable,
    airgap_status,
    analyze_disk_usage_advanced,
    analyze_minidump,
    analyze_top_folder_sizes,
    audit_admin_toolbox,
    audit_drivers,
    audit_local_admins,
    audit_network_ports,
    audit_path_dross,
    audit_permissions,
    audit_scheduled_tasks,
    audit_smb_shares,
    check_disk_health,
    check_system_health_status,
    defragment_disk,
    disk_cleanup,
    get_bugcheck_history,
    get_defender_status,
    get_event_log,
    get_firmware_posture,
    get_gpu_info,
    get_gpu_processes,
    get_hardware_info,
    get_installed_software,
    get_os_info,
    get_performance_metrics,
    get_permissions,
    get_recent_event_errors,
    get_reliability_history,
    get_tailscale_status,
    get_top_resource_processes,
    get_update_status,
    get_volume_info,
    get_vpn_status,
    health_check,
    list_crash_dumps,
    list_shadow_copies,
    optimize_ssd,
    recover_file_ntfs,
    remove_permission,
    scan_volume,
    set_permissions,
    take_ownership,
    validate_recovery,
    windbg_analyze,
    winget_outdated,
)
from system_admin_mcp.tools.monitoring import watcher_manager
from system_admin_mcp.tools.services_and_tasks import (
    add_startup_program,
    analyze_process,
    find_taskbar_blocking_processes,
    forensic_scan,
    get_service_info,
    get_service_stats,
    get_taskbar_settings,
    kill_process,
    kill_taskbar_blocking_processes,
    list_processes,
    list_services,
    list_startup_programs,
    list_taskbar_windows,
    list_tray_icons,
    remove_startup_program,
    set_service_startup,
    set_taskbar_autohide,
    start_service,
    stop_service,
)


@mcp.tool(task=True, annotations=_MUTATING)
async def manage_filesystem_watch(
    operation: Annotated[str, Field(description="Operation: start, stop, list, get_events")],
    path: Annotated[str | None, Field(description="Path to monitor (required for start/stop)")] = None,
    recursive: Annotated[bool, Field(description="Whether to monitor subdirectories")] = True,
    auto_sample: Annotated[bool, Field(description="(Experimental) Use ctx.sample() to analyze events")] = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Manage background filesystem monitoring.

    Operations:
    - start: Begin monitoring a directory (recursive by default).
    - stop: Stop monitoring a directory.
    - list: List all active watches.
    - get_events: Retrieve captured filesystem events.

    ## Return Format
    `{success: bool, message: str, ...}` — `status` is `"success"` (with a
    human-readable `message`) or `"error"` (with an `error` string).
    `list` returns `active_watches`; `get_events` returns `count` + `events`.

    ## Examples
    ```python
    manage_filesystem_watch(operation="start", path="C:\\Data")
    manage_filesystem_watch(operation="get_events", path="C:\\Data")
    manage_filesystem_watch(operation="stop", path="C:\\Data")
    ```
    """
    from system_admin_mcp.mutation_guard import audit_mutation, require_mutable

    if operation in ("start", "stop"):
        audit_mutation(f"manage_watch_{operation}", {"path": path})
        require_mutable(f"manage_watch_{operation}")
    try:
        if operation == "start":
            if not path:
                raise ValueError("Path is required for start operation")
            watcher_manager.start_watch(path)
            return {"status": "success", "message": f"Started watching {path}", "path": path}

        elif operation == "stop":
            if not path:
                raise ValueError("Path is required for stop operation")
            watcher_manager.stop_watch(path)
            return {"status": "success", "message": f"Stopped watching {path}", "path": path}

        elif operation == "list":
            return {"status": "success", "active_watches": list(watcher_manager.watches.keys())}

        elif operation == "get_events":
            events = watcher_manager.get_events(path)

            # Agentic Sampling Logic (FastMCP 3.2)
            if auto_sample and events and ctx:
                await ctx.sample(
                    messages=[
                        {  # type: ignore[reportArgumentType]
                            "role": "user",
                            "content": (
                                f"I've detected {len(events)} filesystem events: {json.dumps(events[:5])}. "
                                "Please summarize if any of these are critical security or system integrity risks."
                            ),
                        }
                    ]
                )

            return {"status": "success", "count": len(events), "events": events}

        else:
            raise ValueError(f"Unknown operation: {operation}")

    except Exception as e:
        return {"status": "error", "error": str(e)}


logger = logging.getLogger(__name__)

# Lazy import UserBridge to avoid startup failures
try:
    from system_admin_mcp.user_bridge import UserBridge
except ImportError as e:
    logger.warning(f"Failed to import UserBridge: {e}. Bridge operations will not be available.")
    UserBridge = None  # type: ignore[reportAssignmentType]
except Exception as e:
    logger.warning(f"Failed to import UserBridge: {e}. Bridge operations will not be available.")
    UserBridge = None  # type: ignore[reportAssignmentType]

# Initialize user bridge lazily to avoid startup errors
_bridge = None


def get_bridge() -> Any | None:
    """Get or create the user bridge instance."""
    global _bridge
    if UserBridge is None:
        return None
    if _bridge is None:
        try:
            _bridge = UserBridge()
        except Exception as e:
            logger.warning(f"Failed to initialize UserBridge: {e}. Some operations may not be available.")
            _bridge = None
    return _bridge


@mcp.tool(annotations=_DESTRUCTIVE)
async def system_admin(
    operation: Annotated[
        Literal[
            # File Recovery
            "scan_volume",
            "recover_file",
            "validate_recovery",
            "batch_recover",
            # Security Management
            "get_permissions",
            "set_permissions",
            "remove_permission",
            "take_ownership",
            "audit_permissions",
            "modify_acl",
            # Protection posture (basic status; full mesh mgmt lives elsewhere)
            "get_defender_status",
            "get_vpn_status",
            "get_tailscale_status",
            # Airgap kill switch (confirm-gated, read-only-blocked)
            "airgap_status",
            "airgap_enable",
            "airgap_disable",
            # Volume Maintenance
            "check_disk_health",
            "analyze_disk_usage",
            "disk_cleanup",
            "defragment_disk",
            "optimize_ssd",
            "get_volume_info",
            # System Diagnostics
            "get_gpu_info",
            "get_gpu_processes",
            "get_hardware_info",
            "get_os_info",
            "get_installed_software",
            "get_performance_metrics",
            "get_event_log",
            "get_recent_event_errors",
            "health_check",
            "check_system_health_status",
            "get_top_resource_processes",
            "audit_network_ports",
            "analyze_top_folder_sizes",
            "get_comprehensive_diagnostics",
            "forensic_scan",
            # Crash Postmortem
            "list_crash_dumps",
            "get_bugcheck_history",
            "analyze_minidump",
            "windbg_analyze",
            "audit_admin_toolbox",
            # System audit
            "get_firmware_posture",
            "audit_scheduled_tasks",
            "get_update_status",
            "audit_local_admins",
            "audit_smb_shares",
            "list_shadow_copies",
            "audit_drivers",
            "get_reliability_history",
            "winget_outdated",
            "audit_path_dross",
            # Windows Services
            "list_services",
            "get_service_stats",
            "get_service_info",
            "start_service",
            "stop_service",
            "set_service_startup",
            # Tasks/Processes
            "list_processes",
            "analyze_process",
            "kill_process",
            # Windows Startup
            "list_startup_programs",
            "add_startup_program",
            "remove_startup_program",
            # Taskbar Management
            "find_taskbar_blocking_processes",
            "kill_taskbar_blocking_processes",
            "get_taskbar_settings",
            "set_taskbar_autohide",
            "list_taskbar_windows",
            "list_tray_icons",
        ],
        Field(description="The operation to perform (required)"),
    ],
    # File Recovery parameters
    drive: Annotated[str | None, Field(description='Drive letter for volume ops, e.g. "C:"')] = None,
    file_pattern: Annotated[str | None, Field(description='File glob for scanning, e.g. "*.docx"')] = None,
    mft_entry: Annotated[int | None, Field(description="MFT entry number for file recovery")] = None,
    source_path: Annotated[str | None, Field(description="Source file path for recovery")] = None,
    destination_path: Annotated[str | None, Field(description="Destination path for recovered file")] = None,
    verify_integrity: Annotated[bool, Field(description="Verify file integrity after recovery")] = True,
    max_results: Annotated[int, Field(description="Maximum results for scanning", ge=1)] = 100,
    # Security parameters
    path: Annotated[str | None, Field(description="File/folder path for security operations")] = None,
    principal: Annotated[str | None, Field(description='User/group for permission ops, e.g. "DOMAIN\\User"')] = None,
    rights: Annotated[str | None, Field(description="Permission rights: Read, Write, Modify, FullControl")] = None,
    inheritance: Annotated[str | None, Field(description="Inheritance setting for permissions")] = None,
    # Volume parameters
    cleanup_targets: Annotated[
        list[str] | None, Field(description="Cleanup targets: temp_files, recycle_bin, etc.")
    ] = None,
    dry_run: Annotated[bool, Field(description="Preview changes without applying")] = True,
    thorough: Annotated[bool, Field(description="Thorough operation (defrag, etc.)")] = False,
    # Diagnostics parameters
    log_name: Annotated[str | None, Field(description="Event log name: System, Application, Security")] = None,
    level: Annotated[str | None, Field(description="Event log level: Error, Warning, Information")] = None,
    hours_back: Annotated[int, Field(description="Hours to look back in event logs", ge=1)] = 24,
    days_back: Annotated[int, Field(description="Days to look back (bugcheck/reliability)", ge=1)] = 7,
    dump_path: Annotated[str | None, Field(description="Path to crash dump for analysis")] = None,
    timeout_seconds: Annotated[int, Field(description="Timeout for long operations", ge=1)] = 120,
    class_filter: Annotated[str | None, Field(description="Driver class filter for audit_drivers")] = None,
    # Services parameters
    service_name: Annotated[str | None, Field(description="Service name for service operations")] = None,
    filter_status: Annotated[str | None, Field(description="Filter services/processes by status")] = None,
    filter_name: Annotated[str | None, Field(description="Filter by name (services/processes)")] = None,
    include_system: Annotated[bool, Field(description="Include system services in results")] = True,
    include_established: Annotated[bool, Field(description="Include ESTABLISHED connections in port audit")] = True,
    wait_timeout: Annotated[int, Field(description="Timeout for service start/stop", ge=1)] = 30,
    startup_type: Annotated[str | None, Field(description="Service startup type: Auto, Manual, Disabled")] = None,
    # Process parameters
    pid: Annotated[int | None, Field(description="Process ID for process operations")] = None,
    filter_user: Annotated[str | None, Field(description="Filter processes by username")] = None,
    sort_by: Annotated[str, Field(description="Sort processes by: cpu, memory, name")] = "cpu",
    page: Annotated[int, Field(description="Result page number", ge=1)] = 1,
    page_size: Annotated[int, Field(description="Results per page", ge=1, le=500)] = 50,
    force: Annotated[bool, Field(description="Force kill processes")] = False,
    # Startup parameters
    startup_name: Annotated[str | None, Field(description="Program name for startup operations")] = None,
    startup_command: Annotated[str | None, Field(description="Command/path for startup program")] = None,
    startup_location: Annotated[str, Field(description="Startup scope: HKCU or HKLM")] = "HKCU",
    # Taskbar parameters
    autohide: Annotated[bool | None, Field(description="Enable/disable taskbar autohide")] = None,
    process_names: Annotated[list[str] | None, Field(description="Process names for taskbar operations")] = None,
    # Confirm-gated operations (airgap): explicit per-call confirmation, never sticky
    confirm: Annotated[
        bool, Field(description="Explicit confirmation for confirm-gated ops (airgap_enable/disable)")
    ] = False,
) -> dict[str, Any]:
    """Comprehensive system administration portmanteau tool.

    PORTMANTEAU PATTERN: Consolidates 20+ system admin operations into unified interface.

    SUPPORTED OPERATIONS:

    File Recovery (NTFS):
    - scan_volume: Scan NTFS volume for deleted files
    - recover_file: Recover deleted file from NTFS volume
    - validate_recovery: Verify recovered file integrity
    - batch_recover: Recover multiple files efficiently

    Security Management:
    - get_permissions: Get file/folder permissions and ACLs
    - set_permissions: Set file/folder permissions
    - remove_permission: Remove specific permission
    - take_ownership: Take ownership of file/folder
    - audit_permissions: Audit security settings
    - get_defender_status: Defender realtime/signatures posture (basic)
    - get_vpn_status: Windows VPN profiles + connection state (basic)
    - get_tailscale_status: Tailscale installed/running/tailnet (basic; full mgmt in tailscale-mcp)
    - airgap_status: Read-only airgap state (firewall + bluetooth)
    - airgap_enable: CUT outside links, requires confirm=True every call
    - airgap_disable: Restore outside links, requires confirm=True every call
    - modify_acl: Modify Access Control List

    Volume Maintenance:
    - check_disk_health: Check disk SMART status and health
    - analyze_disk_usage: Analyze disk space usage
    - disk_cleanup: Clean up temp files and free space
    - defragment_disk: Defragment HDD (HDDs only!)
    - optimize_ssd: Optimize SSD with TRIM (SSDs only!)
    - get_volume_info: Get detailed volume information

    System Diagnostics:
    - get_hardware_info: Get comprehensive hardware details
    - get_os_info: Get operating system information
    - get_installed_software: List installed software
    - get_performance_metrics: Get real-time performance data
    - get_event_log: Query Windows event logs
    - health_check: Perform system health check

    Crash Postmortem:
    - list_crash_dumps: Inventory MEMORY.DMP, Minidump, LiveKernelReports, WER
    - get_bugcheck_history: Correlate 41/1001/6008/1074 shutdown-crash events
    - analyze_minidump: SDK-free minidump triage parse (code, faulting module)
    - windbg_analyze: Full !analyze -v via cdb.exe (needs Debugging Tools)
    - audit_admin_toolbox: Inventory dev/AI/tcom/office/admin toolbox apps

    System audit:
    - get_firmware_posture: SVM/TPM/Secure Boot/VBS/BIOS in one card
    - audit_scheduled_tasks: Task Scheduler listing
    - get_update_status: Last patch, pending reboot, uptime
    - audit_local_admins: Administrators members + local users
    - audit_smb_shares: Shares and open sessions
    - list_shadow_copies: VSS shadows (needs elevation)
    - audit_drivers: Signed driver inventory
    - get_reliability_history: Reliability Monitor records
    - winget_outdated: Upgradable packages
    - audit_path_dross: Missing/duplicate PATH entries

    Windows Services:
    - list_services: List Windows services with filtering
    - get_service_status: Get detailed service status
    - start_service: Start a Windows service
    - stop_service: Stop a Windows service
    - set_service_startup: Set service startup type (Auto/Manual/Disabled)

    Process/Task Management:
    - list_processes: List running processes with filtering
    - analyze_process: Analyze a specific process in detail
    - kill_process: Kill a process by PID
    - kill_processes_by_name: Kill all processes matching a name

    Windows Startup:
    - list_startup_programs: List programs that start with Windows
    - add_startup_program: Add a program to Windows startup
    - remove_startup_program: Remove a program from Windows startup

    Taskbar Management:
    - find_taskbar_blocking_processes: Find processes preventing taskbar autohide
    - kill_taskbar_blocking_processes: Kill processes blocking taskbar
    - get_taskbar_settings: Get current taskbar settings
    - set_taskbar_autohide: Enable/disable taskbar autohide
    - list_taskbar_windows: Visible taskbar buttons with process + autostart flags
    - list_tray_icons: Notification-area icons with tooltips + owner guesses

    Parameter details live on the signature via Annotated[..., Field(...)];
    only the params each operation needs are required (all default to None
    except listed defaults).

    ## Return Format
    `{status: "success" | "error", ...}` — every path returns a `status` key.
    Mutating ops return a human-readable `message`; destructive ops are
    dry-run-first (`dry_run=True` previews, `dry_run=False` applies).

    ## Examples:
        # Scan for deleted files
        system_admin("scan_volume", drive="C:", file_pattern="*.docx", max_results=50)

        # Recover file
        system_admin("recover_file", source_path="C:/deleted/file.docx", destination_path="D:/Recovery/")

        # Get permissions
        system_admin("get_permissions", path="C:/Windows")

        # Set permissions
        system_admin("set_permissions", path="D:/Shared", principal="DOMAIN\\User", rights="Read")

        # Check disk health
        system_admin("check_disk_health", drive="C:")

        # Disk cleanup
        system_admin("disk_cleanup", drive="C:", cleanup_targets=["temp_files", "recycle_bin"], dry_run=True)

        # Get hardware info
        system_admin("get_hardware_info")

        # Get event log
        system_admin("get_event_log", log_name="System", level="Error", hours_back=24)

        # List services
        system_admin("list_services", filter_status="running")

        # Start/stop service
        system_admin("start_service", service_name="Spooler")
        system_admin("stop_service", service_name="Spooler")

        # List processes
        system_admin("list_processes", filter_name="chrome", sort_by="memory")

        # Kill process
        system_admin("kill_process", pid=1234, force=False)

        # List startup programs
        system_admin("list_startup_programs")

        # Taskbar operations
        system_admin("find_taskbar_blocking_processes")
        system_admin("set_taskbar_autohide", enabled=True)
    """
    from system_admin_mcp.mutation_guard import require_mutable

    try:
        # Read-only kill switch: mutating ops refuse before anything executes.
        # Blocked attempts are already audit-logged inside each implementation.
        require_mutable(operation)
        # File Recovery operations
        if operation == "scan_volume":
            if not drive:
                raise ValueError("drive parameter required for scan_volume")
            return scan_volume(drive, file_pattern, max_results)

        elif operation == "recover_file":
            if not source_path or not destination_path:
                raise ValueError("source_path and destination_path required for recover_file")
            return recover_file_ntfs(source_path, destination_path)

        elif operation == "validate_recovery":
            if not destination_path:
                raise ValueError("destination_path required for validate_recovery")
            return validate_recovery(destination_path)

        elif operation == "batch_recover":
            # Batch recovery - recover multiple files
            if not source_path or not destination_path:
                raise ValueError("source_path and destination_path required for batch_recover")
            # For now, attempt single file recovery
            # Full batch recovery would require a list of files
            return recover_file_ntfs(source_path, destination_path)

        # Security Management operations
        elif operation == "get_permissions":
            if not path:
                raise ValueError("path parameter required for get_permissions")
            return get_permissions(path)

        elif operation == "set_permissions":
            if not path or not principal or not rights:
                raise ValueError("path, principal, and rights required for set_permissions")
            return set_permissions(path, principal, rights, inheritance)

        elif operation == "remove_permission":
            if not path or not principal:
                raise ValueError("path and principal required for remove_permission")
            return remove_permission(path, principal)

        elif operation == "take_ownership":
            if not path:
                raise ValueError("path parameter required for take_ownership")
            return take_ownership(path)

        elif operation == "audit_permissions":
            if not path:
                raise ValueError("path parameter required for audit_permissions")
            return audit_permissions(path)

        # Protection posture (basic status reads, no parameters)
        elif operation == "get_defender_status":
            return get_defender_status()

        elif operation == "get_vpn_status":
            return get_vpn_status()

        elif operation == "get_tailscale_status":
            return get_tailscale_status()

        elif operation == "modify_acl":
            if not path:
                raise ValueError("path parameter required for modify_acl")
            # modify_acl is similar to set_permissions but with more granular control
            # For now, use set_permissions
            if not principal or not rights:
                raise ValueError("principal and rights required for modify_acl")
            return set_permissions(path, principal, rights, inheritance)

        # Volume Maintenance operations
        elif operation == "check_disk_health":
            if not drive:
                raise ValueError("drive parameter required for check_disk_health")
            return check_disk_health(drive)

        elif operation == "analyze_disk_usage":
            if not drive:
                raise ValueError("drive parameter required for analyze_disk_usage")
            return analyze_disk_usage_advanced(drive)

        elif operation == "disk_cleanup":
            if not drive:
                raise ValueError("drive parameter required for disk_cleanup")
            return disk_cleanup(drive, cleanup_targets, dry_run)

        elif operation == "defragment_disk":
            if not drive:
                raise ValueError("drive parameter required for defragment_disk")
            return defragment_disk(drive, thorough)

        elif operation == "optimize_ssd":
            if not drive:
                raise ValueError("drive parameter required for optimize_ssd")
            return optimize_ssd(drive)

        elif operation == "get_volume_info":
            if not drive:
                raise ValueError("drive parameter required for get_volume_info")
            return get_volume_info(drive)

        # System Diagnostics operations
        elif operation == "get_hardware_info":
            return get_hardware_info()

        elif operation == "get_os_info":
            return get_os_info()

        elif operation == "get_installed_software":
            return get_installed_software()

        elif operation == "get_performance_metrics":
            return get_performance_metrics()

        elif operation == "get_event_log":
            if not log_name:
                log_name = "System"
            return get_event_log(log_name, level, hours_back)

        elif operation == "get_recent_event_errors":
            return await get_recent_event_errors(log_name or "System", max_results)

        elif operation == "health_check":
            return health_check()

        elif operation == "check_system_health_status":
            return await check_system_health_status()

        elif operation == "get_top_resource_processes":
            return await get_top_resource_processes(max_results if max_results < 50 else 5)

        elif operation == "audit_network_ports":
            return await audit_network_ports(include_established)

        elif operation == "analyze_top_folder_sizes":
            if not path:
                raise ValueError("path parameter required for analyze_top_folder_sizes")
            return await analyze_top_folder_sizes(path)

        elif operation == "get_comprehensive_diagnostics":
            return await get_comprehensive_diagnostics()

        elif operation == "forensic_scan":
            return forensic_scan()

        elif operation == "list_crash_dumps":
            return list_crash_dumps()

        elif operation == "get_bugcheck_history":
            return get_bugcheck_history(days_back, max_results)

        elif operation == "analyze_minidump":
            return analyze_minidump(dump_path, max_results)

        elif operation == "windbg_analyze":
            return windbg_analyze(dump_path, timeout_seconds)

        elif operation == "audit_admin_toolbox":
            return audit_admin_toolbox()

        elif operation == "get_firmware_posture":
            return get_firmware_posture()

        elif operation == "audit_scheduled_tasks":
            return audit_scheduled_tasks(max_results)

        elif operation == "get_update_status":
            return get_update_status()

        elif operation == "audit_local_admins":
            return audit_local_admins()

        elif operation == "audit_smb_shares":
            return audit_smb_shares()

        elif operation == "list_shadow_copies":
            return list_shadow_copies()

        elif operation == "audit_drivers":
            return audit_drivers(class_filter, max_results)

        elif operation == "get_reliability_history":
            return get_reliability_history(days_back, max_results)

        elif operation == "winget_outdated":
            return winget_outdated(max_results)

        elif operation == "audit_path_dross":
            return audit_path_dross()

        elif operation == "get_gpu_info":
            return get_gpu_info()

        elif operation == "get_gpu_processes":
            return get_gpu_processes()

        # Windows Services operations
        elif operation == "list_services":
            return list_services(filter_status, filter_name, include_system, page, page_size)

        elif operation == "get_service_stats":
            return get_service_stats()

        elif operation == "get_service_info":
            if not service_name:
                raise ValueError("service_name parameter required for get_service_info")
            return get_service_info(service_name)

        elif operation == "start_service":
            if not service_name:
                raise ValueError("service_name parameter required for start_service")
            return start_service(service_name, wait_timeout)

        elif operation == "stop_service":
            if not service_name:
                raise ValueError("service_name parameter required for stop_service")
            return stop_service(service_name, wait_timeout)

        elif operation == "set_service_startup":
            if not service_name or not startup_type:
                raise ValueError("service_name and startup_type required for set_service_startup")
            return set_service_startup(service_name, startup_type)

        # Process/Task operations
        elif operation == "list_processes":
            return list_processes(filter_name, filter_user, sort_by, page, page_size)

        elif operation == "analyze_process":
            if not pid:
                raise ValueError("pid parameter required for analyze_process")
            return analyze_process(pid)

        elif operation == "kill_process":
            if not pid:
                raise ValueError("pid parameter required for kill_process")
            return kill_process(pid, force)

        # Windows Startup operations
        elif operation == "list_startup_programs":
            return list_startup_programs()

        elif operation == "add_startup_program":
            if not startup_name or not startup_command:
                raise ValueError("startup_name and startup_command parameters required for add_startup_program")
            return add_startup_program(startup_name, startup_command, startup_location)

        elif operation == "remove_startup_program":
            if not startup_name:
                raise ValueError("startup_name parameter required for remove_startup_program")
            return remove_startup_program(startup_name, startup_location)

        # Taskbar operations
        elif operation == "find_taskbar_blocking_processes":
            return find_taskbar_blocking_processes()

        elif operation == "kill_taskbar_blocking_processes":
            return kill_taskbar_blocking_processes(process_names, force)

        elif operation == "get_taskbar_settings":
            return get_taskbar_settings()

        elif operation == "set_taskbar_autohide":
            if autohide is None:
                raise ValueError("autohide parameter required for set_taskbar_autohide")
            return set_taskbar_autohide(autohide)

        elif operation == "list_taskbar_windows":
            return list_taskbar_windows()

        elif operation == "list_tray_icons":
            return list_tray_icons()

        elif operation == "airgap_status":
            return airgap_status()

        elif operation == "airgap_enable":
            return airgap_enable(confirm=confirm)

        elif operation == "airgap_disable":
            return airgap_disable(confirm=confirm)

        else:
            return {
                "status": "error",
                "message": f"Unknown operation: {operation}",
            }

    except Exception as e:
        from system_admin_mcp.mutation_guard import ReadOnlyError, audit_mutation

        if isinstance(e, ReadOnlyError):
            audit_mutation(operation, {"blocked": "read-only mode"})
        logger.error(f"Error in system_admin operation {operation}: {e}", exc_info=True)
        return {
            "status": "error",
            "operation": operation,
            "error": str(e),
        }


@mcp.tool(annotations=_READ_ONLY)
async def get_comprehensive_diagnostics() -> dict[str, Any]:
    """Perform a comprehensive system health and resource audit.

    Consolidates:
    - System health and reboot status
    - Top resource consumers (CPU/Memory)
    - Recent system event errors
    - Critical volume usage

    ## Return Format
    `{status: "success" | "error", timestamp: str, health: dict,
    top_processes: dict, recent_errors: dict, volume_usage: dict}`.

    ## Examples
    ```python
    get_comprehensive_diagnostics()
    ```
    """
    try:
        health = await check_system_health_status()
        top_procs = await get_top_resource_processes(count=5)
        events = await get_recent_event_errors(log_type="System", count=5)

        # Get primary volume usage
        primary_drive = os.environ.get("SystemDrive", "C:")
        if not primary_drive.endswith("\\"):
            primary_drive += "\\"
        volume_info = get_volume_info(primary_drive)

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "top_processes": top_procs,
            "recent_errors": events,
            "volume_usage": volume_info,
        }
    except Exception as e:
        logger.exception("Error during comprehensive diagnostics")
        return {"status": "error", "error": str(e)}
