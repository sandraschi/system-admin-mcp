"""Tests for crash postmortem implementations (no admin, no real dump needed)."""

import struct

from system_admin_mcp.tools.implementations import (
    _parse_minidump,
    analyze_minidump,
    get_bugcheck_history,
    list_crash_dumps,
    windbg_analyze,
)


def _build_fake_minidump(path) -> None:
    name = "fake.sys"
    raw = name.encode("utf-16-le")

    header = struct.pack("<IIIIIIQ", 0x504D444D, 0, 2, 32, 0, 0, 0)
    dir_entries = struct.pack("<III", 6, 172, 56) + struct.pack("<III", 4, 112, 228)

    record = struct.pack("<IIQQII", 0xEF, 0, 0, 0x12000, 1, 0) + struct.pack("<15Q", 5, *((0,) * 14))
    exception = struct.pack("<II", 7, 0) + record + struct.pack("<II", 0, 0) + struct.pack("<I", 0)

    module = (
        struct.pack("<QIIII", 0x10000, 0x5000, 0, 0, 340)
        + bytes(52)
        + struct.pack("<II", 0, 0)
        + struct.pack("<II", 0, 0)
        + struct.pack("<QQ", 0, 0)
    )
    module_list = struct.pack("<I", 1) + module
    name_blob = struct.pack("<I", len(raw)) + raw

    blob = header + dir_entries
    assert len(blob) == 56
    blob += exception
    assert len(blob) == 228, len(blob)
    blob += module_list
    assert len(blob) == 340, len(blob)
    blob += name_blob
    path.write_bytes(blob)


class TestCrashPostmortem:
    def test_list_crash_dumps_shape(self):
        result = list_crash_dumps()
        assert result["status"] == "success"
        assert result["operation"] == "list_crash_dumps"
        for key in ("minidumps", "live_kernel", "wer", "crash_control", "interpretation"):
            assert key in result

    def test_get_bugcheck_history_admin_gate(self):
        result = get_bugcheck_history(1, 5)
        assert result["operation"] == "get_bugcheck_history"
        assert result["status"] in ("success", "error")

    def test_parse_synthetic_dump(self, tmp_path):
        dump = tmp_path / "synthetic.dmp"
        _build_fake_minidump(dump)
        parsed = _parse_minidump(dump.read_bytes())
        assert parsed["exception_code"] == "0xEF"
        assert parsed["exception_name"] == "CRITICAL_PROCESS_DIED"
        assert parsed["faulting_module"] == "fake.sys"
        assert parsed["exception_params"] == ["0x5"]

    def test_analyze_minidump_synthetic(self, tmp_path):
        dump = tmp_path / "synthetic.dmp"
        _build_fake_minidump(dump)
        result = analyze_minidump(str(dump))
        assert result["status"] == "success"
        assert result["faulting_module"] == "fake.sys"

    def test_analyze_minidump_missing(self, tmp_path):
        result = analyze_minidump(str(tmp_path / "nope.dmp"))
        assert result["status"] == "error"

    def test_analyze_minidump_not_a_dump(self, tmp_path):
        bad = tmp_path / "bad.dmp"
        bad.write_bytes(b"definitely not a minidump file...........")
        result = analyze_minidump(str(bad))
        assert result["status"] == "error"
        assert "MDMP" in result["error"]

    def test_windbg_missing_dump(self, tmp_path):
        result = windbg_analyze(str(tmp_path / "nope.dmp"))
        assert result["status"] == "error"
        assert result["operation"] == "windbg_analyze"
