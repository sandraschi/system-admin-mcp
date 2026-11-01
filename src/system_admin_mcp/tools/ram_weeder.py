"""RAM weeder: find leaked processes by rule, report by default, kill on confirmation.

Built 2026-10-31 after the dev box ran at ~95% CPU / 92% RAM with three WizTree
instances (about 12 GB), 21 Godot game windows nobody closed, seven orphaned headless
Godot servers and roughly 150 idle cmd/conhost pairs. Size alone is a bad signal (one
WizTree at 4 GB is fine; three is the leak), so this works by *rules*:

=====================  =========================================================  ======
rule                   what it matches                                            auto
=====================  =========================================================  ======
orphan_engine          headless engine/browser (godot, chrome headless shell...)  yes
                       whose parent is gone, older than ``orphan_min_age_s``
orphan_dev             dev tooling (node, bun, python, uv, pytest, vite, ...)      no
                       whose parent is gone, older than ``orphan_dev_age_s``,
                       near-idle CPU, not serving a port from WEBAPP_PORTS.md
duplicate_app          3+ instances of a single-use app (WizTree, Task Manager,   no
                       ...): every instance except the newest
duplicate_game         2+ windowed Godot games with the same project              no
                       (``--path``): every instance except the newest
orphan_game            windowed Godot game whose launcher is gone, older than    no
                       ``orphan_game_age_s``
stale_headless         any ``--headless`` process older than ``stale_headless_s``  no
shell_debris           cmd/conhost/powershell with no live children and a dead     no
                       parent, older than ``shell_debris_age_s``
unregistered_port      dev server listening on a port not in WEBAPP_PORTS.md       no
=====================  =========================================================  ======

Never touched: Windows system processes, the protect list (Claude, OpenCode, editors,
Plex, Docker, Podman, WSL, ...; extend with ``SYSTEMADMIN_WEEDER_PROTECT``), this
process and its ancestors, processes of other users.

Only ``orphan_engine`` is eligible for the unattended sweep. Every kill re-checks the
process identity (pid + create time) and that it still matches a rule, kills the whole
tree, and is written to the mutation audit log.
"""

from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import psutil

from system_admin_mcp.mutation_guard import audit_mutation, require_mutable

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SYSTEM_NAMES = frozenset(
    n.lower()
    for n in (
        "System",
        "System Idle Process",
        "Registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "lsaiso.exe",
        "svchost.exe",
        "winlogon.exe",
        "explorer.exe",
        "dwm.exe",
        "MsMpEng.exe",
        "NisSrv.exe",
        "Memory Compression",
        "fontdrvhost.exe",
        "sihost.exe",
        "ctfmon.exe",
        "RuntimeBroker.exe",
        "taskhostw.exe",
        "spoolsv.exe",
        "SearchIndexer.exe",
        "audiodg.exe",
        "WmiPrvSE.exe",
        "dllhost.exe",
        "SecurityHealthService.exe",
        "StartMenuExperienceHost.exe",
        "ShellExperienceHost.exe",
        "TextInputHost.exe",
        "SearchHost.exe",
        "LsaIso.exe",
        "smartscreen.exe",
    )
)

DEFAULT_PROTECT = (
    "claude",
    "Claude",
    "opencode",
    "OpenCode",
    "Cursor",
    "Windsurf",
    "Code",
    "zed",
    "Plex",
    "docker",
    "com.docker",
    "Docker Desktop",
    "Podman",
    "podman",
    "vmmem",
    "vmmemWSL",
    "wsl",
    "wslservice",
    "wslhost",
    "RustDesk",
    "rustdesk",
    "tailscale",
    "tailscaled",
    "Ollama",
    "ollama",
    "LM Studio",
    "lms",
    "OneDrive",
    "firefox",
    "chrome",
    "msedge",
)

ENGINE_NAMES = ("godot", "chrome-headless-shell", "headless_shell", "blender", "unity")
DEV_NAMES = ("node", "bun", "python", "pythonw", "uv", "uvx", "pytest", "vite", "deno", "cargo", "rustc")
SHELL_NAMES = ("cmd", "conhost", "powershell", "pwsh")
SINGLE_USE_APPS = ("WizTree64", "WizTree", "Taskmgr", "procexp64", "procexp", "WinDirStat", "SpaceSniffer", "TreeSize")
DEV_SERVER_NAMES = ("node", "bun", "python", "pythonw", "uvicorn", "deno")

