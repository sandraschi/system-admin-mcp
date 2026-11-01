"""RAM weeder rules on synthetic snapshots (no real processes are touched)."""

from __future__ import annotations

from system_admin_mcp.tools.ram_weeder import (
    Proc,
    Snapshot,
    WeederConfig,
    classify,
    kill,
    pressure,
)

NOW = 1_800_000_000.0
H = 3600


def proc(pid, name, ppid=1, age=10 * H, cmd=(), rss_mb=100, cpu=0.0, user="me", window=None, title="", ports=()):
    return Proc(
        pid=pid,
        name=name,
        ppid=ppid,
        create_time=NOW - age,
        cmdline=list(cmd),
        rss=int(rss_mb * 1024 * 1024),
        cpu_percent=cpu,
        username=user,
        has_window=window,
        window_title=title,
        listen_ports=list(ports),
    )


def snap(*procs, mem=50.0, ports=(), self_chain=(999,)):
    table = {p.pid: p for p in procs}
    # pid 1: an always-alive, very old ancestor ("explorer")
    table.setdefault(1, proc(1, "explorer.exe", ppid=0, age=1000 * H))
    for p in table.values():
        parent = table.get(p.ppid)
        if parent:
            parent.children.append(p.pid)
    return Snapshot(
        taken_at=NOW,
        procs=table,
        self_chain=set(self_chain),
        current_user="me",
        memory_percent=mem,
        memory_available=8 * 1024**3,
        memory_total=64 * 1024**3,
        registered_ports=set(ports),
    )


def rules(cands):
    return {c.pid: c.rule for c in cands}


def test_orphan_headless_godot_is_auto_eligible():
    s = snap(proc(10, "godot.exe", ppid=4242, age=2 * H, cmd=["godot", "--path", "x", "--headless"]))
    (c,) = classify(s)
    assert c.rule == "orphan_engine"
    assert c.auto_ok is True
    assert "gone" in c.parent


def test_headless_godot_with_live_parent_is_left_alone():
    s = snap(
        proc(20, "python.exe", ppid=1, age=3 * H, ports=[10993]),
        proc(21, "godot.exe", ppid=20, age=2 * H, cmd=["godot", "--headless"]),
        ports=[10993],
    )
    assert 21 not in rules(classify(s))


def test_young_orphan_engine_waits_for_min_age():
    s = snap(proc(10, "godot.exe", ppid=4242, age=60, cmd=["godot", "--headless"]))
    assert classify(s) == []


def test_reused_parent_pid_counts_as_gone():
    # parent pid exists but is younger than the child: pid reuse, real parent is gone
    s = snap(
        proc(30, "notepad.exe", ppid=1, age=60),
        proc(31, "godot.exe", ppid=30, age=5 * H, cmd=["godot", "--headless"]),
    )
    assert rules(classify(s))[31] == "orphan_engine"


def test_three_wiztrees_flag_all_but_newest():
    s = snap(
        proc(40, "WizTree64.exe", age=30 * H, rss_mb=4000, window=True),
        proc(41, "WizTree64.exe", age=20 * H, rss_mb=4300, window=True),
        proc(42, "WizTree64.exe", age=1 * H, rss_mb=3000, window=True),
    )
    r = rules(classify(s))
    assert r == {40: "duplicate_app", 41: "duplicate_app"}


def test_two_wiztrees_are_fine():
    s = snap(proc(40, "WizTree64.exe", window=True), proc(41, "WizTree64.exe", window=True))
    assert classify(s) == []


def test_duplicate_godot_game_windows_keep_newest():
    g = ["godot", "--path", "D:\\Dev\\repos\\gamecraft\\depot/games\\sokoban"]
    s = snap(
        proc(50, "godot.exe", ppid=1, age=30 * H, cmd=g, window=True, title="Sokoban"),
        proc(51, "godot.exe", ppid=1, age=29 * H, cmd=g, window=True, title="Sokoban"),
        proc(52, "godot.exe", ppid=1, age=1 * H, cmd=g, window=True, title="Sokoban"),
    )
    r = rules(classify(s))
    assert r == {50: "duplicate_game", 51: "duplicate_game"}


