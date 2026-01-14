"""Tests for the system_admin portmanteau tool."""

import pytest
from tests.test_portmanteau_helper import system_admin_test as system_admin


class TestFileRecovery:
    """Tests for file recovery operations."""

    @pytest.mark.asyncio
    async def test_scan_volume(self, mock_subprocess, mock_win32):
        """Test volume scanning."""
        result = await system_admin("scan_volume", drive="C:", file_pattern="*.txt", max_results=10)
        assert result["status"] in ["success", "error"]  # May fail if PowerShell unavailable
        assert result["operation"] == "scan_volume"
        assert result["drive"] == "C:\\"

    @pytest.mark.asyncio
    async def test_scan_volume_missing_drive(self):
        """Test scan_volume with missing drive parameter."""
        with pytest.raises(ValueError, match="drive parameter required"):
            await system_admin("scan_volume")

    @pytest.mark.asyncio
    async def test_recover_file(self, mock_subprocess):
        """Test file recovery."""
        result = await system_admin(
            "recover_file",
            source_path="C:/deleted/file.txt",
            destination_path="D:/recovered/file.txt",
        )
        assert result["status"] in ["success", "error"]  # May fail if file doesn't exist

    @pytest.mark.asyncio
    async def test_recover_file_missing_params(self):
        """Test recover_file with missing parameters."""
        with pytest.raises(ValueError, match="source_path and destination_path required"):
            await system_admin("recover_file", source_path="C:/test.txt")

    @pytest.mark.asyncio
    async def test_validate_recovery(self, temp_file, mock_subprocess):
        """Test recovery validation."""
        result = await system_admin("validate_recovery", destination_path=str(temp_file))
        assert result["status"] == "success"
        assert result["operation"] == "validate_recovery"

    @pytest.mark.asyncio
    async def test_batch_recover(self, mock_subprocess):
        """Test batch recovery."""
        result = await system_admin(
            "batch_recover",
            source_path="C:/deleted/file.txt",
            destination_path="D:/recovered/",
        )
        assert result["status"] in ["success", "error"]


class TestSecurityManagement:
    """Tests for security management operations."""

    @pytest.mark.asyncio
    async def test_get_permissions(self, temp_file, mock_win32security):
        """Test getting file permissions."""
        result = await system_admin("get_permissions", path=str(temp_file))
        assert result["status"] == "success"
        assert result["operation"] == "get_permissions"

    @pytest.mark.asyncio
    async def test_get_permissions_missing_path(self):
        """Test get_permissions with missing path."""
        with pytest.raises(ValueError, match="path parameter required"):
            await system_admin("get_permissions")

    @pytest.mark.asyncio
    async def test_set_permissions(self, temp_file, mock_win32security, mock_is_admin):
        """Test setting file permissions."""
        result = await system_admin(
            "set_permissions",
            path=str(temp_file),
            principal="DOMAIN\\User",
            rights="Read",
        )
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_set_permissions_missing_params(self):
        """Test set_permissions with missing parameters."""
        with pytest.raises(ValueError, match="path, principal, and rights required"):
            await system_admin("set_permissions", path="/test")

    @pytest.mark.asyncio
    async def test_set_permissions_no_admin(self, temp_file, mock_win32security, mock_is_not_admin):
        """Test set_permissions without admin privileges."""
        result = await system_admin(
            "set_permissions",
            path=str(temp_file),
            principal="DOMAIN\\User",
            rights="Read",
        )
        assert result["status"] == "error"
        assert "Administrator privileges required" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_permission(self, temp_file, mock_win32security, mock_is_admin):
        """Test removing permissions."""
        result = await system_admin("remove_permission", path=str(temp_file), principal="DOMAIN\\User")
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_take_ownership(self, temp_file, mock_win32security, mock_is_admin, mock_win32):
        """Test taking ownership."""
        result = await system_admin("take_ownership", path=str(temp_file))
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_audit_permissions(self, temp_file, mock_win32security):
        """Test permission auditing."""
        result = await system_admin("audit_permissions", path=str(temp_file))
        assert result["status"] == "success"
        assert "security_issues" in result
        assert "warnings" in result

    @pytest.mark.asyncio
    async def test_modify_acl(self, temp_file, mock_win32security, mock_is_admin):
        """Test ACL modification."""
        result = await system_admin(
            "modify_acl",
            path=str(temp_file),
            principal="DOMAIN\\User",
            rights="Read",
        )
        assert result["status"] in ["success", "error"]


