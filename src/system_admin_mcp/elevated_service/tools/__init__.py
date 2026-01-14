"""
Privileged system administration tools.

This module contains implementations of system administration operations that
require elevated privileges. These tools are only accessible through the
elevated service and are called by the user bridge.
"""

from typing import Dict, Any
import os
import logging
import win32security
import win32api
import win32file
import psutil

logger = logging.getLogger(__name__)


def get_file_owner(path: str) -> Dict[str, Any]:
    """Get the owner of a file or directory.

    Args:
        path: Absolute path to the file or directory

    Returns:
        Dict containing owner information or error details
    """
    try:
        # Convert to absolute path for security
        path = os.path.abspath(path)

        # Get security descriptor
        sd = win32security.GetFileSecurity(
            path, win32security.OWNER_SECURITY_INFORMATION
        )

        # Get owner SID
        owner_sid = sd.GetSecurityDescriptorOwner()

        # Convert SID to account name
        try:
            account_name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
            owner = f"{domain}\\{account_name}"
        except win32security.error:
            # If we can't resolve the SID, return the SID string
            owner = win32security.ConvertSidToStringSid(owner_sid)

        return {
            "status": "success",
            "result": {
                "path": path,
                "owner": owner,
                "sid": win32security.ConvertSidToStringSid(owner_sid),
            },
        }

    except Exception as e:
        logger.exception(f"Failed to get file owner for {path}")
        return {
            "status": "error",
            "error": {"code": "get_owner_failed", "message": str(e)},
        }


def list_volumes() -> Dict[str, Any]:
    """List all volumes on the system.

    Returns:
        Dict containing volume information or error details
    """
    try:
        volumes = []
        drives = win32api.GetLogicalDriveStrings().split("\x00")[:-1]

        for drive in drives:
            try:
                drive_type = win32file.GetDriveType(drive)

                # Skip network and removable drives if not ready
                if drive_type in (win32file.DRIVE_REMOVABLE, win32file.DRIVE_REMOTE):
                    try:
                        free_bytes, total_bytes, _ = win32file.GetDiskFreeSpaceEx(drive)
                    except Exception:
                        continue
                else:
                    free_bytes, total_bytes, _ = win32file.GetDiskFreeSpaceEx(drive)

                # Get volume information
                volume_info = {
                    "name": drive.rstrip("\\"),
                    "type": {
                        win32file.DRIVE_UNKNOWN: "unknown",
                        win32file.DRIVE_NO_ROOT_DIR: "no_root_dir",
                        win32file.DRIVE_REMOVABLE: "removable",
                        win32file.DRIVE_FIXED: "fixed",
                        win32file.DRIVE_REMOTE: "remote",
                        win32file.DRIVE_CDROM: "cdrom",
                        win32file.DRIVE_RAMDISK: "ramdisk",
                    }.get(drive_type, "unknown"),
                    "total_bytes": total_bytes,
                    "free_bytes": free_bytes,
                    "used_bytes": total_bytes - free_bytes if total_bytes else 0,
                    "total_gb": total_bytes / (1024**3) if total_bytes else 0,
                    "free_gb": free_bytes / (1024**3) if free_bytes else 0,
                }

                # Add volume label if available
                try:
                    volume_name = win32api.GetVolumeInformation(drive)[0]
                    if volume_name:
                        volume_info["label"] = volume_name
                except Exception:
                    pass

                volumes.append(volume_info)

            except Exception as e:
                logger.warning(f"Error getting info for {drive}: {e}")
                continue

        return {"status": "success", "result": volumes}

    except Exception as e:
        logger.exception("Failed to list volumes")
        return {
            "status": "error",
            "error": {"code": "list_volumes_failed", "message": str(e)},
        }


def get_disk_usage(path: str) -> Dict[str, Any]:
    """Get disk usage information for a path.

    Args:
        path: Path to check (file or directory)

    Returns:
        Dict containing disk usage information or error details
    """
    try:
        path = os.path.abspath(path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        # Get disk usage using psutil for cross-platform compatibility
        usage = psutil.disk_usage(os.path.splitdrive(path)[0])

        return {
            "status": "success",
            "result": {
                "path": path,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent_used": usage.percent,
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
            },
        }

    except Exception as e:
        logger.exception(f"Failed to get disk usage for {path}")
        return {
            "status": "error",
            "error": {"code": "get_disk_usage_failed", "message": str(e)},
        }


def get_process_info(pid: int) -> Dict[str, Any]:
    """Get information about a running process.

    Args:
        pid: Process ID

    Returns:
        Dict containing process information or error details
    """
    try:
        process = psutil.Process(pid)

        with process.oneshot():
            info = {
                "pid": process.pid,
                "name": process.name(),
                "exe": process.exe(),
                "cmdline": process.cmdline(),
                "status": process.status(),
                "create_time": process.create_time(),
                "username": process.username(),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_info": process.memory_info()._asdict(),
                "num_threads": process.num_threads(),
                "num_handles": process.num_handles(),
                "io_counters": process.io_counters()._asdict()
                if process.io_counters()
                else None,
                "cpu_affinity": process.cpu_affinity(),
                "nice": process.nice(),
                "ionice": process.ionice(),
                "num_ctx_switches": process.num_ctx_switches()._asdict(),
                "ppid": process.ppid(),
                "parent": process.parent().pid if process.parent() else None,
                "children": [p.pid for p in process.children(recursive=False)],
                "is_running": process.is_running(),
                "terminal": process.terminal()
                if hasattr(process, "terminal")
                else None,
                "uids": process.uids()._asdict() if hasattr(process, "uids") else None,
                "gids": process.gids()._asdict() if hasattr(process, "gids") else None,
            }

        return {"status": "success", "result": info}

    except psutil.NoSuchProcess:
        return {
            "status": "error",
            "error": {
                "code": "process_not_found",
                "message": f"No process with PID {pid} found",
            },
        }
    except Exception as e:
        logger.exception(f"Failed to get info for process {pid}")
        return {
            "status": "error",
            "error": {"code": "get_process_info_failed", "message": str(e)},
        }


def ping() -> Dict[str, Any]:
    """Simple ping method to check if the service is responsive.

    Returns:
        Dict with status "pong"
    """
    return {"status": "success", "result": "pong"}
