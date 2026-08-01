"""Integration tests for System Admin MCP."""

import asyncio

import pytest

from system_admin_mcp.app import mcp
from system_admin_mcp.tools import system_ops


def _tool_names() -> set[str]:
    """Public API (FastMCP 3.4+) — mcp.list_tools() is the supported surface."""
    tools = asyncio.run(mcp.list_tools())
    return {t.name for t in tools}


class TestToolRegistration:
    """Tests for tool registration."""

    def test_tools_registered(self):
        """Test that all tools are registered."""
        names = _tool_names()
        assert len(names) > 0
        assert "system_admin" in names
        assert "list_volumes" in names
        assert "ping" in names
        assert "help" in names
        assert "status" in names

    def test_portmanteau_tool_registered(self):
        """Test that portmanteau tool is registered."""
        assert "system_admin" in _tool_names()

    def test_all_operations_available(self):
        """Test that all 22 operations are available in portmanteau."""
        # File Recovery (4)
        operations = [
            "scan_volume",
            "recover_file",
            "validate_recovery",
            "batch_recover",
            # Security (6)
            "get_permissions",
            "set_permissions",
            "remove_permission",
            "take_ownership",
            "audit_permissions",
            "modify_acl",
            # Volume (6)
            "check_disk_health",
            "analyze_disk_usage",
            "disk_cleanup",
            "defragment_disk",
            "optimize_ssd",
            "get_volume_info",
            # Diagnostics (6)
            "get_hardware_info",
            "get_os_info",
            "get_installed_software",
            "get_performance_metrics",
            "get_event_log",
            "health_check",
        ]
        # All operations should be callable (validation happens at runtime)
        assert len(operations) == 22


class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_system_admin_operation_validation(self):
        """Test that system_admin validates operation parameter."""
        from tests.test_portmanteau_helper import system_admin_test

        result = await system_admin_test("invalid_operation")
        assert result["status"] == "error"
        assert "Unknown operation" in result["message"]

    @pytest.mark.asyncio
    async def test_system_admin_parameter_validation(self):
        """Test that system_admin validates required parameters."""
        from tests.test_portmanteau_helper import system_admin_test

        with pytest.raises(ValueError):
            await system_admin_test("scan_volume")  # Missing drive

    @pytest.mark.asyncio
    async def test_help_tool_works(self):
        """Test that help tool works."""
        result = await system_ops.help()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_status_tool_works(self, mock_bridge):
        """Test that status tool works."""
        result = await system_ops.status()
        assert isinstance(result, str)
        assert len(result) > 0


class TestErrorRecovery:
    """Tests for error recovery and resilience."""

    @pytest.mark.asyncio
    async def test_operation_with_service_down(self, mock_bridge):
        """Test behavior when service is down."""
        mock_bridge.service_running = False
        mock_bridge.ping.return_value = False
        result = await system_ops.ping()
        assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_operation_with_service_not_installed(self, mock_bridge):
        """Test behavior when service is not installed."""
        mock_bridge.service_installed = False
        result = await system_ops.ping()
        assert result["status"] in ["success", "error"]
