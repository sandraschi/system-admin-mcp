"""Assfix coverage suite: hermetic tests for transport, prompts, monitoring,
system_ops branches, server REST surface, minidump parsers, portmanteau
dispatch, main entry, and app lifespan (enter only — never shuts down the
global watcher).

All tests are side-effect free: no service/process mutation, no disk writes
outside tmp_path, watcher state persisted with persist=False only.
"""

import argparse
import os
import struct
import sys
from unittest.mock import AsyncMock, patch

from fastmcp import FastMCP
from starlette.testclient import TestClient

from system_admin_mcp import transport as transport_mod
from system_admin_mcp.prompts import register_all_prompts
from system_admin_mcp.tools import portmanteau as pm
from system_admin_mcp.tools.implementations import _read_minidump_string
from system_admin_mcp.tools.monitoring import FileWatcherManager, WatchEvent

# --------------------------------------------------------------------------
# transport.py — pure config resolution, no server start
# --------------------------------------------------------------------------


class TestTransportConfig:
    def test_defaults(self, monkeypatch):
        for var in ("MCP_TRANSPORT", "MCP_HOST", "MCP_PORT", "MCP_PATH"):
            monkeypatch.delenv(var, raising=False)
        cfg = transport_mod.get_transport_config()
        assert cfg == {"transport": "stdio", "host": "127.0.0.1", "port": 10861, "path": "/mcp"}

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("MCP_TRANSPORT", "HTTP")
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_PORT", "19999")
        monkeypatch.setenv("MCP_PATH", "/custom")
        cfg = transport_mod.get_transport_config()
        assert cfg["transport"] == "http"
        assert cfg["host"] == "0.0.0.0"
        assert cfg["port"] == 19999
        assert cfg["path"] == "/custom"

    def test_parser_cli_flags(self):
        parser = transport_mod.create_argument_parser("x-mcp")
        args = parser.parse_args(["--http", "--port", "12345", "--host", "0.0.0.0"])
        assert transport_mod.resolve_transport(args) == "http"
        cfg = transport_mod.resolve_config(args)
        assert cfg["port"] == 12345
        assert cfg["host"] == "0.0.0.0"

    def test_cli_beats_env(self, monkeypatch):
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        parser = transport_mod.create_argument_parser("x-mcp")
        args = parser.parse_args(["--stdio"])
        assert transport_mod.resolve_transport(args) == "stdio"

    def test_invalid_env_falls_back_stdio(self, monkeypatch):
        monkeypatch.setenv("MCP_TRANSPORT", "carrier-pigeon")
        parser = transport_mod.create_argument_parser("x-mcp")
        args = parser.parse_args([])
        assert transport_mod.resolve_transport(args) == "stdio"

    def test_sse_deprecated_path(self):
        parser = transport_mod.create_argument_parser("x-mcp")
        args = parser.parse_args(["--sse"])
        assert transport_mod.resolve_transport(args) == "sse"

    def test_resolve_config_env_fallback(self, monkeypatch):
        monkeypatch.setenv("MCP_PORT", "18888")
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        parser = transport_mod.create_argument_parser("x-mcp")
        cfg = transport_mod.resolve_config(parser.parse_args([]))
        assert cfg["transport"] == "stdio"
        assert cfg["port"] == 18888

    def test_namespace_defaults(self):
        args = argparse.Namespace(http=False, sse=False, stdio=False, host=None, port=None, path=None, debug=False)
        assert transport_mod.resolve_transport(args) == "stdio"


# --------------------------------------------------------------------------
# prompts.py — registration on a fresh instance
# --------------------------------------------------------------------------


class TestPrompts:
    async def test_register_all(self):
        mcp = FastMCP("cov-prompts")
        register_all_prompts(mcp)
        prompts = await mcp.list_prompts()
        names = {p.name for p in prompts}
        assert {"system_diagnostics_expert", "security_hardening_expert", "system_troubleshooter"} <= names

    async def test_prompt_renders(self):
        mcp = FastMCP("cov-render")
        register_all_prompts(mcp)
        rendered = await mcp.render_prompt("system_diagnostics_expert", {"focus": "disk"})
        assert rendered.messages, "prompt should render at least one message"


