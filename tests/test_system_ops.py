"""Tests for individual system operation tools."""

import pytest

from system_admin_mcp.tools.system_ops import (
    get_disk_usage,
    get_file_owner,
    get_process_info,
    get_system_info,
    help,
    list_volumes,
    ping,
    recover_file,
    status,
)


class TestBasicTools:
    """Tests for basic tools."""

    @pytest.mark.asyncio
    async def test_ping(self, mock_bridge):
        """Test ping tool."""
        result = await ping()
        assert result["status"] in ["success", "error"]
        assert "service_installed" in result

    @pytest.mark.asyncio
    async def test_list_volumes(self, mock_bridge):
        """Test list_volumes tool."""
        result = await list_volumes()
        assert isinstance(result, list)
        assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_get_file_owner(self, temp_file, mock_bridge):
        """Test get_file_owner tool."""
        result = await get_file_owner(str(temp_file))
        assert isinstance(result, dict)
        assert "file" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_disk_usage(self, mock_bridge):
        """Test get_disk_usage tool."""
        result = await get_disk_usage("C:\\")
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_get_process_info(self, mock_bridge):
        """Test get_process_info tool."""
        result = await get_process_info(1234)
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_get_system_info(self, mock_bridge):
        """Test get_system_info tool."""
        result = await get_system_info()
        assert isinstance(result, dict)
        assert "status" in result or "os" in result

    @pytest.mark.asyncio
    async def test_recover_file(self, mock_bridge):
        """Test recover_file tool."""
        result = await recover_file("C:/deleted.txt", "D:/recovered.txt")
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_help(self):
        """Test help tool."""
        result = await help()
        assert isinstance(result, str)
        assert len(result) > 0

        result_intermediate = await help(level="intermediate")
        assert isinstance(result_intermediate, str)

        result_advanced = await help(level="advanced")
        assert isinstance(result_advanced, str)

    @pytest.mark.asyncio
    async def test_status(self, mock_bridge):
        """Test status tool."""
        result = await status()
        assert isinstance(result, str)
        assert len(result) > 0

        result_intermediate = await status(level="intermediate")
        assert isinstance(result_intermediate, str)

        result_advanced = await status(level="advanced")
        assert isinstance(result_advanced, str)


class TestErrorHandling:
    """Tests for error handling in system_ops."""

    @pytest.mark.asyncio
    async def test_get_process_info_invalid_pid(self, mock_bridge):
        """Test get_process_info with invalid PID."""
        mock_bridge.get_process_info.return_value = {
            "status": "error",
            "error": {"code": "process_not_found", "message": "Process not found"},
        }
        result = await get_process_info(99999)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_get_disk_usage_nonexistent_path(self, mock_bridge):
        """Test get_disk_usage with nonexistent path."""
        mock_bridge.get_disk_usage.return_value = {
            "status": "error",
            "error": {"code": "path_not_found", "message": "Path not found"},
        }
        result = await get_disk_usage("Z:/nonexistent")
        assert result["status"] == "error"
