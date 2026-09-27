"""Tests for admin toolbox inventory (no admin needed, live registry reads)."""

from system_admin_mcp.tools.implementations import (
    _ADMIN_TOOLBOX,
    _scan_uninstall,
    audit_admin_toolbox,
)


class TestAdminToolbox:
    def test_catalog_integrity(self):
        ids = [e["id"] for e in _ADMIN_TOOLBOX]
        assert len(ids) == len(set(ids)), "duplicate catalog ids"
        assert len(_ADMIN_TOOLBOX) >= 30
        for entry in _ADMIN_TOOLBOX:
            assert entry["id"] and entry["label"] and entry["category"]
            assert entry["category"] in ("dev", "ai", "tcom", "office", "admin")
            has_detection = entry.get("names") or entry.get("paths") or entry.get("bins")
            assert has_detection, f"{entry['id']} has no detection method"
            assert entry.get("winget") or entry.get("url"), f"{entry['id']} has no install hint"

    def test_scan_uninstall_miss(self):
        assert _scan_uninstall(["definitely-not-installed-xyz-123"]) is None

    def test_audit_shape(self):
        result = audit_admin_toolbox()
        assert result["status"] == "success"
        assert result["operation"] == "audit_admin_toolbox"
        assert result["found_count"] + len(result["missing"]) == result["total_count"]
        assert result["total_count"] == len(_ADMIN_TOOLBOX)
        for item in result["found"] + result["missing"]:
            assert {"id", "label", "category", "found", "running", "install"} <= set(item)

    def test_git_detected_on_fleet_box(self):
        result = audit_admin_toolbox()
        by_id = {i["id"]: i for i in result["found"] + result["missing"]}
        assert by_id["git"]["found"], "git should be detected on a fleet dev box"