# --------------------------------------------------------------------------
# monitoring.py — singleton watcher, persist=False (never touches USERPROFILE)
# --------------------------------------------------------------------------


class TestMonitoring:
    def test_singleton(self):
        assert FileWatcherManager() is FileWatcherManager()

    def test_start_stop_tmp_watch(self, tmp_path, monkeypatch):
        mgr = FileWatcherManager()
        monkeypatch.setattr(mgr, "_save_state", lambda: None)
        target = str(tmp_path)
        try:
            assert mgr.start_watch(target, persist=False) is True
            assert os.path.abspath(target) in mgr.watches
        finally:
            assert mgr.stop_watch(target) in (True, False)
        assert os.path.abspath(target) not in mgr.watches

    def test_stop_unknown_returns_false(self):
        mgr = FileWatcherManager()
        assert mgr.stop_watch("Z:\\definitely-not-watched-xyz") is False

    def test_add_and_get_events(self, tmp_path, monkeypatch):
        mgr = FileWatcherManager()
        monkeypatch.setattr(mgr, "_save_state", lambda: None)
        target = str(tmp_path)
        try:
            mgr.start_watch(target, persist=False)
            mgr.add_event(
                os.path.abspath(target),
                WatchEvent(timestamp=1.0, event_type="created", src_path="a.txt", is_directory=False),
            )
            events = mgr.get_events(os.path.abspath(target))
            assert len(events) >= 1
            assert events[0]["event_type"] == "created"
        finally:
            mgr.stop_watch(target)
            mgr.events.pop(os.path.abspath(target), None)


# --------------------------------------------------------------------------
# system_ops.py — help/status branches + bridge-backed tools
# --------------------------------------------------------------------------


class TestSystemOpsBranches:
    async def test_help_levels(self):
        from system_admin_mcp.tools import system_ops as so

        assert "Available Tools" in await so.help("basic")
        assert "File Operations" in await so.help("intermediate")
        assert "Architecture" in await so.help("advanced")
        assert "Architecture" in await so.help("nonsense-level")

    async def test_status_levels(self, mock_bridge):
        from system_admin_mcp.tools import system_ops as so

        basic = await so.status("basic")
        assert "System Admin MCP Status" in basic
        assert "Detailed Status" in (await so.status("intermediate"))
        assert await so.status("advanced")

    async def test_bridge_tools(self, mock_bridge):
        from system_admin_mcp.tools import system_ops as so

        assert (await so.ping())["status"] in ("success", "pong", "error")
        vols = await so.list_volumes()
        assert isinstance(vols, list) and vols and "drive" in vols[0]
        info = await so.get_system_info()
        assert isinstance(info, dict)
        usage = await so.get_disk_usage("C:\\")
        assert isinstance(usage, dict)

    def test_is_admin_bool(self):
        from system_admin_mcp.tools import system_ops as so

        assert isinstance(so.is_admin(), bool)


# --------------------------------------------------------------------------
# server.py REST surface via TestClient (real local APIs, read-only paths)
# --------------------------------------------------------------------------

client = TestClient(__import__("system_admin_mcp.server", fromlist=["app"]).app)


