"""Safety tests: read-only kill switch, confirm gates, mutation audit log.

Never enables the airgap and never mutates: enable/disable are exercised
only through their refusal paths (missing confirm) plus read-only blocks.
Audit log is isolated via SYSTEMADMIN_AUDIT_LOG.
"""

import json

import pytest

from system_admin_mcp import mutation_guard as guard
from system_admin_mcp.tools import portmanteau as pm


@pytest.fixture
def audit_file(tmp_path, monkeypatch):
    path = tmp_path / "mutations.log"
    monkeypatch.setenv("SYSTEMADMIN_AUDIT_LOG", str(path))
    monkeypatch.delenv("SYSTEMADMIN_READ_ONLY", raising=False)
    return path


def _audit_entries(path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TestReadOnlyMode:
    def test_require_mutable_blocks_listed_ops(self, monkeypatch):
        monkeypatch.setenv("SYSTEMADMIN_READ_ONLY", "1")
        with pytest.raises(guard.ReadOnlyError):
            guard.require_mutable("kill_process")

    def test_require_mutable_allows_reads(self, monkeypatch):
        monkeypatch.setenv("SYSTEMADMIN_READ_ONLY", "1")
        guard.require_mutable("list_processes")
        guard.require_mutable("airgap_status")

    def test_require_mutable_off_by_default(self, monkeypatch):
        monkeypatch.delenv("SYSTEMADMIN_READ_ONLY", raising=False)
        guard.require_mutable("kill_process")

    def test_mutating_set_covers_dangerous_ops(self):
        for op in (
            "kill_process",
            "set_permissions",
            "take_ownership",
            "stop_service",
            "airgap_enable",
            "airgap_disable",
            "remove_permission",
        ):
            assert op in guard.MUTATING_OPS, op
        # disk_cleanup is deliberately NOT listed: dry_run previews must stay
        # usable in read-only mode; the function guards real deletes itself.
        assert "disk_cleanup" not in guard.MUTATING_OPS

    async def test_dispatch_blocks_in_read_only(self, monkeypatch, audit_file):
        monkeypatch.setenv("SYSTEMADMIN_READ_ONLY", "1")
        result = await pm.system_admin(operation="kill_process", pid=999999)
        assert result["status"] == "error"
        assert "read-only" in result["error"].lower()
        blocked = [e for e in _audit_entries(audit_file) if e.get("blocked")]
        assert blocked and blocked[0]["operation"] == "kill_process"

    async def test_direct_tool_blocked_in_read_only(self, monkeypatch, audit_file):
        from system_admin_mcp.tools import services_and_tasks as svc

        monkeypatch.setenv("SYSTEMADMIN_READ_ONLY", "1")
        # Guard lives inside the function's try: -> error dict (file style),
        # not a raised exception. Dispatch wraps it the same way.
        result = svc.set_taskbar_autohide(True)
        assert result["status"] == "error"
        assert "read-only" in result["error"].lower()
        assert any(e["operation"] == "set_taskbar_autohide" for e in _audit_entries(audit_file))


class TestConfirmGates:
    async def test_airgap_enable_requires_confirm(self, audit_file):
        result = await pm.system_admin(operation="airgap_enable")
        assert result["status"] == "error"
        assert "confirm" in result["error"].lower()

    async def test_airgap_disable_requires_confirm(self, audit_file):
        result = await pm.system_admin(operation="airgap_disable")
        assert result["status"] == "error"
        assert "confirm" in result["error"].lower()

    async def test_airgap_status_read(self, audit_file):
        result = await pm.system_admin(operation="airgap_status")
        assert result["status"] in ("success", "error")
        if result["status"] == "success":
            assert isinstance(result["airgapped"], bool)
            assert isinstance(result.get("firewall_outbound"), dict)


class TestAuditLog:
    def test_audit_appends_jsonl(self, audit_file, monkeypatch):
        monkeypatch.delenv("SYSTEMADMIN_READ_ONLY", raising=False)
        guard.audit_mutation("unit_test_op", {"x": 1})
        entries = _audit_entries(audit_file)
        assert entries and entries[-1]["operation"] == "unit_test_op"
        assert entries[-1]["x"] == 1
        assert "ts" in entries[-1]

    def test_audit_never_raises(self, monkeypatch):
        monkeypatch.setenv("SYSTEMADMIN_AUDIT_LOG", "Z:\\no-such-dir-xyz\\a.log")
        guard.audit_mutation("nope")  # must not raise
