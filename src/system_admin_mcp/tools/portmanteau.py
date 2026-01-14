"""Portmanteau tools for System Admin MCP - consolidates related operations."""

import logging
from typing import Any, Dict, List, Literal, Optional

from system_admin_mcp.app import mcp
from system_admin_mcp.tools.implementations import (
    analyze_disk_usage_advanced,
    audit_permissions,
    check_disk_health,
    defragment_disk,
    disk_cleanup,
    get_event_log,
    get_hardware_info,
    get_installed_software,
    get_os_info,
    get_performance_metrics,
    get_permissions,
    get_volume_info,
    health_check,
    optimize_ssd,
    recover_file_ntfs,
    remove_permission,
    scan_volume,
    set_permissions,
    take_ownership,
    validate_recovery,
)
from system_admin_mcp.tools.services_and_tasks import (
    add_startup_program,
    analyze_process,
    find_taskbar_blocking_processes,
    get_service_info,
    get_service_stats,
    get_taskbar_settings,
    kill_process,
    kill_taskbar_blocking_processes,
    list_processes,
    list_services,
    list_startup_programs,
    remove_startup_program,
    set_service_startup,
    set_taskbar_autohide,
    start_service,
    stop_service,
)

logger = logging.getLogger(__name__)

# Lazy import UserBridge to avoid startup failures
try:
    from system_admin_mcp.user_bridge import UserBridge
except ImportError as e:
    logger.warning(f"Failed to import UserBridge: {e}. Bridge operations will not be available.")
    UserBridge = None  # type: ignore
except Exception as e:
    logger.warning(f"Failed to import UserBridge: {e}. Bridge operations will not be available.")
    UserBridge = None  # type: ignore

# Initialize user bridge lazily to avoid startup errors
_bridge = None


def get_bridge() -> Optional[Any]:
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


@mcp.tool()
async def system_admin(
    operation: Literal[
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
        # Volume Maintenance
        "check_disk_health",
        "analyze_disk_usage",
        "disk_cleanup",
        "defragment_disk",
        "optimize_ssd",
        "get_volume_info",
        # System Diagnostics
        "get_hardware_info",
        "get_os_info",
        "get_installed_software",
        "get_performance_metrics",
        "get_event_log",
        "health_check",
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
    ],
    # File Recovery parameters
    drive: Optional[str] = None,
    file_pattern: Optional[str] = None,
    mft_entry: Optional[int] = None,
    source_path: Optional[str] = None,
    destination_path: Optional[str] = None,
    verify_integrity: bool = True,
    max_results: int = 100,
    # Security parameters
    path: Optional[str] = None,
    principal: Optional[str] = None,
    rights: Optional[str] = None,
    inheritance: Optional[str] = None,
    # Volume parameters
    cleanup_targets: Optional[List[str]] = None,
    dry_run: bool = True,
    thorough: bool = False,
    # Diagnostics parameters
    log_name: Optional[str] = None,
    level: Optional[str] = None,
    hours_back: int = 24,
    # Services parameters
    service_name: Optional[str] = None,
    filter_status: Optional[str] = None,
    filter_name: Optional[str] = None,
    include_system: bool = True,
    wait_timeout: int = 30,
    startup_type: Optional[str] = None,
    # Process parameters
    pid: Optional[int] = None,
    filter_user: Optional[str] = None,
    sort_by: str = "cpu",
    force: bool = False,
    # Startup parameters
    startup_name: Optional[str] = None,
    startup_command: Optional[str] = None,
    startup_location: str = "HKCU",
    # Taskbar parameters
    autohide: Optional[bool] = None,
    process_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
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

    Args:
        operation: The operation to perform (required)
        drive: Drive letter (e.g., "C:") for volume operations
        file_pattern: File pattern for scanning (e.g., "*.docx")
        mft_entry: MFT entry number for file recovery
        source_path: Source file path for recovery
        destination_path: Destination path for recovery
        verify_integrity: Verify file integrity after recovery
        max_results: Maximum results for scanning
        path: File/folder path for security operations
        principal: User/group for permission operations
        rights: Permission rights (Read, Write, Modify, FullControl)
        inheritance: Inheritance setting for permissions
        cleanup_targets: List of cleanup targets (temp_files, recycle_bin, etc.)
        dry_run: Preview changes without applying
        thorough: Perform thorough operation (defrag, etc.)
        log_name: Event log name (System, Application, Security)
        level: Event log level (Error, Warning, Information)
        hours_back: Hours to look back in event logs
        service_name: Service name for service operations
        filter_status: Filter services/processes by status
        filter_name: Filter by name (services/processes)
        include_system: Include system services in results
        startup_type: Service startup type (Auto, Manual, Disabled)
        wait_timeout: Timeout for service start/stop operations
        pid: Process ID for process operations
        filter_user: Filter processes by username
        sort_by: Sort processes by (cpu, memory, name)
        force: Force kill processes
        name: Program name for startup operations
        command: Command/path for startup program
        scope: Scope for startup (current_user, all_users)
        enabled: Enable/disable flag for taskbar operations

    Returns:
        Dictionary with operation-specific results

    Examples:
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
    try:
        # File Recovery operations
        if operation == "scan_volume":
            if not drive:
                raise ValueError("drive parameter required for scan_volume")
            return scan_volume(drive, file_pattern, max_results)

        elif operation == "recover_file":
            if not source_path or not destination_path:
                raise ValueError(
                    "source_path and destination_path required for recover_file"
                )
            return recover_file_ntfs(source_path, destination_path)

        elif operation == "validate_recovery":
            if not destination_path:
                raise ValueError("destination_path required for validate_recovery")
            return validate_recovery(destination_path)

        elif operation == "batch_recover":
            # Batch recovery - recover multiple files
            if not source_path or not destination_path:
                raise ValueError(
                    "source_path and destination_path required for batch_recover"
                )
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
                raise ValueError(
                    "path, principal, and rights required for set_permissions"
                )
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

        elif operation == "health_check":
            return health_check()

        # Windows Services operations
        elif operation == "list_services":
            return list_services(filter_status, filter_name, include_system)

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
            return list_processes(filter_name, filter_user, sort_by)

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
                raise ValueError(
                    "startup_name and startup_command parameters required for add_startup_program"
                )
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

        else:
            return {
                "status": "error",
                "message": f"Unknown operation: {operation}",
            }

    except Exception as e:
        logger.error(f"Error in system_admin operation {operation}: {e}", exc_info=True)
        return {
            "status": "error",
            "operation": operation,
            "error": str(e),
        }