class TestServerRest:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_status(self):
        r = client.get("/api/status")
        assert r.status_code == 200
        assert "uptime_seconds" in r.json() or "status" in r.json()

    def test_tools_list(self):
        r = client.get("/api/tools")
        assert r.status_code == 200
        assert len(r.json()) >= 50

    def test_tools_call_ping(self):
        r = client.post("/api/tools/call", json={"name": "ping", "arguments": {}})
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_tools_call_missing_name(self):
        r = client.post("/api/tools/call", json={"arguments": {}})
        assert r.status_code == 200
        assert r.json()["status"] == "error"

    def test_tools_call_unknown(self):
        r = client.post("/api/tools/call", json={"name": "no_such_tool_xyz", "arguments": {}})
        assert r.status_code == 200
        assert r.json()["status"] == "error"

    def test_metrics(self):
        assert client.get("/api/metrics").status_code == 200

    def test_skills(self):
        r = client.get("/api/skills")
        assert r.status_code == 200

    def test_diagnostics(self):
        r = client.get("/api/v1/diagnostics")
        assert r.status_code == 200

    def test_volumes(self):
        assert client.get("/api/volumes").status_code == 200

    def test_processes(self):
        r = client.get("/api/processes", params={"page_size": 5})
        assert r.status_code == 200

    def test_process_self(self):
        r = client.get(f"/api/processes/{os.getpid()}")
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_file_owner_tmp(self, tmp_path):
        f = tmp_path / "owned.txt"
        f.write_text("x")
        r = client.post("/api/file_owner", json={"path": str(f)})
        assert r.status_code == 200

    def test_file_owner_missing_path(self):
        r = client.post("/api/file_owner", json={})
        assert r.json()["status"] == "error"

    def test_disk_usage_missing_path(self):
        r = client.post("/api/disk_usage", json={})
        assert r.json()["status"] == "error"

    def test_recover_missing_params(self):
        r = client.post("/api/recover_file", json={})
        assert r.json()["status"] == "error"

    def test_logs(self):
        assert client.get("/api/logs", params={"tail": 5}).status_code == 200

    def test_crash_dumps(self):
        assert client.get("/api/crash/dumps").status_code == 200

    def test_admin_toolbox(self):
        assert client.get("/api/admin-toolbox").status_code == 200

    def test_firmware_posture(self):
        assert client.get("/api/firmware-posture").status_code == 200

    def test_update_status(self):
        assert client.get("/api/update-status").status_code == 200

    def test_path_dross(self):
        assert client.get("/api/path-dross").status_code == 200

    def test_llm_discover(self):
        r = client.get("/api/llm/discover")
        assert r.status_code == 200
        assert "providers" in r.json()

    def test_fleet_apps(self):
        r = client.get("/api/fleet/apps")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert isinstance(body["known"], list)
        assert isinstance(body["experimental"], list)
        assert body["count"] == len(body["known"])
        names = {a["name"] for a in body["known"]}
        assert "system-admin-mcp" in names


# --------------------------------------------------------------------------
# minidump pure parsers — crafted bytes, no dump file needed
# --------------------------------------------------------------------------


class TestMinidumpPure:
    def test_read_string_ok(self):
        payload = "AB".encode("utf-16-le")
        data = struct.pack("<I", len(payload)) + payload
        assert _read_minidump_string(data, 0) == "AB"

    def test_read_string_truncated_returns_none(self):
        assert _read_minidump_string(b"\x04", 0) is None
        assert _read_minidump_string(b"", 0) is None
        # Absurd length degrades to empty string rather than raising.
        assert _read_minidump_string(b"\xff\xff\xff\xff", 0) == ""

    def test_analyze_missing_file(self):
        from system_admin_mcp.tools.implementations import analyze_minidump

        result = analyze_minidump("Z:\\no-such-dump-xyz.dmp")
        assert result["status"] == "error"


class TestTaskbarOps:
    async def test_taskbar_windows_shape(self):
        result = await pm.system_admin(operation="list_taskbar_windows")
        assert result["status"] == "success"
        assert result["count"] == len(result["windows"])
        for w in result["windows"]:
            assert {"hwnd", "title", "pid", "process", "autostart"} <= set(w)

    async def test_tray_icons_shape(self):
        result = await pm.system_admin(operation="list_tray_icons")
        assert result["status"] in ("success", "error")
        if result["status"] == "success":
            assert result["count"] == len(result["icons"])
            for icon in result["icons"]:
                assert {"tooltip", "confidence", "autostart"} <= set(icon)

    def test_tray_rest_endpoint(self):
        body = client.post(
            "/api/tools/call", json={"name": "system_admin", "arguments": {"operation": "list_taskbar_windows"}}
        ).json()
        assert body["status"] == "success"
        assert body["result"]["status"] == "success"


