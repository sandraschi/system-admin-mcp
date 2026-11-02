"""Tests for RAM map and standby purge tools in system-admin-mcp."""

import pytest

from system_admin_mcp.tools import native_memory, system_ops


def test_query_nt_memory_info():
    info = native_memory.query_nt_memory_info(detailed=True)
    if info is not None:
        assert info["status"] == "success"
        assert "categories" in info
        cats = info["categories"]
        assert cats["total_mb"] > 0
        assert cats["standby_total_mb"] >= 0
        assert "standby_priorities_mb" in info
        assert len(info["standby_priorities_mb"]) == 8


@pytest.mark.asyncio
async def test_get_ram_map_tool():
    res = await system_ops.get_ram_map(detailed=True)
    if res.get("status") == "success":
        assert "categories" in res
        assert "standby_priorities_mb" in res


@pytest.mark.asyncio
async def test_purge_standby_memory_confirm_gate():
    # Calling without confirm=True must fail
    res = await system_ops.purge_standby_memory(target="standby", confirm=False)
    assert res["status"] == "error"
    assert "confirm=True" in res["message"]


@pytest.mark.asyncio
async def test_purge_standby_memory_execution():
    # Calling with confirm=True should attempt execution and return structured status
    res = await system_ops.purge_standby_memory(target="standby", confirm=True)
    assert res["status"] in ("success", "error")
    assert res["operation"] == "purge_standby_memory"
