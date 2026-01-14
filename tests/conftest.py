"""Pytest configuration and fixtures for System Admin MCP tests."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file for tests."""
    test_file = temp_dir / "test_file.txt"
    test_file.write_text("Test content")
    yield test_file


@pytest.fixture
def mock_bridge():
    """Mock UserBridge for testing without actual service."""
    with patch("system_admin_mcp.user_bridge.UserBridge") as mock:
        bridge = MagicMock()
        bridge.service_installed = True
        bridge.service_running = True
        bridge.ping.return_value = True
        bridge.get_system_info.return_value = {
            "status": "success",
            "result": {
                "os": {"platform": "win32", "name": "Windows"},
                "python": {"version": "3.10.0"},
            },
        }
        bridge.get_disk_usage.return_value = {
            "status": "success",
            "result": {
                "path": "C:\\",
                "total_bytes": 1000000000,
                "used_bytes": 500000000,
                "free_bytes": 500000000,
            },
        }
        bridge.get_process_info.return_value = {
            "status": "success",
            "result": {"pid": 1234, "name": "test.exe"},
        }
        bridge.list_volumes.return_value = {
            "status": "success",
            "result": [{"name": "C", "type": "fixed", "total_gb": 100}],
        }
        bridge.recover_file.return_value = {
            "status": "success",
            "result": {"recovered": True},
        }
        mock.return_value = bridge
        yield bridge


@pytest.fixture
def mock_wmi():
    """Mock WMI for hardware tests."""
    with patch("system_admin_mcp.tools.implementations.wmi") as mock:
        wmi_instance = MagicMock()
        cpu = MagicMock()
        cpu.Name = "Test CPU"
        cpu.NumberOfCores = 4
        cpu.NumberOfLogicalProcessors = 8
        cpu.MaxClockSpeed = 3000
        wmi_instance.Win32_Processor.return_value = [cpu]
        wmi_instance.Win32_DiskDrive.return_value = []
        wmi_instance.Win32_VideoController.return_value = []
        mock.WMI.return_value = wmi_instance
        yield wmi_instance


@pytest.fixture
def mock_psutil():
    """Mock psutil for system metrics tests."""
    with patch("system_admin_mcp.tools.implementations.psutil") as mock:
        # Mock CPU
        mock.cpu_count.return_value = 4
        mock.cpu_freq.return_value = MagicMock(current=3000.0)
        mock.cpu_percent.return_value = 25.0

        # Mock memory
        mem = MagicMock()
        mem.total = 16 * 1024**3  # 16 GB
        mem.used = 8 * 1024**3  # 8 GB
        mem.available = 8 * 1024**3  # 8 GB
        mem.percent = 50.0
        mock.virtual_memory.return_value = mem

        # Mock swap
        swap = MagicMock()
        swap.total = 4 * 1024**3
        swap.used = 1 * 1024**3
        swap.percent = 25.0
        mock.swap_memory.return_value = swap

        # Mock disk
        disk_usage = MagicMock()
        disk_usage.total = 100 * 1024**3
        disk_usage.used = 50 * 1024**3
        disk_usage.free = 50 * 1024**3
        disk_usage.percent = 50.0
        mock.disk_usage.return_value = disk_usage

        # Mock disk partitions
        partition = MagicMock()
        partition.device = "C:\\"
        partition.mountpoint = "C:\\"
        partition.fstype = "NTFS"
        mock.disk_partitions.return_value = [partition]

        # Mock disk I/O
        disk_io = MagicMock()
        disk_io.read_bytes = 1000000
        disk_io.write_bytes = 500000
        disk_io.read_count = 100
        disk_io.write_count = 50
        mock.disk_io_counters.return_value = disk_io

        # Mock network I/O
        net_io = MagicMock()
        net_io.bytes_sent = 1000000
        net_io.bytes_recv = 2000000
        net_io.packets_sent = 100
        net_io.packets_recv = 200
        mock.net_io_counters.return_value = net_io

        # Mock process
        mock.process_iter.return_value = []
        mock.boot_time.return_value = 1000000.0

        yield mock


@pytest.fixture
def mock_win32():
    """Mock win32api functions."""
    with patch("system_admin_mcp.tools.implementations.win32api") as mock:
        mock.GetLogicalDriveStrings.return_value = "C:\\\x00D:\\\x00"
        mock.GetVolumeInformation.return_value = ("TestVolume", None, None, None, "NTFS")
        mock.GetUserName.return_value = "TestUser"
        mock.GetCurrentProcess.return_value = MagicMock()
        mock.FormatMessage.return_value = "Test error message"
        yield mock


@pytest.fixture
def mock_win32security():
    """Mock win32security functions."""
    with patch("system_admin_mcp.tools.implementations.win32security") as mock:
        # Mock security descriptor
        sd = MagicMock()
        owner_sid = MagicMock()
        sd.GetSecurityDescriptorOwner.return_value = owner_sid
        sd.GetSecurityDescriptorDacl.return_value = MagicMock()
        mock.GetFileSecurity.return_value = sd

        # Mock SID lookup
        mock.LookupAccountSid.return_value = ("TestUser", "TestDomain", 1)
        mock.LookupAccountName.return_value = (MagicMock(), "TestDomain", 1)
        mock.ConvertSidToStringSid.return_value = "S-1-5-21-1234567890-1234567890-1234567890-1001"

        # Mock privileges
        mock.LookupPrivilegeValue.return_value = MagicMock()
        mock.SE_TAKE_OWNERSHIP_NAME = "SeTakeOwnershipPrivilege"
        mock.SE_PRIVILEGE_ENABLED = 2

        # Mock ACL
        acl = MagicMock()
        acl.GetAceCount.return_value = 0
        acl.GetAce.return_value = None
        mock.ACL.return_value = acl

        yield mock


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for PowerShell commands."""
    with patch("system_admin_mcp.tools.implementations.subprocess") as mock:
        result = MagicMock()
        result.returncode = 0
        result.stdout = '{"test": "data"}'
        result.stderr = ""
        mock.run.return_value = result
        yield mock


@pytest.fixture
def mock_win32evtlog():
    """Mock win32evtlog for event log tests."""
    with patch("system_admin_mcp.tools.implementations.win32evtlog") as mock:
        mock.OpenEventLog.return_value = MagicMock()
        mock.ReadEventLog.return_value = []
        mock.CloseEventLog.return_value = None
        mock.EVENTLOG_BACKWARDS_READ = 1
        mock.EVENTLOG_SEQUENTIAL_READ = 2
        mock.EVENTLOG_ERROR_TYPE = 1
        mock.EVENTLOG_WARNING_TYPE = 2
        mock.EVENTLOG_INFORMATION_TYPE = 4
        yield mock


@pytest.fixture
def mock_platform():
    """Mock platform module."""
    with patch("system_admin_mcp.tools.implementations.platform") as mock:
        mock.machine.return_value = "AMD64"
        mock.version.return_value = "10.0.19041"
        mock.release.return_value = "10"
        mock.win32_edition.return_value = "Professional"
        yield mock


@pytest.fixture
def mock_is_admin():
    """Mock is_admin function."""
    with patch("system_admin_mcp.tools.implementations.is_admin", return_value=True):
        yield


@pytest.fixture
def mock_is_not_admin():
    """Mock is_admin function returning False."""
    with patch("system_admin_mcp.tools.implementations.is_admin", return_value=False):
        yield