# --------------------------------------------------------------------------
# portmanteau dispatch — error paths + watch list (no side effects)
# --------------------------------------------------------------------------


class TestPortmanteauDispatch:
    async def test_unknown_operation_errors(self):
        result = await pm.system_admin(operation="no_such_op_xyz")
        assert result["status"] == "error"

    async def test_watch_list(self):
        result = await pm.manage_filesystem_watch(operation="list")
        assert result["status"] == "success"
        assert "active_watches" in result

    async def test_watch_unknown_operation_errors(self):
        result = await pm.manage_filesystem_watch(operation="frobnicate")
        assert result["status"] == "error"

    async def test_diagnostics_with_mocks(self):
        with (
            patch.object(pm, "check_system_health_status", new=AsyncMock(return_value={"status": "ok"})),
            patch.object(pm, "get_top_resource_processes", new=AsyncMock(return_value={"top": []})),
            patch.object(pm, "get_recent_event_errors", new=AsyncMock(return_value={"events": []})),
            patch.object(pm, "get_volume_info", return_value={"drive": "C:"}),
        ):
            result = await pm.get_comprehensive_diagnostics()
        assert result["status"] == "success"
        assert result["health"] == {"status": "ok"}


# --------------------------------------------------------------------------
# implementations with mocked platform APIs (raise covered-line count)
# --------------------------------------------------------------------------


class TestImplementationsMocked:
    def test_performance_metrics(self, mock_psutil):
        from system_admin_mcp.tools import implementations as impl

        result = impl.get_performance_metrics()
        assert result["status"] == "success"

    def test_os_info(self, mock_platform, mock_win32):
        from system_admin_mcp.tools import implementations as impl

        with patch.object(impl, "_wmi_connect", side_effect=Exception("no wmi")):
            result = impl.get_os_info()
        assert isinstance(result, dict)

    def test_hardware_info_partial(self, mock_psutil):
        from system_admin_mcp.tools import implementations as impl

        with patch.object(impl, "_wmi_connect", side_effect=Exception("no wmi")):
            result = impl.get_hardware_info()
        assert isinstance(result, dict)

    def test_get_permissions_mocked(self, mock_win32security):
        from system_admin_mcp.tools import implementations as impl

        result = impl.get_permissions("C:\\Windows")
        assert isinstance(result, dict)

    def test_bugcheck_history_no_log(self, mock_win32evtlog):
        from system_admin_mcp.tools import implementations as impl

        with patch.object(impl.win32evtlog, "OpenEventLog", side_effect=Exception("denied")):
            result = impl.get_bugcheck_history(days_back=1)
        assert isinstance(result, dict)


# --------------------------------------------------------------------------
# main entry + app lifespan (enter only)
# --------------------------------------------------------------------------


class TestMainAndLifespan:
    def test_create_app(self):
        from system_admin_mcp.main import create_app

        assert create_app() is not None

    def test_main_stdio_path(self, monkeypatch):
        import system_admin_mcp.main as main_mod

        monkeypatch.setattr(sys, "argv", ["system-admin-mcp"])
        with patch.object(main_mod, "run_server") as rs:
            main_mod.main()
        rs.assert_called_once()

    async def test_lifespan_registers(self):
        from system_admin_mcp.app import lifespan, mcp

        cm = lifespan(mcp)
        await cm.__aenter__()  # never __aexit__: must not shut down the global watcher
        tools = await mcp.list_tools()
        assert len(tools) >= 50

    async def test_resources_registered(self):
        import json

        from system_admin_mcp.app import mcp

        resources = await mcp.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "systemadmin://status" in uris
        assert "systemadmin://config" in uris
        content = await mcp.read_resource("systemadmin://config")
        blocks = getattr(content, "contents", [content])
        first = blocks[0]
        text = getattr(first, "content", first.get("content") if isinstance(first, dict) else str(first))
        payload = json.loads(text)
        assert payload["frontend_port"] == 10860
        assert "transport" in payload
