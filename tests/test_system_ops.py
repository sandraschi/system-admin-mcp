"""Tests for system operations tools."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import win32security
import win32file

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from system_admin_mcp.tools import system_ops


def test_is_admin():
    """Test the is_admin function."""
    # This test just verifies the function runs without errors
    # The actual return value depends on the test environment
    assert isinstance(system_ops.is_admin(), bool)


def test_list_volumes():
    """Test listing volumes."""
    with patch("win32api.GetLogicalDriveStrings") as mock_drives, patch(
        "win32file.GetDriveType"
    ) as mock_drive_type:
        mock_drives.return_value = "C:\\\x00D:\\\x00"
        mock_drive_type.return_value = win32file.DRIVE_FIXED

        volumes = system_ops.list_volumes()
        assert len(volumes) == 2
        assert volumes[0]["drive"] == "C:\\"
        assert volumes[0]["type"] == win32file.DRIVE_FIXED


def test_get_file_owner(temp_file):
    """Test getting file owner."""
    mock_sid = MagicMock()
    mock_sd = MagicMock()
    mock_sd.GetSecurityDescriptorOwner.return_value = mock_sid

    with patch("win32security.GetFileSecurity") as mock_get_sec, patch(
        "win32security.LookupAccountSid"
    ) as mock_lookup, patch(
        "win32security.ConvertSidToStringSid"
    ) as mock_convert_sid:
        mock_get_sec.return_value = mock_sd
        mock_lookup.return_value = ("testuser", "TESTDOMAIN", 1)
        mock_convert_sid.return_value = "S-1-5-21-..."

        result = system_ops.get_file_owner(str(temp_file))
        assert result["owner"] == "TESTDOMAIN\\testuser"
        assert "S-1-5-21-" in result["sid"]


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        f.close()
        yield f.name
        try:
            os.unlink(f.name)
        except OSError:
            pass


if __name__ == "__main__":
    pytest.main(["-v", "--cov=system_admin_mcp", "--cov-report=term-missing"])
