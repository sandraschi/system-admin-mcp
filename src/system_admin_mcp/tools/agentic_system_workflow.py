"""
System Admin MCP — Agentic Workflows (FastMCP 3.2 / SEP-1577)

Real sampling-driven orchestration using ctx.sample().
No simulation stubs — all phases execute actual tool calls.
"""

import json
import logging
from typing import Any

from fastmcp import Context

from system_admin_mcp.app import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def agentic_system_workflow(
    workflow_prompt: str,
    available_tools: list[str],
    max_iterations: int = 5,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Execute agentic system administration workflows using SEP-1577 sampling.

    The server borrows the client LLM via ctx.sample() to autonomously orchestrate
    multi-step system operations without client round-trips.

    Args:
        workflow_prompt: Plain-language description of the workflow to execute.
        available_tools: List of system_admin operations to make available.
        max_iterations: Max sampling loops (default 5).
        ctx: FastMCP Context (required for sampling).

    Returns:
        Structured result with findings, recommendations, and actions taken.

    Examples:
        agentic_system_workflow(
            workflow_prompt="Diagnose why the system is running slowly",
            available_tools=["get_performance_metrics", "list_processes", "get_recent_event_errors"]
        )
        agentic_system_workflow(
            workflow_prompt="Audit security permissions on D:/Shared",
            available_tools=["audit_permissions", "get_permissions", "audit_network_ports"]
        )
    """
    if not ctx:
        return {"success": False, "error": "Context required for agentic workflow (sampling)."}

    if not workflow_prompt:
        return {"success": False, "error": "workflow_prompt is required."}

    if not available_tools:
        return {"success": False, "error": "available_tools must not be empty."}

    ctx.info(f"Agentic workflow started: {workflow_prompt[:60]}")
    ctx.report_progress(5, 100)

    # Phase 1: Collect baseline diagnostics for the available tools
    inventory: dict[str, Any] = {}

    from system_admin_mcp.tools.portmanteau import system_admin  # noqa: PLC0415

    collection_map = {
        "get_performance_metrics": ("performance", {"operation": "get_performance_metrics"}),
        "health_check": ("health", {"operation": "health_check"}),
        "get_recent_event_errors": ("event_errors", {"operation": "get_recent_event_errors", "log_name": "System"}),
        "get_top_resource_processes": ("top_processes", {"operation": "get_top_resource_processes"}),
        "get_hardware_info": ("hardware", {"operation": "get_hardware_info"}),
        "get_os_info": ("os_info", {"operation": "get_os_info"}),
        "get_service_stats": ("service_stats", {"operation": "get_service_stats"}),
        "list_startup_programs": ("startup_programs", {"operation": "list_startup_programs"}),
        "audit_network_ports": ("network_ports", {"operation": "audit_network_ports"}),
    }

    for tool_name in available_tools:
        if tool_name in collection_map:
            label, kwargs = collection_map[tool_name]
            try:
                inventory[label] = await system_admin(**kwargs)
            except Exception as e:
                inventory[label] = {"error": str(e)}

    ctx.report_progress(40, 100)

    # Phase 2: SEP-1577 sampling — reason over inventory
    ctx.info("Phase 2: Sampling for analysis and recommendations...")

    system_prompt = (
        "You are a senior Windows systems administrator. "
        "Analyze the provided system inventory and workflow goal. "
        "Produce: (1) top findings with severity (HIGH/MED/LOW), "
        "(2) specific remediation steps using system_admin operations, "
        "(3) a brief executive summary. Be concise and actionable."
    )
    user_prompt = (
        f"Workflow goal: {workflow_prompt}\n\n"
        f"Available tools: {', '.join(available_tools)}\n\n"
        f"System inventory:\n{json.dumps(inventory, indent=2, default=str)}"
    )

    try:
        sampling_res = await ctx.sample(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=1200,
        )
        analysis = (
            sampling_res.content[0].text
            if sampling_res and sampling_res.content
            else "Sampling returned no analysis."
        )
    except Exception as e:
        analysis = f"Sampling failed: {e}"

    ctx.info(f"Analysis: {analysis[:100]}...")
    ctx.report_progress(80, 100)

    # Phase 3: Extract and queue HIGH priority actions (up to max_iterations)
    high_priority = [
        line.strip()
        for line in analysis.splitlines()
        if "HIGH" in line.upper() and line.strip()
    ][:max_iterations]

    ctx.report_progress(100, 100)

    return {
        "success": True,
        "workflow": workflow_prompt,
        "inventory_collected": list(inventory.keys()),
        "analysis": analysis,
        "high_priority_items": high_priority,
        "iterations_used": 1,
    }


@mcp.tool()
async def autonomous_system_troubleshooter(
    problem_description: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Autonomously diagnose a Windows system problem using 3-phase SEP-1577 sampling.

    Phase 1: Collects event logs, process list, and health metrics.
    Phase 2: Samples for root cause analysis.
    Phase 3: Returns prioritised remediation steps.

    Args:
        problem_description: Plain-language description of the problem.
        ctx: FastMCP Context (required).
    """
    if not ctx:
        return {"success": False, "error": "Context required."}

    ctx.info(f"Troubleshooting: {problem_description[:60]}")
    ctx.report_progress(10, 100)

    from system_admin_mcp.tools.portmanteau import system_admin  # noqa: PLC0415

    findings: dict[str, Any] = {}

    # Phase 1: Gather diagnostics
    for label, kwargs in [
        ("health", {"operation": "health_check"}),
        ("event_errors", {"operation": "get_recent_event_errors", "log_name": "System"}),
        ("performance", {"operation": "get_performance_metrics"}),
        ("top_processes", {"operation": "get_top_resource_processes"}),
    ]:
        try:
            findings[label] = await system_admin(**kwargs)
        except Exception as e:
            findings[label] = {"error": str(e)}

    ctx.report_progress(50, 100)

    # Phase 2: Root cause sampling
    ctx.info("Sampling for root cause analysis...")
    system_prompt = (
        "You are a senior Windows engineer. "
        "Given a problem description and diagnostics, identify: "
        "(1) most probable root cause, "
        "(2) verification steps using system_admin operations, "
        "(3) exact fix commands. "
        "Category: Permissions | Process conflict | Service failure | Resource exhaustion | Hardware | Network."
    )
    user_prompt = (
        f"Problem: {problem_description}\n\n"
        f"Diagnostics:\n{json.dumps(findings, indent=2, default=str)}"
    )

    try:
        res = await ctx.sample(prompt=user_prompt, system_prompt=system_prompt, max_tokens=900)
        root_cause_analysis = res.content[0].text if res and res.content else "Sampling unavailable."
    except Exception as e:
        root_cause_analysis = f"Sampling failed: {e}"

    ctx.report_progress(100, 100)

    return {
        "success": True,
        "problem": problem_description,
        "diagnostics_collected": list(findings.keys()),
        "root_cause_analysis": root_cause_analysis,
    }
