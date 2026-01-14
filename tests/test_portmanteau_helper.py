"""Helper to get the actual function from FastMCP tool wrapper."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the module before the decorator is applied
import system_admin_mcp.tools.portmanteau as portmanteau_module

# The function is defined in the module, we need to get it before decoration
# Since FastMCP decorator wraps it, we'll create a test helper that calls the implementation directly
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


async def system_admin_test(
    operation: str,
    drive: str = None,
    file_pattern: str = None,
    mft_entry: int = None,
    source_path: str = None,
    destination_path: str = None,
    verify_integrity: bool = True,
    max_results: int = 100,
    path: str = None,
    principal: str = None,
    rights: str = None,
    inheritance: str = None,
    cleanup_targets: list = None,
    dry_run: bool = True,
    thorough: bool = False,
    log_name: str = None,
    level: str = None,
    hours_back: int = 24,
):
    """Test helper that mimics the system_admin function logic."""
    # This is the same logic as in portmanteau.py but without the decorator
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
        if not source_path or not destination_path:
            raise ValueError("source_path and destination_path required for batch_recover")
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

    elif operation == "modify_acl":
        if not path:
            raise ValueError("path parameter required for modify_acl")
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

    else:
        return {
            "status": "error",
            "message": f"Unknown operation: {operation}",
        }

