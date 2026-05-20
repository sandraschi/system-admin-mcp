"""System operations tools for the System Admin MCP."""

import ctypes
import logging
from typing import Any

# Import the FastMCP instance from app module
from system_admin_mcp.app import mcp

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


def is_admin() -> bool:
    """Check if the current process has administrator privileges.

    Returns:
        bool: True if running as administrator, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logger.warning(f"Failed to check admin status: {e}")
        return False


@mcp.tool()
async def list_volumes() -> list[dict]:
    """List all available volumes on the system.

    Returns:
        List of dictionaries containing volume information
    """
    import win32api
    import win32file

    volumes = []
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split("\x00") if drives else []

    for drive in drives:
        if not drive:
            continue
        try:
            volume_info = {
                "drive": drive,
                "type": win32file.GetDriveType(drive),
            }
            volumes.append(volume_info)
        except Exception as e:
            logger.warning(f"Error getting info for {drive}: {e}")

    return volumes


@mcp.tool()
async def get_file_owner(file_path: str) -> dict:
    """Get the owner of a file or directory.

    Args:
        file_path: Path to the file or directory

    Returns:
        Dictionary containing owner information
    """
    import win32security

    try:
        sd = win32security.GetFileSecurity(file_path, win32security.OWNER_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
        return {
            "file": file_path,
            "owner": f"{domain}\\{name}",
            "sid": win32security.ConvertSidToStringSid(owner_sid),
        }
    except Exception as e:
        logger.error(f"Error getting owner for {file_path}: {e}")
        raise


@mcp.tool()
async def recover_file(original_path: str, output_dir: str) -> dict:
    """Attempt to recover a deleted file from NTFS volume.

    Args:
        original_path: Original path of the deleted file
        output_dir: Directory to save the recovered file

    Returns:
        Dictionary with recovery status
    """
    if not is_admin():
        raise RuntimeError("Administrator privileges required for file recovery")

    try:
        # Implementation would go here
        # This is a placeholder that needs proper NTFS implementation
        return {
            "status": "error",
            "message": "File recovery not yet implemented",
            "original_path": original_path,
            "output_dir": output_dir,
        }

    except Exception as e:
        logger.error(f"File recovery failed: {e}")
        raise


@mcp.tool()
async def get_disk_usage(path: str) -> dict:
    """Get disk usage information for a path.

    Args:
        path: Path to check (file or directory)

    Returns:
        Dictionary containing disk usage information
    """
    try:
        return _bridge.get_disk_usage(path)
    except Exception as e:
        logger.error(f"Error getting disk usage for {path}: {e}")
        raise


@mcp.tool()
async def get_process_info(pid: int) -> dict:
    """Get information about a running process.

    Args:
        pid: Process ID

    Returns:
        Dictionary containing process information
    """
    bridge = get_bridge()
    if bridge is None:
        raise RuntimeError("UserBridge not available. Service may not be installed.")
    try:
        return bridge.get_process_info(pid)
    except Exception as e:
        logger.error(f"Error getting process info for PID {pid}: {e}")
        raise


@mcp.tool()
async def ping() -> dict:
    """Check if the System Admin MCP service is responsive.

    Returns:
        Dictionary with status information
    """
    bridge = get_bridge()
    if bridge is None:
        return {
            "status": "error",
            "message": "UserBridge not available. Service may not be installed.",
            "service_installed": False,
            "service_running": False,
        }
    try:
        is_alive = bridge.ping()
        return {
            "status": "success" if is_alive else "error",
            "message": "pong" if is_alive else "service not responding",
            "service_installed": bridge.service_installed,
            "service_running": bridge.service_running,
        }
    except Exception as e:
        logger.error(f"Error pinging service: {e}")
        return {
            "status": "error",
            "message": str(e),
            "service_installed": False,
            "service_running": False,
        }


@mcp.tool()
async def get_system_info() -> dict:
    """Get system information from the service.

    Returns:
        Dictionary containing system information
    """
    try:
        return _bridge.get_system_info()
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise


@mcp.tool()
async def help(level: str = "basic", topic: str | None = None) -> str:
    """Get help information about System Admin MCP.

    Args:
        level: Detail level - "basic", "intermediate", or "advanced"
        topic: Optional topic to focus on (file_recovery, security, volume, diagnostics)

    Returns:
        Help text for the server
    """
    if level == "basic":
        return """# System Admin MCP Help

## Overview
FastMCP 2.13+ server for elevated Windows system administration tasks.

## Available Tools
- list_volumes: List all available volumes
- get_file_owner: Get file/directory owner information
- recover_file: Recover deleted files from NTFS volumes
- get_disk_usage: Get disk usage information
- get_process_info: Get process information
- get_system_info: Get system information
- ping: Check service responsiveness
- help: Get help information
- status: Get server status

## Usage
Most operations require administrator privileges.
"""
    elif level == "intermediate":
        return """# System Admin MCP - Intermediate Help

## Tools

### File Operations
- **get_file_owner**: Get owner of file/directory
- **recover_file**: Recover deleted files (NTFS only)

### Volume Operations
- **list_volumes**: List all volumes with details
- **get_disk_usage**: Get disk space usage

### System Operations
- **get_process_info**: Get detailed process information
- **get_system_info**: Get system information
- **ping**: Check service status

## Examples
- list_volumes() - List all drives
- get_file_owner("C:\\Windows") - Get folder owner
- get_disk_usage("C:\\") - Check disk space
"""
    else:
        return """# System Admin MCP - Advanced Help

## Architecture
- FastMCP 2.13+ framework
- Windows service for elevated operations
- Named pipe communication
- NTFS-specific file recovery

## Security
- Administrator privileges required
- All operations logged
- Service-based elevation model

## Tool Details
See individual tool docstrings for detailed information.
"""


@mcp.tool()
async def status(level: str = "basic", focus: str | None = None) -> str:
    """Get server status and diagnostics.

    Args:
        level: Detail level - "basic", "intermediate", or "advanced"
        focus: Optional focus area (tools, service, system)

    Returns:
        Status information
    """
    try:
        bridge = get_bridge()
        service_status = {
            "installed": bridge.service_installed if bridge else False,
            "running": bridge.service_running if bridge else False,
        }

        if level == "basic":
            return f"""# System Admin MCP Status

**Status:** {"✅ Running" if service_status["running"] else "⚠️ Service not running"}
**Service Installed:** {"Yes" if service_status["installed"] else "No"}
**Tools:** 9
**FastMCP:** 2.13+
"""
        elif level == "intermediate":
            return f"""# System Admin MCP - Detailed Status

## Service Information
- **Installed:** {"Yes" if service_status["installed"] else "No"}
- **Running:** {"Yes" if service_status["running"] else "No"}

## Tools
- list_volumes
- get_file_owner
- recover_file
- get_disk_usage
- get_process_info
- get_system_info
- ping
- help
- status

## Configuration
- Python: 3.8+
- FastMCP: 2.13+
- Platform: Windows
"""
        else:
            return f"""# System Admin MCP - Advanced Status

## Service Status
- Installed: {service_status["installed"]}
- Running: {service_status["running"]}

## System Information
- Platform: Windows
- FastMCP: 2.13+
- Tools: 9

## Compliance
- ✅ FastMCP 2.13+
- ✅ Help tool
- ✅ Status tool
"""
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return f"Error getting status: {e}"
