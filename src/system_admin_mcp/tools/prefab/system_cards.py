"""
Prefab UI Tools - System Admin MCP SOTA v0.3.0
Rich in-chat cards for system administration data.
Requires: uv sync --extra apps   (prefab-ui>=0.18.0)
Disable: SYSADMIN_PREFAB_APPS=0
"""

from typing import Any, Optional

import psutil
from fastmcp import Context
from fastmcp.tools import ToolResult
from prefab_ui.app import PrefabApp
from prefab_ui.components import Card, CardContent, CardHeader, CardTitle, Text

from system_admin_mcp.tools.implementations import health_check


async def system_health_card(ctx: Optional[Context] = None) -> Any:
    """
    Display a rich system health card with CPU, memory, disk, and health status.
    Returns a Prefab UI card in capable MCP hosts; plain text fallback otherwise.
    """
    if ctx:
        ctx.info("Building system health card...")

    cpu = psutil.cpu_percent(interval=1, percpu=True)
    cpu_avg = sum(cpu) / len(cpu) if cpu else 0.0
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\") if __import__("sys").platform == "win32" else psutil.disk_usage("/")

    try:
        health = health_check()
        health_status = health.get("status", "unknown") if isinstance(health, dict) else "unknown"
    except Exception:
        health_status = "unavailable"

    mem_used_gb = mem.used / (1024 ** 3)
    mem_total_gb = mem.total / (1024 ** 3)
    disk_used_gb = disk.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)

    summary = (
        f"CPU {cpu_avg:.1f}% | RAM {mem_used_gb:.1f}/{mem_total_gb:.1f}GB ({mem.percent}%) | "
        f"Disk {disk_used_gb:.1f}/{disk_total_gb:.1f}GB | Health: {health_status}"
    )

    with Card(css_class="max-w-lg") as view:
        with CardHeader():
            CardTitle("System Health — Goliath")
        with CardContent():
            Text(f"Health status: {health_status.upper()}")
            Text(f"CPU average: {cpu_avg:.1f}%  ({len(cpu)} cores, max {max(cpu):.1f}%)")
            Text(f"RAM: {mem_used_gb:.1f} GB / {mem_total_gb:.1f} GB  ({mem.percent}% used)")
            Text(f"Disk (C:): {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB  ({disk.percent}% used)")

    return ToolResult(
        content=summary,
        structured_content=PrefabApp(view=view, title="System Health"),
    )


async def top_processes_card(
    sort_by: str = "cpu",
    max_procs: int = 15,
    ctx: Optional[Context] = None,
) -> Any:
    """
    Display a rich card of top processes sorted by CPU or memory.
    Returns a Prefab UI card in capable MCP hosts; plain text fallback otherwise.
    """
    if ctx:
        ctx.info(f"Building top processes card (sort={sort_by}, max={max_procs})")

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "username"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    procs.sort(key=lambda x: x.get(key) or 0, reverse=True)
    procs = procs[:max_procs]

    summary = f"Top {len(procs)} processes by {sort_by}"

    with Card(css_class="max-w-xl") as view:
        with CardHeader():
            CardTitle(f"Top Processes — by {sort_by.upper()}")
        with CardContent():
            for p in procs:
                name = p.get("name") or "?"
                pid = p.get("pid", "?")
                cpu = p.get("cpu_percent") or 0.0
                mem = p.get("memory_percent") or 0.0
                Text(f"[{pid}] {name:<28} CPU:{cpu:5.1f}%  MEM:{mem:4.1f}%")

    return ToolResult(
        content=summary,
        structured_content=PrefabApp(view=view, title="Top Processes"),
    )
