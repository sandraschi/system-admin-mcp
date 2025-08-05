"""System operations tools for the System Admin MCP."""
import ctypes
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from mcp import tool

logger = logging.getLogger(__name__)


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


@tool()
def list_volumes() -> List[dict]:
    """List all available volumes on the system.

    Returns:
        List of dictionaries containing volume information
    """
    import win32api

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


@tool()
def get_file_owner(file_path: str) -> dict:
    """Get the owner of a file or directory.

    Args:
        file_path: Path to the file or directory

    Returns:
        Dictionary containing owner information
    """
    import win32security
    import ntsecuritycon as con

    try:
        sd = win32security.GetFileSecurity(
            file_path, win32security.OWNER_SECURITY_INFORMATION
        )
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


@tool()
def recover_file(original_path: str, output_dir: str) -> dict:
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
        from win32file import (
            GENERIC_READ,
            OPEN_EXISTING,
            FILE_FLAG_NO_BUFFERING,
            CreateFile,
            ReadFile,
            CloseHandle,
        )

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
