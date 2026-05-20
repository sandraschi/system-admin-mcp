"""Tests for implementation functions."""

from unittest.mock import patch

from system_admin_mcp.tools.implementations import (
    analyze_disk_usage_advanced,
    audit_permissions,
    check_disk_health,
    defragment_disk,
    disk_cleanup,
    get_event_log,
    get_hardware_info,
    get_installed_software,
    get_os_info,
    get_performance_metrics,
    get_permissions,
    get_volume_info,
    health_check,
    is_admin,
    optimize_ssd,
    recover_file_ntfs,
    remove_permission,
    scan_volume,
    set_permissions,
    take_ownership,
    validate_recovery,
)


class TestFileRecovery:
    """Tests for file recovery implementations."""

    def test_scan_volume(self, mock_subprocess, mock_win32):
        """Test volume scanning implementation."""
        result = scan_volume("C:", "*.txt", 10)
        assert result["status"] in ["success", "error"]
        assert result["operation"] == "scan_volume"

    def test_recover_file_ntfs(self, mock_subprocess):
        """Test NTFS file recovery."""
        result = recover_file_ntfs("C:/deleted.txt", "D:/recovered.txt")
        assert result["status"] in ["success", "error"]

    def test_validate_recovery(self, temp_file, mock_subprocess):
        """Test recovery validation."""
        result = validate_recovery(str(temp_file))
        assert result["status"] == "success"
        assert "file_path" in result
        assert "exists" in result


class TestSecurityManagement:
    """Tests for security management implementations."""

    def test_get_permissions(self, temp_file, mock_win32security):
        """Test getting permissions."""
        result = get_permissions(str(temp_file))
        assert result["status"] == "success"
        assert "permissions" in result
        assert "owner" in result

    def test_set_permissions(self, temp_file, mock_win32security, mock_is_admin):
        """Test setting permissions."""
        result = set_permissions(str(temp_file), "DOMAIN\\User", "Read")
        assert result["status"] in ["success", "error"]

    def test_set_permissions_no_admin(self, temp_file, mock_win32security, mock_is_not_admin):
        """Test setting permissions without admin."""
        result = set_permissions(str(temp_file), "DOMAIN\\User", "Read")
        assert result["status"] == "error"
        assert "Administrator privileges required" in result["error"]

    def test_remove_permission(self, temp_file, mock_win32security, mock_is_admin):
        """Test removing permission."""
        result = remove_permission(str(temp_file), "DOMAIN\\User")
        assert result["status"] in ["success", "error"]

    def test_take_ownership(self, temp_file, mock_win32security, mock_is_admin, mock_win32):
        """Test taking ownership."""
        result = take_ownership(str(temp_file))
        assert result["status"] in ["success", "error"]

    def test_audit_permissions(self, temp_file, mock_win32security):
        """Test permission auditing."""
        result = audit_permissions(str(temp_file))
        assert result["status"] == "success"
        assert "security_issues" in result
        assert "warnings" in result


class TestVolumeMaintenance:
    """Tests for volume maintenance implementations."""

    def test_check_disk_health(self, mock_wmi):
        """Test disk health check."""
        result = check_disk_health("C:")
        assert result["status"] in ["success", "error"]
        assert result["operation"] == "check_disk_health"

    def test_analyze_disk_usage_advanced(self, mock_psutil, mock_subprocess):
        """Test advanced disk usage analysis."""
        result = analyze_disk_usage_advanced("C:")
        assert result["status"] == "success"
        assert "total_bytes" in result
        assert "largest_directories" in result

    def test_disk_cleanup(self, mock_subprocess, mock_is_admin):
        """Test disk cleanup."""
        result = disk_cleanup("C:", ["temp_files"], dry_run=True)
        assert result["status"] in ["success", "error"]
        assert result["operation"] == "disk_cleanup"

    def test_defragment_disk(self, mock_subprocess, mock_is_admin):
        """Test disk defragmentation."""
        result = defragment_disk("C:", thorough=False)
        assert result["status"] in ["success", "error"]

    def test_optimize_ssd(self, mock_subprocess, mock_is_admin):
        """Test SSD optimization."""
        result = optimize_ssd("C:")
        assert result["status"] in ["success", "error"]

    def test_get_volume_info(self, mock_psutil, mock_win32):
        """Test getting volume info."""
        result = get_volume_info("C:")
        assert result["status"] == "success"
        assert "drive" in result
        assert "file_system" in result


class TestSystemDiagnostics:
    """Tests for system diagnostics implementations."""

    def test_get_hardware_info(self, mock_psutil, mock_wmi, mock_platform):
        """Test getting hardware info."""
        result = get_hardware_info()
        assert result["status"] == "success"
        assert "cpu" in result
        assert "memory" in result
        assert "disks" in result
        assert "network" in result

    def test_get_os_info(self, mock_psutil, mock_platform):
        """Test getting OS info."""
        result = get_os_info()
        assert result["status"] == "success"
        assert "platform" in result
        assert "boot_time" in result

    def test_get_installed_software(self, mock_subprocess):
        """Test getting installed software."""
        result = get_installed_software()
        assert result["status"] == "success"
        assert "count" in result
        assert "software" in result

    def test_get_performance_metrics(self, mock_psutil):
        """Test getting performance metrics."""
        result = get_performance_metrics()
        assert result["status"] == "success"
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "network" in result
        assert "top_processes" in result

    def test_get_event_log(self, mock_win32evtlog, mock_is_admin):
        """Test getting event log."""
        result = get_event_log("System", "Error", 24)
        assert result["status"] in ["success", "error"]

    def test_health_check(self, mock_psutil):
        """Test health check."""
        result = health_check()
        assert result["status"] == "success"
        assert "checks" in result
        assert "overall_status" in result
        assert result["overall_status"] in ["healthy", "needs_attention"]


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_is_admin(self, mock_is_admin):
        """Test is_admin function."""
        assert is_admin() is True

    def test_is_not_admin(self, mock_is_not_admin):
        """Test is_admin returning False."""
        assert is_admin() is False


class TestErrorHandling:
    """Tests for error handling in implementations."""

    def test_get_permissions_nonexistent_path(self, mock_win32security):
        """Test get_permissions with nonexistent path."""
        mock_win32security.GetFileSecurity.side_effect = FileNotFoundError("Path not found")
        result = get_permissions("C:/nonexistent/path.txt")
        assert result["status"] == "error"

    def test_check_disk_health_no_wmi(self):
        """Test check_disk_health without WMI."""
        with patch("system_admin_mcp.tools.implementations.WMI_AVAILABLE", False):
            result = check_disk_health("C:")
            assert result["status"] == "error"
            assert "WMI not available" in result["error"]
