"""Volume operations for the elevated service."""
import logging
import win32api
import win32file
import win32security

logger = logging.getLogger(__name__)

def list_volumes() -> list:
    """List all available volumes with elevated privileges.

    Returns:
        List of dictionaries containing volume information
    """
    volumes = []
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split("\x00") if drives else []

    for drive in drives:
        if not drive:
            continue
        try:
            drive_type = win32file.GetDriveType(drive)
            
            # Get volume information
            volume_info = {
                "drive": drive,
                "type": _get_drive_type_name(drive_type),
                "type_code": drive_type,
            }
            
            # Try to get more detailed information
            try:
                volume_name = win32api.GetVolumeInformation(drive)[0]
                volume_info["label"] = volume_name
            except:
                pass
                
            volumes.append(volume_info)
            
        except Exception as e:
            logger.warning(f"Error getting info for {drive}: {e}")
            volumes.append({
                "drive": drive,
                "error": str(e),
                "type": "error"
            })

    return volumes

def _get_drive_type_name(drive_type: int) -> str:
    """Convert drive type code to human-readable name.
    
    Args:
        drive_type: Drive type code from win32file
        
    Returns:
        Human-readable drive type name
    """
    drive_types = {
        win32file.DRIVE_UNKNOWN: "Unknown",
        win32file.DRIVE_NO_ROOT_DIR: "No root directory",
        win32file.DRIVE_REMOVABLE: "Removable",
        win32file.DRIVE_FIXED: "Fixed",
        win32file.DRIVE_REMOTE: "Remote",
        win32file.DRIVE_CDROM: "CD-ROM",
        win32file.DRIVE_RAMDISK: "RAM disk",
    }
    
    return drive_types.get(drive_type, f"Unknown ({drive_type})")