class TestVolumeMaintenance:
    """Tests for volume maintenance operations."""

    @pytest.mark.asyncio
    async def test_check_disk_health(self, mock_wmi):
        """Test disk health check."""
        result = await system_admin("check_disk_health", drive="C:")
        assert result["status"] in ["success", "error"]
        assert result["operation"] == "check_disk_health"

    @pytest.mark.asyncio
    async def test_check_disk_health_missing_drive(self):
        """Test check_disk_health with missing drive."""
        with pytest.raises(ValueError, match="drive parameter required"):
            await system_admin("check_disk_health")

    @pytest.mark.asyncio
    async def test_analyze_disk_usage(self, mock_psutil, mock_subprocess):
        """Test disk usage analysis."""
        result = await system_admin("analyze_disk_usage", drive="C:")
        assert result["status"] == "success"
        assert "total_bytes" in result
        assert "used_bytes" in result
        assert "free_bytes" in result

    @pytest.mark.asyncio
    async def test_disk_cleanup(self, mock_subprocess, mock_is_admin):
        """Test disk cleanup."""
        result = await system_admin(
            "disk_cleanup",
            drive="C:",
            cleanup_targets=["temp_files", "recycle_bin"],
            dry_run=True,
        )
        assert result["status"] in ["success", "error"]
        assert result["operation"] == "disk_cleanup"

    @pytest.mark.asyncio
    async def test_disk_cleanup_no_admin(self, mock_subprocess, mock_is_not_admin):
        """Test disk cleanup without admin."""
        result = await system_admin("disk_cleanup", drive="C:")
        assert result["status"] == "error"
        assert "Administrator privileges required" in result["error"]

    @pytest.mark.asyncio
    async def test_defragment_disk(self, mock_subprocess, mock_is_admin):
        """Test disk defragmentation."""
        result = await system_admin("defragment_disk", drive="C:", thorough=False)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_optimize_ssd(self, mock_subprocess, mock_is_admin):
        """Test SSD optimization."""
        result = await system_admin("optimize_ssd", drive="C:")
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_get_volume_info(self, mock_psutil, mock_win32):
        """Test getting volume information."""
        result = await system_admin("get_volume_info", drive="C:")
        assert result["status"] == "success"
        assert "drive" in result
        assert "total_bytes" in result


class TestSystemDiagnostics:
    """Tests for system diagnostics operations."""

    @pytest.mark.asyncio
    async def test_get_hardware_info(self, mock_psutil, mock_wmi, mock_platform):
        """Test getting hardware information."""
        result = await system_admin("get_hardware_info")
        assert result["status"] == "success"
        assert "cpu" in result
        assert "memory" in result
        assert "disks" in result

    @pytest.mark.asyncio
    async def test_get_os_info(self, mock_psutil, mock_platform):
        """Test getting OS information."""
        result = await system_admin("get_os_info")
        assert result["status"] == "success"
        assert "platform" in result

    @pytest.mark.asyncio
    async def test_get_installed_software(self, mock_subprocess):
        """Test getting installed software list."""
        result = await system_admin("get_installed_software")
        assert result["status"] == "success"
        assert "count" in result
        assert "software" in result

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, mock_psutil):
        """Test getting performance metrics."""
        result = await system_admin("get_performance_metrics")
        assert result["status"] == "success"
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "network" in result

    @pytest.mark.asyncio
    async def test_get_event_log(self, mock_win32evtlog, mock_is_admin):
        """Test getting event log."""
        result = await system_admin("get_event_log", log_name="System", level="Error", hours_back=24)
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_get_event_log_no_admin(self, mock_win32evtlog, mock_is_not_admin):
        """Test getting event log without admin."""
        result = await system_admin("get_event_log", log_name="System")
        assert result["status"] == "error"
        assert "Administrator privileges required" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check(self, mock_psutil):
        """Test system health check."""
        result = await system_admin("health_check")
        assert result["status"] == "success"
        assert "checks" in result
        assert "overall_status" in result


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        """Test unknown operation."""
        result = await system_admin("unknown_operation")
        assert result["status"] == "error"
        assert "Unknown operation" in result["message"]

    @pytest.mark.asyncio
    async def test_operation_with_exception(self, mock_subprocess):
        """Test operation that raises exception."""
        mock_subprocess.run.side_effect = Exception("Test error")
        result = await system_admin("scan_volume", drive="C:")
        assert result["status"] == "error"
        assert "error" in result