def test_single_orphaned_game_window_is_reported_not_auto():
    s = snap(proc(55, "godot.exe", ppid=777, age=5 * H, cmd=["godot", "--path", "D:\\g\\pong"], window=True))
    (c,) = classify(s)
    assert c.rule == "orphan_game"
    assert c.auto_ok is False


def test_godot_editor_is_never_a_duplicate_game():
    e = ["godot", "--editor", "--path", "D:\\g\\x"]
    s = snap(proc(56, "godot.exe", cmd=e, window=True), proc(57, "godot.exe", cmd=e, window=True))
    assert classify(s) == []


def test_protected_and_system_processes_are_never_candidates():
    s = snap(
        proc(60, "claude.exe", ppid=4242, age=50 * H, cmd=["claude", "--headless"]),
        proc(61, "svchost.exe", ppid=4242, age=50 * H),
        proc(62, "vmmemWSL", ppid=4242, age=50 * H, rss_mb=2000),
        proc(63, "Plex Transcoder.exe", ppid=4242, age=50 * H),
        proc(999, "python.exe", ppid=4242, age=50 * H),  # this server
    )
    assert classify(s) == []


def test_other_users_processes_are_skipped():
    s = snap(proc(70, "godot.exe", ppid=4242, age=5 * H, cmd=["godot", "--headless"], user="someone-else"))
    assert classify(s) == []


def test_extra_protect_via_config_and_env(monkeypatch):
    s = snap(proc(71, "godot.exe", ppid=4242, age=5 * H, cmd=["godot", "--headless"]))
    assert classify(s, WeederConfig(extra_protect=("godot",))) == []
    monkeypatch.setenv("SYSTEMADMIN_WEEDER_PROTECT", "godot")
    assert classify(s) == []


def test_orphan_dev_needs_idle_and_skips_registered_servers():
    s = snap(
        proc(80, "node.exe", ppid=4242, age=3 * H, cpu=0.0),
        proc(81, "node.exe", ppid=4242, age=3 * H, cpu=50.0),
        proc(82, "python.exe", ppid=4242, age=3 * H, cpu=0.0, ports=[10861]),
        ports=[10861],
    )
    r = rules(classify(s))
    assert r == {80: "orphan_dev"}


def test_shell_debris_only_without_children_and_parent():
    s = snap(
        proc(90, "cmd.exe", ppid=4242, age=5 * H),
        proc(91, "conhost.exe", ppid=90, age=5 * H),
        proc(92, "cmd.exe", ppid=4242, age=5 * H),
        proc(93, "python.exe", ppid=92, age=5 * H, cpu=10.0),
    )
    r = rules(classify(s))
    assert r.get(90) is None  # has a live child (its conhost)
    assert r.get(91) is None  # parent alive
    assert r.get(92) is None  # has a live child


def test_unregistered_dev_server_port():
    s = snap(
        proc(100, "bun.exe", ppid=1, age=2 * H, ports=[5173], cpu=5),
        proc(101, "bun.exe", ppid=1, age=2 * H, ports=[11258], cpu=5),
        ports=[11258, 10860],
    )
    assert rules(classify(s)) == {100: "unregistered_port"}


def test_one_candidate_per_process_first_rule_wins():
    s = snap(proc(110, "godot.exe", ppid=4242, age=10 * H, cmd=["godot", "--headless"]))
    (c,) = classify(s)
    assert c.rule == "orphan_engine"  # not also stale_headless


def test_pressure_levels():
    assert pressure(snap(mem=50))["level"] == "ok"
    assert pressure(snap(mem=88))["level"] == "warn"
    assert pressure(snap(mem=95))["level"] == "critical"


def test_kill_requires_confirm():
    r = kill([1234], confirm=False)
    assert r["status"] == "error"
    assert "confirm" in r["error"]


def test_kill_blocked_in_read_only_mode(monkeypatch):
    import pytest

    from system_admin_mcp.mutation_guard import ReadOnlyError

    monkeypatch.setenv("SYSTEMADMIN_READ_ONLY", "1")
    with pytest.raises(ReadOnlyError):
        kill([1234], confirm=True)