DEFAULT_PORTS_FILE = Path(r"D:\Dev\repos\mcp-central-docs\operations\WEBAPP_PORTS.md")


@dataclass
class WeederConfig:
    """Thresholds; every field can be overridden per call."""

    orphan_min_age_s: int = 30 * 60
    orphan_dev_age_s: int = 60 * 60
    stale_headless_s: int = 6 * 60 * 60
    shell_debris_age_s: int = 60 * 60
    idle_cpu_percent: float = 2.0  # percent of one core
    orphan_game_age_s: int = 2 * 60 * 60
    duplicate_threshold: int = 3
    pressure_warn_percent: float = 85.0
    pressure_critical_percent: float = 93.0
    extra_protect: tuple[str, ...] = ()
    ports_file: Path | None = None


def _stem(name: str) -> str:
    n = name.lower()
    return n[:-4] if n.endswith(".exe") else n


def _matches(stem: str, names: Iterable[str]) -> bool:
    return any(stem == _stem(n) or stem.startswith(_stem(n) + "_") or stem.startswith(_stem(n) + ".") for n in names)


def protect_list(cfg: WeederConfig) -> tuple[str, ...]:
    env = tuple(x.strip() for x in os.getenv("SYSTEMADMIN_WEEDER_PROTECT", "").split(",") if x.strip())
    return DEFAULT_PROTECT + cfg.extra_protect + env


# ---------------------------------------------------------------------------
# Snapshot (pure data, so the rules are testable without psutil)
# ---------------------------------------------------------------------------


@dataclass
class Proc:
    pid: int
    name: str
    ppid: int
    create_time: float
    cmdline: list[str]
    rss: int
    cpu_percent: float
    username: str | None
    has_window: bool | None = None
    window_title: str = ""
    listen_ports: list[int] = field(default_factory=list)
    children: list[int] = field(default_factory=list)

    @property
    def stem(self) -> str:
        return _stem(self.name)

    @property
    def cmd(self) -> str:
        return " ".join(self.cmdline)


@dataclass
class Snapshot:
    taken_at: float
    procs: dict[int, Proc]
    self_chain: set[int]
    current_user: str | None
    memory_percent: float
    memory_available: int
    memory_total: int
    registered_ports: set[int]


@dataclass
class Candidate:
    pid: int
    name: str
    create_time: float
    rule: str
    reason: str
    auto_ok: bool
    age_s: int
    rss_mb: float
    cpu_percent: float
    parent: str
    window_title: str
    cmdline: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parent_alive(p: Proc, snap: Snapshot) -> bool:
    parent = snap.procs.get(p.ppid)
    # A pid that was reused by a younger process is not the real parent.
    return parent is not None and parent.create_time <= p.create_time + 1.0


def _parent_label(p: Proc, snap: Snapshot) -> str:
    parent = snap.procs.get(p.ppid)
    if parent is None or parent.create_time > p.create_time + 1.0:
        return f"{p.ppid} (gone)"
    return f"{p.ppid} {parent.name}"


def _is_protected(p: Proc, snap: Snapshot, cfg: WeederConfig) -> bool:
    if p.pid in snap.self_chain or p.pid <= 4:
        return True
    if p.name.lower() in SYSTEM_NAMES:
        return True
    if snap.current_user and p.username and p.username.lower() != snap.current_user.lower():
        return True
    return _matches(p.stem, protect_list(cfg))


def _godot_project(p: Proc) -> str | None:
    args = p.cmdline
    for i, a in enumerate(args):
        if a == "--path" and i + 1 < len(args):
            return args[i + 1].replace("/", "\\").lower().rstrip("\\")
    return None


