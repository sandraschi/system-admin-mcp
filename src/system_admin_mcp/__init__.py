"""System Admin MCP - FastMCP 2.10+ service for elevated system operations.

This module provides system administration tools that require elevated privileges.
"""
from mcp import tool
from .user_bridge import UserBridge

__version__ = "0.1.0"

# Initialize the user bridge
_bridge = UserBridge()

# Tool decorators for MCP integration
@tool()
def get_file_owner(file_path: str) -> dict:
    """Get the owner of a file or directory.

    Args:
        file_path: Path to the file or directory

    Returns:
        Dictionary containing owner information
    """
    return _bridge.get_file_owner(file_path)

@tool()
def list_volumes() -> list:
    """List all available volumes on the system.

    Returns:
        List of dictionaries containing volume information
    """
    return _bridge.list_volumes()

@tool()
def recover_file(source_path: str, destination_path: str) -> dict:
    """Recover a deleted file from NTFS volume.

    Args:
        source_path: Original path of the deleted file
        destination_path: Directory to save the recovered file

    Returns:
        Dictionary with recovery status
    """
    return _bridge.recover_file(source_path, destination_path)
