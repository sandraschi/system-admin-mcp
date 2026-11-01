"""MCP surface for the RAM weeder (logic in ram_weeder.py)."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, Literal

from mcp.types import ToolAnnotations
from pydantic import Field

from system_admin_mcp.app import mcp
from system_admin_mcp.tools import ram_weeder

_DESTRUCTIVE = ToolAnnotations(destructiveHint=True)


@mcp.tool(annotations=_DESTRUCTIVE)
async def ram_weeder_tool(
    operation: Annotated[
        Literal["scan", "kill", "sweep"],
        Field(description="scan = report only; kill = kill approved pids; sweep = orphaned headless engines only"),
    ],
    pids: Annotated[
        list[int] | None, Field(description="kill: pids from a previous scan that the user approved")
    ] = None,
    confirm: Annotated[bool, Field(description="kill: must be True; there is no implicit kill")] = False,
    apply: Annotated[bool, Field(description="sweep: False (default) only lists what it would kill")] = False,
    orphan_min_age_min: Annotated[int, Field(description="Age before an orphaned headless engine counts", ge=1)] = 30,
    duplicate_threshold: Annotated[
        int, Field(description="Instances of a single-use app that count as a leak", ge=2)
    ] = 3,
) -> dict[str, Any]:
    """Find and remove leaked processes (orphaned test engines, duplicate apps, shell debris).

    Works by rules, not by size: orphan_engine, orphan_dev, duplicate_app, duplicate_game,
    orphan_game, stale_headless, shell_debris, unregistered_port. System processes, the
    protect list (Claude, OpenCode, editors, Plex, Docker, WSL, browsers, ...) and this
    server's own process chain are never candidates. Also reports memory pressure
    (warn 85%, critical 93%).

    Always scan first and show the user the candidates. kill re-checks every pid
    (identity and rule) before killing its whole tree and logs it to the mutation audit
    log. Only orphan_engine is eligible for sweep.

    ## Return Format
    scan: {"status", "pressure": {...}, "summary": {...}, "candidates": [{pid, name, rule, reason, auto_ok, age_s, rss_mb, ...}]}
    kill: {"status", "killed": [...], "skipped": [{pid, reason}], "freed_mb_estimate"}
    sweep: {"status", "applied", "pressure", "eligible": [...], "kill"?: {...}}

    ## Examples
    ram_weeder_tool(operation="scan")
    ram_weeder_tool(operation="kill", pids=[1234, 5678], confirm=True)
    ram_weeder_tool(operation="sweep", apply=True)
    """
    cfg = ram_weeder.WeederConfig(
        orphan_min_age_s=orphan_min_age_min * 60,
        duplicate_threshold=duplicate_threshold,
    )
    if operation == "scan":
        return await asyncio.to_thread(ram_weeder.scan, cfg)
    if operation == "kill":
        return await asyncio.to_thread(ram_weeder.kill, list(pids or []), confirm, False, cfg)
    return await asyncio.to_thread(ram_weeder.sweep, apply, cfg)
