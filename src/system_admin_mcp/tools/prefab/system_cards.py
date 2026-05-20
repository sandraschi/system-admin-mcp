"""
Prefab UI Tools - System Admin MCP SOTA v0.4.0
Rich in-chat cards for system administration data.
Core dependency: prefab-ui>=0.14.0
Disable: SYSADMIN_PREFAB_APPS=0
"""

from typing import Any

import psutil
from fastmcp import Context
from fastmcp.tools import ToolResult
from prefab_ui.app import PrefabApp
from prefab_ui.components import Card, CardContent, CardHeader, CardTitle, Text

from system_admin_mcp.tools.implementations import health_check


async def system_health_card(ctx: Context | None = None) -> Any:
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

    mem_used_gb = mem.used / (1024**3)
    mem_total_gb = mem.total / (1024**3)
    disk_used_gb = disk.used / (1024**3)
    disk_total_gb = disk.total / (1024**3)

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
    ctx: Context | None = None,
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


async def list_services_card(
    filter_status: str | None = None,
    filter_name: str | None = None,
    ctx: Context | None = None,
) -> Any:
    """Display a rich card of Windows services with filtering.

    ## Return Format
    ToolResult with PrefabApp Card.

    ## Examples
        list_services_card(filter_status="running")
        list_services_card(filter_name="sql")
    """
    if ctx:
        ctx.info("Building services card...")

    from system_admin_mcp.tools.services_and_tasks import list_services

    result = list_services(filter_status, filter_name)
    services = result.get("services", []) if result.get("status") == "success" else []

    summary = f"Windows Services: {len(services)} found"
    if filter_status:
        summary += f" (status={filter_status})"
    if filter_name:
        summary += f" (filter={filter_name})"

    with Card(css_class="max-w-2xl") as view:
        with CardHeader():
            CardTitle(f"Windows Services ({len(services)})")
        with CardContent():
            for svc in services[:30]:
                name = svc.get("name", "?")
                display = svc.get("display_name", "")
                status = svc.get("status", "?")
                startup = svc.get("startup_type", "?")
                status_icon = "RUN" if status == "Running" else "STOP"
                Text(f"[{status_icon}] {name:<32} {status:<12} {startup:<10}  {display}")

    return ToolResult(
        content=summary,
        structured_content=PrefabApp(view=view, title="Windows Services"),
    )


async def volume_status_card(
    ctx: Context | None = None,
) -> Any:
    """Display a rich card of all volumes with disk usage.

    ## Return Format
    ToolResult with PrefabApp Card.

    ## Examples
        volume_status_card()
    """
    if ctx:
        ctx.info("Building volume status card...")

    volumes = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            volumes.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": usage.total / (1024**3),
                    "used_gb": usage.used / (1024**3),
                    "free_gb": usage.free / (1024**3),
                    "percent": usage.percent,
                }
            )
        except PermissionError:
            volumes.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": 0,
                    "used_gb": 0,
                    "free_gb": 0,
                    "percent": 0,
                }
            )

    summary = f"Volumes: {len(volumes)} found"
    with Card(css_class="max-w-2xl") as view:
        with CardHeader():
            CardTitle(f"Volume Status ({len(volumes)} volumes)")
        with CardContent():
            for vol in volumes:
                device = vol["device"]
                mount = vol["mountpoint"]
                fstype = vol["fstype"]
                pct = vol["percent"]
                free = vol["free_gb"]
                total = vol["total_gb"]
                bar = "=" * int(pct / 5) + " " * (20 - int(pct / 5))
                Text(f"{device} ({mount}) [{fstype}]")
                Text(f"  [{bar}] {pct:.0f}%  {free:.1f} GB free / {total:.1f} GB total")

    return ToolResult(
        content=summary,
        structured_content=PrefabApp(view=view, title="Volume Status"),
    )
