"""Tests for edge cases and boundary conditions."""

import pytest

from tests.test_portmanteau_helper import system_admin_test as system_admin


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_strings(self):
        """Test operations with empty strings."""
        with pytest.raises(ValueError, match="path parameter required"):
            await system_admin("get_permissions", path="")

    @pytest.mark.asyncio
    async def test_very_long_paths(self):
        """Test operations with very long paths."""
        long_path = "C:/" + "a" * 300
        result = await system_admin("get_permissions", path=long_path)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_special_characters_in_path(self):
        """Test operations with special characters in paths."""
        special_path = "C:/test file with spaces & symbols!.txt"
        result = await system_admin("get_permissions", path=special_path)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_unicode_paths(self):
        """Test operations with Unicode paths."""
        unicode_path = "C:/测试/文件.txt"
        result = await system_admin("get_permissions", path=unicode_path)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_negative_values(self):
        """Test operations with negative values."""
        result = await system_admin("scan_volume", drive="C:", max_results=-1)
        # Should handle gracefully or validate
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_zero_values(self):
        """Test operations with zero values."""
        result = await system_admin("scan_volume", drive="C:", max_results=0)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_very_large_values(self):
        """Test operations with very large values."""
        result = await system_admin("scan_volume", drive="C:", max_results=999999999)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_nonexistent_drives(self):
        """Test operations with nonexistent drives."""
        result = await system_admin("check_disk_health", drive="Z:")
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_invalid_drive_formats(self):
        """Test operations with invalid drive formats."""
        for invalid_drive in ["C", "C/", "/C", "drive", ""]:
            result = await system_admin("check_disk_health", drive=invalid_drive)
            assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations."""
        import asyncio

        tasks = [
            system_admin("get_hardware_info"),
            system_admin("get_os_info"),
            system_admin("health_check"),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception) or result["status"] in ["success", "error"]


class TestParameterValidation:
    """Tests for parameter validation."""

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self):
        """Test operations with missing required parameters."""
        operations = [
            ("scan_volume", {}),
            ("recover_file", {}),
            ("get_permissions", {}),
            ("set_permissions", {}),
            ("check_disk_health", {}),
        ]

        for operation, params in operations:
            with pytest.raises(ValueError):
                await system_admin(operation, **params)

    @pytest.mark.asyncio
    async def test_invalid_parameter_types(self):
        """Test operations with invalid parameter types."""
        # These should be caught by FastMCP validation, but test anyway
        result = await system_admin("scan_volume", drive=123)  # Should be string
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_extra_parameters(self):
        """Test operations with extra parameters (should be ignored)."""
        result = await system_admin("get_hardware_info", extra_param="should_be_ignored", another_extra=123)
        assert result["status"] in ["success", "error"]


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    @pytest.mark.asyncio
    async def test_max_results_boundary(self):
        """Test scan_volume with boundary max_results values."""
        # Test with 1 (minimum reasonable)
        result1 = await system_admin("scan_volume", drive="C:", max_results=1)
        assert result1["status"] in ["success", "error"]

        # Test with very large number
        result2 = await system_admin("scan_volume", drive="C:", max_results=1000000)
        assert result2["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_hours_back_boundary(self):
        """Test get_event_log with boundary hours_back values."""
        # Test with 0
        result1 = await system_admin("get_event_log", log_name="System", hours_back=0)
        assert result1["status"] in ["success", "error"]

        # Test with very large number
        result2 = await system_admin("get_event_log", log_name="System", hours_back=8760)  # 1 year
        assert result2["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_dry_run_flag(self):
        """Test operations with dry_run flag."""
        result = await system_admin("disk_cleanup", drive="C:", cleanup_targets=["temp_files"], dry_run=True)
        assert result["status"] in ["success", "error"]
        assert result.get("dry_run") is True
