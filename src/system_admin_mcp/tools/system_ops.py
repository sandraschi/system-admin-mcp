"""System operations tools for the System Admin MCP."""

import ctypes
import logging
from typing import Annotated, Any

from pydantic import Field

# Import the FastMCP instance from app module
from system_admin_mcp.app import mcp

logger = logging.getLogger(__name__)

from mcp.types import ToolAnnotations

# Fleet tool-annotation standard (TOOL_DESIGN_STANDARDS.md S9).
_READ_ONLY = ToolAnnotations(readOnlyHint=True)
_DESTRUCTIVE = ToolAnnotations(destructiveHint=True)

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
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception as e:
        logger.warning(f"Failed to check admin status: {e}")
        return False


@mcp.tool(annotations=_READ_ONLY)
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


@mcp.tool(annotations=_READ_ONLY)
async def get_file_owner(file_path: Annotated[str, Field(description="Path to the file or directory")]) -> dict:
    """Get the owner of a file or directory.

    ## Return Format
    `{file: str, owner: "DOMAIN\\User", sid: str}`.

    ## Examples
    ```python
    get_file_owner("C:\\Windows")
    ```
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


@mcp.tool(annotations=_DESTRUCTIVE)
async def recover_file(
    original_path: Annotated[str, Field(description="Original path of the deleted file")],
    output_dir: Annotated[str, Field(description="Directory to save the recovered file")],
) -> dict:
    """Attempt to recover a deleted file from NTFS volume.

    ## Return Format
    `{status: "success" | "error", ...}` with recovery details or an
    `error: {code, message}` payload (e.g. `admin_required`).

    ## Examples
    ```python
    recover_file("C:/deleted/file.docx", "D:/Recovery")
    ```
    """
    from system_admin_mcp.mutation_guard import audit_mutation, require_mutable

    audit_mutation("recover_file", {"source": original_path, "dest": output_dir})
    require_mutable("recover_file")
    if not is_admin():
        return {
            "status": "error",
            "error": {
                "code": "admin_required",
                "message": "Administrator privileges required for file recovery",
            },
        }

    bridge = get_bridge()
    if bridge is None:
        return {
            "status": "error",
            "error": {
                "code": "bridge_unavailable",
                "message": "UserBridge not available. Service may not be installed.",
            },
        }
    try:
        return bridge.recover_file(original_path, output_dir)
    except Exception as e:
        logger.error(f"File recovery failed: {e}")
        return {"status": "error", "error": {"code": "recovery_failed", "message": str(e)}}


@mcp.tool(annotations=_READ_ONLY)
async def get_disk_usage(path: Annotated[str, Field(description="Path to check (file or directory)")]) -> dict:
    """Get disk usage information for a path.

    ## Return Format
    Bridge result dict with total/used/free bytes for the path.

    ## Examples
    ```python
    get_disk_usage("C:\\")
    ```
    """
    bridge = get_bridge()
    if bridge is None:
        raise RuntimeError("UserBridge not available. Service may not be installed.")
    try:
        return bridge.get_disk_usage(path)
    except Exception as e:
        logger.error(f"Error getting disk usage for {path}: {e}")
        raise


@mcp.tool(annotations=_READ_ONLY)
async def get_process_info(pid: Annotated[int, Field(description="Process ID")]) -> dict:
    """Get information about a running process.

    ## Return Format
    Bridge result dict with process details for the PID.

    ## Examples
    ```python
    get_process_info(1234)
    ```
    """
    bridge = get_bridge()
    if bridge is None:
        raise RuntimeError("UserBridge not available. Service may not be installed.")
    try:
        return bridge.get_process_info(pid)
    except Exception as e:
        logger.error(f"Error getting process info for PID {pid}: {e}")
        raise


@mcp.tool(annotations=_READ_ONLY)
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


@mcp.tool(annotations=_READ_ONLY)
async def get_system_info() -> dict:
    """Get system information from the service.

    Returns:
        Dictionary containing system information
    """
    try:
        if _bridge is None:
            raise RuntimeError("bridge not initialized")
        return _bridge.get_system_info()
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise


@mcp.tool(annotations=_READ_ONLY)
async def help(
    level: Annotated[str, Field(description='Detail level: "basic", "intermediate", or "advanced"')] = "basic",
    topic: Annotated[str | None, Field(description="Focus topic: file_recovery, security, volume, diagnostics")] = None,
) -> str:
    """Get help information about System Admin MCP.

    ## Return Format
    Markdown help text for the requested level.

    ## Examples
    ```python
    help("basic")
    help("intermediate", topic="security")
    ```
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


@mcp.tool(annotations=_READ_ONLY)
async def status(
    level: Annotated[str, Field(description='Detail level: "basic", "intermediate", or "advanced"')] = "basic",
    focus: Annotated[str | None, Field(description="Focus area: tools, service, system")] = None,
) -> str:
    """Get server status and diagnostics.

    ## Return Format
    Markdown status text for the requested level.

    ## Examples
    ```python
    status("basic")
    ```
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
