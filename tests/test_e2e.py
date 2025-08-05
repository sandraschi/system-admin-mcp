"""
End-to-end tests for System Admin MCP.

These tests verify the complete functionality of the MCP, including:
- Service installation and startup
- Bridge communication
- Privileged operations
- Error handling and security
"""

import os
import sys
import time
import json
import pytest
import tempfile
import win32serviceutil
import win32service
import win32api
import win32con
import win32security
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import the bridge for testing
from system_admin_mcp.user_bridge.bridge import UserBridge, SystemAdminMCP

# Test configuration
TEST_DIR = Path(tempfile.gettempdir()) / "system_admin_mcp_tests"
TEST_FILE = TEST_DIR / "test_file.txt"
SERVICE_NAME = "SystemAdminMCP"

@pytest.fixture(scope="module")
def setup_test_environment():
    """Set up test environment with a test file."""
    # Create test directory
    TEST_DIR.mkdir(exist_ok=True)
    
    # Create a test file
    with open(TEST_FILE, 'w') as f:
        f.write("Test content")
    
    yield  # Test runs here
    
    # Cleanup
    if TEST_FILE.exists():
        TEST_FILE.unlink()
    if TEST_DIR.exists():
        TEST_DIR.rmdir()

@pytest.fixture
def bridge():
    """Create a bridge instance for testing."""
    bridge = UserBridge()
    
    # Ensure service is running
    if not bridge.service_running:
        if bridge.service_installed:
            win32serviceutil.StartService(SERVICE_NAME)
            time.sleep(2)  # Give service time to start
        else:
            pytest.skip("Service is not installed")
    
    yield bridge
    
    # Clean up
    bridge.cleanup()

@pytest.fixture
def mcp_server():
    """Create an MCP server instance for testing."""
    return SystemAdminMCP()

def test_service_running(bridge):
    """Test that the service is running."""
    assert bridge.service_installed, "Service should be installed"
    assert bridge.service_running, "Service should be running"

def test_ping(bridge):
    """Test the ping command."""
    assert bridge.ping(), "Ping should return True"

async def test_get_file_owner(bridge, mcp_server):
    """Test getting file owner through both direct bridge and MCP server."""
    # Test with direct bridge
    owner_bridge = bridge.get_file_owner(str(TEST_FILE))
    assert owner_bridge, "Should return owner information"
    assert "Error" not in owner_bridge, f"Should not return error: {owner_bridge}"
    
    # Test with MCP server
    result = await mcp_server.execute("get_file_owner", {"path": str(TEST_FILE)})
    assert result["status"] == "success", f"Should succeed: {result}"
    assert "owner" in result["result"], "Should include owner information"

async def test_list_volumes(bridge, mcp_server):
    """Test listing volumes through both direct bridge and MCP server."""
    # Test with direct bridge
    volumes_bridge = bridge.list_volumes()
    assert isinstance(volumes_bridge, list), "Should return a list of volumes"
    assert len(volumes_bridge) > 0, "Should find at least one volume"
    
    # Test with MCP server
    result = await mcp_server.execute("list_volumes", {})
    assert result["status"] == "success", f"Should succeed: {result}"
    assert isinstance(result["result"], list), "Should return a list of volumes"
    assert len(result["result"]) > 0, "Should find at least one volume"

async def test_get_disk_usage(bridge, mcp_server):
    """Test getting disk usage through both direct bridge and MCP server."""
    # Get system drive (usually C:\)
    system_drive = os.environ.get('SystemDrive', 'C:\\')
    
    # Test with direct bridge
    usage_bridge = bridge.get_disk_usage(system_drive)
    assert isinstance(usage_bridge, dict), "Should return disk usage information"
    assert "total_bytes" in usage_bridge, "Should include total bytes"
    
    # Test with MCP server
    result = await mcp_server.execute("get_disk_usage", {"path": system_drive})
    assert result["status"] == "success", f"Should succeed: {result}"
    assert "total_bytes" in result["result"], "Should include total bytes"

async def test_get_process_info(bridge, mcp_server):
    """Test getting process information through both direct bridge and MCP server."""
    # Get current process ID
    current_pid = os.getpid()
    
    # Test with direct bridge
    process_info = bridge.get_process_info(current_pid)
    assert isinstance(process_info, dict), "Should return process information"
    assert process_info.get("pid") == current_pid, "Should return info for the correct process"
    
    # Test with MCP server
    result = await mcp_server.execute("get_process_info", {"pid": current_pid})
    assert result["status"] == "success", f"Should succeed: {result}"
    assert result["result"].get("pid") == current_pid, "Should return info for the correct process"

def test_error_handling(bridge):
    """Test error handling for invalid inputs."""
    # Test with non-existent file
    non_existent = str(TEST_DIR / "non_existent_file.txt")
    result = bridge.get_file_owner(non_existent)
    assert "Error" in result, "Should return error for non-existent file"
    
    # Test with invalid PID
    invalid_pid = 999999
    result = bridge.get_process_info(invalid_pid)
    assert "error" in result, "Should return error for invalid PID"

if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    sys.exit(pytest.main(["-v", __file__]))