def classify(snap: Snapshot, cfg: WeederConfig | None = None) -> list[Candidate]:
    """Apply every rule; one candidate per process (first matching rule wins)."""
    cfg = cfg or WeederConfig()
    now = snap.taken_at
    out: dict[int, Candidate] = {}

    def add(p: Proc, rule: str, reason: str, auto_ok: bool = False) -> None:
        if p.pid in out or _is_protected(p, snap, cfg):
            return
        out[p.pid] = Candidate(
            pid=p.pid,
            name=p.name,
            create_time=p.create_time,
            rule=rule,
            reason=reason,
            auto_ok=auto_ok,
            age_s=int(now - p.create_time),
            rss_mb=round(p.rss / (1024 * 1024), 1),
            cpu_percent=round(p.cpu_percent, 1),
            parent=_parent_label(p, snap),
            window_title=p.window_title,
            cmdline=p.cmd[:400],
        )

    procs = list(snap.procs.values())
    for p in procs:
        age = now - p.create_time
        headless = "--headless" in p.cmdline or "--headless=new" in p.cmd
        orphan = not _parent_alive(p, snap)
        if _matches(p.stem, ENGINE_NAMES) and headless and orphan and age >= cfg.orphan_min_age_s:
            add(p, "orphan_engine", f"headless {p.stem} whose launcher (pid {p.ppid}) is gone", auto_ok=True)

    for p in procs:
        age = now - p.create_time
        serves_registered_port = bool(p.listen_ports) and all(port in snap.registered_ports for port in p.listen_ports)
        if (
            _matches(p.stem, DEV_NAMES)
            and not serves_registered_port
            and not _parent_alive(p, snap)
            and age >= cfg.orphan_dev_age_s
            and p.cpu_percent <= cfg.idle_cpu_percent
            and not p.has_window
        ):
            add(p, "orphan_dev", f"idle {p.stem} whose parent (pid {p.ppid}) is gone")

    by_stem: dict[str, list[Proc]] = defaultdict(list)
    for p in procs:
        if _matches(p.stem, SINGLE_USE_APPS):
            by_stem[p.stem].append(p)
    for stem, group in by_stem.items():
        if len(group) >= cfg.duplicate_threshold:
            group.sort(key=lambda x: x.create_time)
            total_mb = sum(x.rss for x in group) / (1024 * 1024)
            for p in group[:-1]:
                add(
                    p,
                    "duplicate_app",
                    f"{len(group)} instances of {stem} ({total_mb:,.0f} MB together); keeping the newest",
                )

    games: dict[str, list[Proc]] = defaultdict(list)
    for p in procs:
        if (
            _matches(p.stem, ("godot",))
            and "--headless" not in p.cmdline
            and "--editor" not in p.cmdline
            and "-e" not in p.cmdline
        ):
            proj = _godot_project(p)
            if proj:
                games[proj].append(p)
    for proj, group in games.items():
        if len(group) >= 2:
            group.sort(key=lambda x: x.create_time)
            for p in group[:-1]:
                add(
                    p,
                    "duplicate_game",
                    f"{len(group)} windows of the same Godot project {Path(proj).name}; keeping the newest",
                )

    for p in procs:
        if (
            _matches(p.stem, ("godot",))
            and "--headless" not in p.cmdline
            and _godot_project(p)
            and not _parent_alive(p, snap)
            and now - p.create_time >= cfg.orphan_game_age_s
        ):
            add(p, "orphan_game", f"Godot game window open {int((now - p.create_time) / 3600)} h, its launcher is gone")

    for p in procs:
        if "--headless" in p.cmdline and now - p.create_time >= cfg.stale_headless_s:
            add(p, "stale_headless", f"headless process running for {int((now - p.create_time) / 3600)} h")

    for p in procs:
        if (
            _matches(p.stem, SHELL_NAMES)
            and not any(c in snap.procs for c in p.children)
            and not _parent_alive(p, snap)
            and now - p.create_time >= cfg.shell_debris_age_s
            and not p.has_window
            and p.cpu_percent <= cfg.idle_cpu_percent
        ):
            add(p, "shell_debris", f"idle {p.stem} with no children and no parent")

    if snap.registered_ports:
        for p in procs:
            if _matches(p.stem, DEV_SERVER_NAMES) and p.listen_ports:
                unknown = [port for port in p.listen_ports if port not in snap.registered_ports and port >= 1024]
                if unknown and len(unknown) == len(p.listen_ports):
                    add(p, "unregistered_port", f"dev server on unregistered port(s) {unknown}")

    return sorted(out.values(), key=lambda c: (-c.rss_mb, c.pid))


