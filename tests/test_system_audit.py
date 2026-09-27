"""Tests for system audit operations (unelevated-safe, live reads)."""

from system_admin_mcp.tools.implementations import (
    audit_drivers,
    audit_local_admins,
    audit_path_dross,
    audit_scheduled_tasks,
    audit_smb_shares,
    get_firmware_posture,
    get_reliability_history,
    get_update_status,
    list_shadow_copies,
    winget_outdated,
)


def _shape(result, op):
    assert result["operation"] == op
    assert result["status"] in ("success", "error")


class TestSystemAudit:
    def test_firmware_posture(self):
        r = get_firmware_posture()
        _shape(r, "get_firmware_posture")
        if r["status"] == "success":
            assert "virtualization_firmware" in r
            assert "tpm" in r and "secure_boot" in r

    def test_scheduled_tasks(self):
        r = audit_scheduled_tasks(5)
        _shape(r, "audit_scheduled_tasks")
        if r["status"] == "success":
            assert isinstance(r["tasks"], list)

    def test_update_status(self):
        r = get_update_status()
        assert r["status"] == "success"
        assert isinstance(r["pending_reboot"], bool)
        assert r["uptime_hours"] > 0

    def test_local_admins(self):
        r = audit_local_admins()
        _shape(r, "audit_local_admins")
        if r["status"] == "success":
            assert isinstance(r["administrators"], list)

    def test_smb_shares(self):
        r = audit_smb_shares()
        _shape(r, "audit_smb_shares")
        if r["status"] == "success":
            assert isinstance(r["shares"], list)

    def test_shadow_copies_gate(self):
        r = list_shadow_copies()
        assert r["operation"] == "list_shadow_copies"
        assert r["status"] in ("success", "error")

    def test_drivers(self):
        r = audit_drivers(None, 10)
        _shape(r, "audit_drivers")
        if r["status"] == "success":
            assert len(r["drivers"]) <= 10

    def test_drivers_filter(self):
        r = audit_drivers("Display", 10)
        _shape(r, "audit_drivers")

    def test_reliability(self):
        r = get_reliability_history(1, 10)
        _shape(r, "get_reliability_history")

    def test_winget(self):
        r = winget_outdated(5)
        assert r["operation"] == "winget_outdated"
        assert r["status"] in ("success", "error")

    def test_path_dross(self):
        r = audit_path_dross()
        assert r["status"] == "success"
        assert "missing" in r and "duplicates" in r and "entries" in r