def pressure(snap: Snapshot, cfg: WeederConfig | None = None) -> dict[str, Any]:
    cfg = cfg or WeederConfig()
    level = "ok"
    if snap.memory_percent >= cfg.pressure_critical_percent:
        level = "critical"
    elif snap.memory_percent >= cfg.pressure_warn_percent:
        level = "warn"
    return {
        "level": level,
        "memory_percent": round(snap.memory_percent, 1),
        "available_gb": round(snap.memory_available / 1024**3, 1),
        "total_gb": round(snap.memory_total / 1024**3, 1),
        "warn_at": cfg.pressure_warn_percent,
        "critical_at": cfg.pressure_critical_percent,
    }


# ---------------------------------------------------------------------------
# Live snapshot
# ---------------------------------------------------------------------------


def registered_ports(path: Path | None = None) -> set[int]:
    path = path or Path(os.getenv("SYSTEMADMIN_WEEDER_PORTS_FILE", str(DEFAULT_PORTS_FILE)))
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    return {int(m) for m in re.findall(r"\b(\d{4,5})\b", text) if 1024 <= int(m) <= 65535}


def _windows_by_pid() -> dict[int, str]:
    """Visible top-level window titles by pid (Windows only; empty elsewhere)."""
    try:
        import win32gui  # type: ignore[import-not-found]
        import win32process  # type: ignore[import-not-found]
    except Exception:
        return {}
    found: dict[int, str] = {}

    def cb(hwnd: int, _: Any) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                found.setdefault(pid, title)
        return True

    try:
        win32gui.EnumWindows(cb, None)
    except Exception:
        return {}
    return found


def take_snapshot(cfg: WeederConfig | None = None, cpu_sample_s: float = 0.5) -> Snapshot:
    cfg = cfg or WeederConfig()
    windows = _windows_by_pid()
    handles: list[psutil.Process] = []
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(None)
            handles.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    time.sleep(cpu_sample_s)
    procs: dict[int, Proc] = {}
    for proc in handles:
        try:
            with proc.oneshot():
                try:
                    cmdline = proc.cmdline()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    cmdline = []
                try:
                    user = proc.username()
                except psutil.AccessDenied:
                    user = None
                procs[proc.pid] = Proc(
                    pid=proc.pid,
                    name=proc.name(),
                    ppid=proc.ppid(),
                    create_time=proc.create_time(),
                    cmdline=cmdline,
                    rss=proc.memory_info().rss,
                    cpu_percent=proc.cpu_percent(None),
                    username=user,
                    has_window=(proc.pid in windows) if windows else None,
                    window_title=windows.get(proc.pid, ""),
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    for p in procs.values():
        parent = procs.get(p.ppid)
        if parent is not None:
            parent.children.append(p.pid)
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.status == psutil.CONN_LISTEN and conn.pid in procs and conn.laddr:
                procs[conn.pid].listen_ports.append(conn.laddr.port)
    except (psutil.AccessDenied, OSError):
        pass
    chain: set[int] = set()
    try:
        me = psutil.Process()
        chain.add(me.pid)
        chain.update(a.pid for a in me.parents())
        me_user = me.username()
    except Exception:
        me_user = None
    vm = psutil.virtual_memory()
    return Snapshot(
        taken_at=time.time(),
        procs=procs,
        self_chain=chain,
        current_user=me_user,
        memory_percent=vm.percent,
        memory_available=vm.available,
        memory_total=vm.total,
        registered_ports=registered_ports(cfg.ports_file),
    )


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def _summary(cands: list[Candidate]) -> dict[str, Any]:
    by_rule: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "rss_mb": 0.0})
    for c in cands:
        by_rule[c.rule]["count"] += 1
        by_rule[c.rule]["rss_mb"] += c.rss_mb
    return {
        "candidates": len(cands),
        "reclaimable_mb": round(sum(c.rss_mb for c in cands), 1),
        "auto_eligible": sum(1 for c in cands if c.auto_ok),
        "by_rule": {k: {"count": int(v["count"]), "rss_mb": round(v["rss_mb"], 1)} for k, v in by_rule.items()},
    }


def scan(cfg: WeederConfig | None = None) -> dict[str, Any]:
    """Read-only: memory pressure plus every candidate with its reason."""
    cfg = cfg or WeederConfig()
    snap = take_snapshot(cfg)
    cands = classify(snap, cfg)
    return {
        "status": "success",
        "operation": "weed_scan",
        "pressure": pressure(snap, cfg),
        "summary": _summary(cands),
        "candidates": [c.to_dict() for c in cands],
        "processes_seen": len(snap.procs),
        "registered_ports_loaded": len(snap.registered_ports),
    }


def _kill_tree(pid: int, grace_s: float = 5.0) -> list[int]:
    try:
        root = psutil.Process(pid)
        tree = [*root.children(recursive=True), root]
    except psutil.NoSuchProcess:
        return []
    for p in tree:
        try:
            p.terminate()
        except psutil.Error:
            pass
    _, alive = psutil.wait_procs(tree, timeout=grace_s)
    for p in alive:
        try:
            p.kill()
        except psutil.Error:
            pass
    psutil.wait_procs(alive, timeout=grace_s)
    return [p.pid for p in tree]


def kill(
    targets: list[dict[str, Any]] | list[int],
    confirm: bool = False,
    auto_only: bool = False,
    cfg: WeederConfig | None = None,
) -> dict[str, Any]:
    """Kill confirmed candidates. Each target is re-checked against a fresh scan:
    same pid, same create time, still matching a rule (and auto-eligible when
    ``auto_only``). Anything else is skipped with the reason."""
    if not confirm:
        return {
            "status": "error",
            "operation": "weed_kill",
            "error": "confirm=True is required; run weed_scan first and pass the pids you approve",
        }
    require_mutable("weed_kill")
    cfg = cfg or WeederConfig()
    snap = take_snapshot(cfg, cpu_sample_s=0.3)
    current = {c.pid: c for c in classify(snap, cfg)}
    killed, skipped = [], []
    for t in targets:
        pid = int(t["pid"]) if isinstance(t, dict) else int(t)
        want_ct = float(t["create_time"]) if isinstance(t, dict) and "create_time" in t else None
        cand = current.get(pid)
        if cand is None:
            skipped.append({"pid": pid, "reason": "no longer a candidate (gone, protected, or rule no longer matches)"})
            continue
        if want_ct is not None and abs(cand.create_time - want_ct) > 1.0:
            skipped.append({"pid": pid, "reason": "pid was reused by a different process"})
            continue
        if auto_only and not cand.auto_ok:
            skipped.append({"pid": pid, "reason": f"rule {cand.rule} is not auto-eligible"})
            continue
        pids = _kill_tree(pid)
        record = {"pid": pid, "name": cand.name, "rule": cand.rule, "rss_mb": cand.rss_mb, "tree": pids}
        audit_mutation("weed_kill", record)
        killed.append(record)
    return {
        "status": "success",
        "operation": "weed_kill",
        "killed": killed,
        "skipped": skipped,
        "freed_mb_estimate": round(sum(k["rss_mb"] for k in killed), 1),
    }


def sweep(apply: bool = False, cfg: WeederConfig | None = None) -> dict[str, Any]:
    """Unattended pass: only ``orphan_engine`` candidates. Dry run unless ``apply``."""
    cfg = cfg or WeederConfig()
    snap = take_snapshot(cfg)
    cands = [c for c in classify(snap, cfg) if c.auto_ok]
    result: dict[str, Any] = {
        "status": "success",
        "operation": "weed_sweep",
        "applied": apply,
        "pressure": pressure(snap, cfg),
        "eligible": [c.to_dict() for c in cands],
    }
    if apply and cands:
        result["kill"] = kill(
            [{"pid": c.pid, "create_time": c.create_time} for c in cands], confirm=True, auto_only=True, cfg=cfg
        )
    if apply:
        audit_mutation("weed_sweep", {"eligible": len(cands), "memory_percent": snap.memory_percent})
    return result
