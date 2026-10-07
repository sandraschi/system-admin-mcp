import asyncio
import logging
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any

import psutil
from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from system_admin_mcp.app import mcp

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("system_admin_mcp")

# Import tools to trigger @mcp.tool() decorators
# Using relative imports to ensure we use the same package context as server.py
try:
    from system_admin_mcp.tools import (
        agentic_system_workflow,  # noqa: F401
        portmanteau,  # noqa: F401
        services_and_tasks,  # noqa: F401
        system_ops,
    )

    logger.info("Tool modules imported successfully via relative paths")
except Exception as e:
    logger.warning(f"Error registering tools via relative imports: {e}")
    # Fallback to absolute if relative fails (though uvicorn should handle this)
    try:
        from system_admin_mcp.tools import system_ops  # noqa: F401

        logger.info("Tool modules imported via absolute paths")
    except Exception as e2:
        logger.warning(f"Absolute import fallback also failed: {e2}")


# Verify registration (FastMCP 3.1+ internal check)
def _get_registered_tools():
    try:
        # FastMCP 3.1+ uses local_provider._components (flat dict of prefixed keys)
        if hasattr(mcp, "local_provider") and hasattr(mcp.local_provider, "_components"):
            components = mcp.local_provider._components
            return [k.split(":")[1].rstrip("@") for k in components.keys() if k.startswith("tool:")]
        # Fallback to legacy _tools for older versions
        return list(getattr(mcp, "_tools", {}).keys())
    except Exception as e:
        logger.warning(f"Error in _get_registered_tools: {e}")
        return []


registered_tools = _get_registered_tools()
logger.info(f"Initialized with {len(registered_tools)} registered tools: {registered_tools}")

# Create FastAPI app
app = FastAPI(
    title="System Admin MCP Server",
    description="Elevated system operations and monitoring API",
    version="0.1.0",
)

# Add CORS middleware - fleet standard: explicit origins + unconditional regex
# covering Tauri webview, Tailscale, LAN IPs, Tailscale CGNAT, localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10860",
        "http://127.0.0.1:10860",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Start time for uptime calculation
START_TIME = time.time()


registered_tools = _get_registered_tools()
logger.info(f"FastAPI Backend: Initialized with {len(registered_tools)} registered tools: {registered_tools}")


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Basic health check."""
    return {
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": "system-admin-mcp",
    }


@app.get("/api/status")
async def system_status() -> dict[str, Any]:
    """Detailed system and service status."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "service": "system-admin-mcp",
        "version": "0.1.0",
        "status": "healthy",
        "uptime": int(time.time() - START_TIME),
        "system": {
            "cpu_usage_percent": round(min(cpu_percent, 99.9), 1),
            "cpu_count": psutil.cpu_count(),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/api/tools")
async def list_mcp_tools() -> list[dict[str, Any]]:
    """List available MCP tools for the frontend analyzer."""
    tools_list = []
    try:
        # FastMCP 3.1+ uses list_tools() coroutine
        tools = await mcp.list_tools()
        for tool in tools:
            try:
                # Get schema if available
                schema = {}
                if hasattr(tool, "parameters"):
                    params = tool.parameters
                    if hasattr(params, "model_json_schema"):
                        schema = params.model_json_schema()  # type: ignore[reportAttributeAccessIssue]
                    elif hasattr(params, "schema"):
                        schema = params.schema()  # type: ignore[reportAttributeAccessIssue]

                tools_list.append(
                    {
                        "name": tool.name,
                        "description": getattr(tool, "description", "") or "",
                        "parameters": schema,
                    }
                )
            except Exception as e:
                logger.warning(f"Error processing tool '{getattr(tool, 'name', 'unknown')}': {e}")
                tools_list.append(
                    {
                        "name": getattr(tool, "name", "unknown"),
                        "description": f"Error retrieving tool metadata: {e}",
                        "parameters": {},
                    }
                )
    except Exception as e:
        logger.error(f"Global error listing tools: {e}")

    return tools_list


@app.post("/api/tools/call")
async def call_mcp_tool(request: Request) -> dict[str, Any]:
    """Execute an MCP tool and return the result."""
    tool_name = ""
    try:
        body = await request.json()
        tool_name = body.get("name") or ""
        arguments = body.get("arguments", {})

        if not tool_name:
            return {"status": "error", "message": "Tool name required"}

        # Use _run_tool helper which handles the registration lookup and async execution
        result = await _run_tool(tool_name, **arguments)

        # Handle non-serializable results
        try:
            import json

            json.dumps(result)
        except (TypeError, OverflowError):
            result = str(result)

        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error calling tool {tool_name or 'unknown'}: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/metrics")
async def get_metrics() -> dict[str, Any]:
    """Extended system metrics for monitoring."""
    net_io = psutil.net_io_counters()
    return {
        "cpu_count": psutil.cpu_count(),
        "load_average": getattr(os, "getloadavg", lambda: [0, 0, 0])(),
        "network": {"bytes_sent": net_io.bytes_sent, "bytes_recv": net_io.bytes_recv},
    }


@app.get("/api/llm/discover")
async def llm_discover() -> dict[str, Any]:
    """Probe local LLM providers (Ollama, LM Studio) and list available models."""
    import httpx

    async def probe(name: str, base: str, url: str, container: str, field: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    items = r.json().get(container) or []
                    models = [m.get(field) for m in items if m.get(field)]
                    return {"name": name, "base": base, "detected": True, "models": models}
        except Exception:
            logger.debug("LLM provider probe failed for %s; marking undetected", name, exc_info=True)
        return {"name": name, "base": base, "detected": False, "models": []}

    providers = await asyncio.gather(
        probe("ollama", "http://127.0.0.1:11434", "http://127.0.0.1:11434/api/tags", "models", "name"),
        probe("lm_studio", "http://127.0.0.1:1234", "http://127.0.0.1:1234/v1/models", "data", "id"),
    )
    return {"providers": providers, "detected": [p for p in providers if p["detected"]]}


@app.post("/api/chat")
async def chat(
    query: str = Body(..., embed=True),
    model: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Chat with a local LLM (Ollama default, LM Studio fallback)."""
    import httpx

    base = "http://127.0.0.1:1234/v1" if provider == "lm_studio" else "http://127.0.0.1:11434/v1"
    model_name = model or "llama3.2:3b"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{base}/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": query}],
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
            )
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            return {
                "status": "success",
                "response": content,
                "model": model_name,
                "provider": provider or "ollama",
            }
        return {"status": "error", "message": f"LLM HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"LLM unreachable: {e}"}


@app.get("/api/skills")
async def api_skills() -> dict[str, Any]:
    """List available skills from the skills/ directory."""
    skills_dir = Path(__file__).resolve().parent.parent.parent / "skills"
    results = []
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            sk = d / "SKILL.md"
            if d.is_dir() and sk.exists():
                results.append({"name": d.name, "description": sk.read_text(encoding="utf-8")[:200]})
    return {"skills": results}


@app.get("/api/v1/diagnostics")
async def api_diagnostics() -> dict[str, Any]:
    """Full diagnostics for CUA-NSIS smoke testing: tools, system, errors."""
    try:
        tools = await mcp.list_tools()
        tool_list = [{"name": t.name} for t in tools]
    except Exception as e:
        tool_list = []
        logger.warning(f"Diagnostics tool listing failed: {e}")
    return {
        "status": "ok",
        "server": "system-admin-mcp",
        "version": "0.4.0",
        "uptime_seconds": int(time.time() - START_TIME),
        "tool_count": len(tool_list),
        "tools": tool_list,
        "system": {"windows": os.name == "nt", "cpu_count": psutil.cpu_count()},
        "errors": [],
    }


@app.post("/api/shutdown")
async def api_shutdown() -> dict[str, Any]:
    """Gracefully stop the server (agent/self-termination endpoint)."""
    threading.Timer(0.5, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
    return {"status": "shutting_down"}


async def _run_tool(name: str, **kwargs: Any) -> Any:
    """Run an MCP tool by name; handles FastMCP 3.1+ tool lookup."""
    try:
        # FastMCP 3.1+ get_tool is async
        tool = await mcp.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")

        # Extract function from tool object
        fn: Any = getattr(tool, "fn", tool)

        if asyncio.iscoroutinefunction(fn):
            return await fn(**kwargs)
        return await asyncio.to_thread(fn, **kwargs)
    except Exception as e:
        logger.error(f"Error resolving tool '{name}': {e}")
        # Fallback to internal lookup if get_tool fails
        try:
            if hasattr(mcp, "local_provider") and hasattr(mcp.local_provider, "_components"):
                components = mcp.local_provider._components
                tool_key = f"tool:{name}@"
                if tool_key in components:
                    tool = components[tool_key]
                    fn: Any = getattr(tool, "fn", tool)
                    if asyncio.iscoroutinefunction(fn):
                        return await fn(**kwargs)
                    return await asyncio.to_thread(fn, **kwargs)
        except Exception as e2:
            logger.error(f"Fallback resolution failed for '{name}': {e2}")
        raise ValueError(f"Tool '{name}' not found or failed to execute: {e}") from e


@app.get("/api/logs")
async def get_logs(tail: int = 200, file: str | None = None) -> dict[str, Any]:
    """Read log files from SystemAdminMCP log directories."""
    appdata = Path(os.environ.get("LOCALAPPDATA", ""))
    log_dirs = [
        appdata / "SystemAdminMCP" / "Logs",
        appdata / "SystemAdminMCP",
    ]
    log_files: list[Path] = []
    log_dir = log_dirs[0]
    for log_dir in log_dirs:
        if log_dir.is_dir():
            log_files.extend(log_dir.glob("*.log"))
    if not log_files:
        return {"lines": [], "source": str(log_dirs[0]), "message": "No log files found"}
    try:
        if file:
            log_path = appdata / "SystemAdminMCP" / "Logs" / file
            if log_path.is_file():
                paths = [log_path]
            else:
                log_path = appdata / "SystemAdminMCP" / file
                if log_path.is_file():
                    paths = [log_path]
                else:
                    return {"lines": [], "source": str(log_path), "message": "File not found"}
        else:
            paths = sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)
        lines: list[str] = []
        for p in paths[:3]:
            with open(p, encoding="utf-8", errors="replace") as f:
                chunk = f.readlines()
            lines.extend(chunk)
        if tail and len(lines) > tail:
            lines = lines[-tail:]
        return {"lines": lines, "source": str(paths[0]) if paths else str(log_dir)}
    except Exception as e:
        logger.exception("Error reading logs")
        return {"lines": [], "source": str(log_dir), "message": str(e)}


@app.get("/api/volumes")
async def api_volumes() -> dict[str, Any]:
    """List volumes with usage via MCP list_volumes + psutil.

    Disk stat calls run in a worker thread: sleeping USB drives can stall
    for seconds each, and blocking the event loop wedges every endpoint
    (seen 2026-09-28: whole backend unresponsive behind one volumes call).
    """
    try:
        result = await _run_tool("list_volumes")
        volumes = result if isinstance(result, list) else result.get("volumes", [])

        def _enrich() -> list[dict[str, Any]]:
            fstype_by_drive = {p.device.rstrip("\\").lower(): p.fstype for p in psutil.disk_partitions()}
            enriched: list[dict[str, Any]] = []
            for v in volumes:
                drive = v.get("drive", "") if isinstance(v, dict) else str(v)
                item: dict[str, Any] = dict(v) if isinstance(v, dict) else {"drive": drive}
                item.setdefault("fstype", fstype_by_drive.get(drive.rstrip("\\").lower(), ""))
                try:
                    usage = psutil.disk_usage(drive)
                    item.update(
                        {
                            "total_gb": round(usage.total / (1024**3), 1),
                            "used_gb": round(usage.used / (1024**3), 1),
                            "free_gb": round(usage.free / (1024**3), 1),
                            "percent": usage.percent,
                        }
                    )
                except Exception:
                    item.update({"total_gb": None, "used_gb": None, "free_gb": None, "percent": None})
                enriched.append(item)
            return enriched

        return {"volumes": await asyncio.to_thread(_enrich)}
    except Exception as e:
        logger.exception("Error listing volumes")
        return {"volumes": [], "error": str(e)}


@app.post("/api/disk_usage")
async def api_disk_usage(request: Request) -> dict[str, Any]:
    """Get disk usage for a path via MCP get_disk_usage."""
    try:
        body = await request.json()
        path_arg = body.get("path", "")
        if not path_arg:
            return {"status": "error", "message": "path required"}
        result = await _run_tool("get_disk_usage", path=path_arg)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.exception("Error getting disk usage")
        return {"status": "error", "message": str(e)}


@app.post("/api/file_owner")
async def api_file_owner(request: Request) -> dict[str, Any]:
    """Get file/directory owner via MCP get_file_owner."""
    try:
        body = await request.json()
        path_arg = body.get("path", "")
        if not path_arg:
            return {"status": "error", "message": "path required"}
        result = await _run_tool("get_file_owner", file_path=path_arg)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.exception("Error getting file owner")
        return {"status": "error", "message": str(e)}


@app.post("/api/recover_file")
async def api_recover_file(request: Request) -> dict[str, Any]:
    """Attempt file recovery via MCP recover_file."""
    try:
        body = await request.json()
        original_path = body.get("original_path", "")
        output_dir = body.get("output_dir", "")
        if not original_path or not output_dir:
            return {"status": "error", "message": "original_path and output_dir required"}
        result = await _run_tool("recover_file", original_path=original_path, output_dir=output_dir)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.exception("Error recovering file")
        return {"status": "error", "message": str(e)}


@app.get("/api/processes")
async def api_processes(
    filter_name: str | None = None,
    filter_user: str | None = None,
    sort_by: str = "cpu",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """List processes via portmanteau system_admin tool.

    NOTE (2026-09-29): runs the sync psutil implementation in a worker
    thread on purpose. It used to go through the async portmanteau wrapper
    in-loop, where one wedged proc.status() froze the whole event loop
    (single worker: even /api/health starved).
    """
    try:
        from system_admin_mcp.tools.services_and_tasks import list_processes

        result = await asyncio.to_thread(
            list_processes,
            filter_name=filter_name or None,
            filter_user=filter_user or None,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )
        if result.get("status") != "success":
            return {"processes": [], "total": 0, "error": result.get("error", "unknown")}
        processes = result.get("processes", [])
        for p in processes:
            mem = p.get("memory_info") or {}
            rss = mem.get("rss", 0)
            p["memory_mb"] = round(rss / (1024 * 1024), 2) if rss else None
        return {
            "processes": processes,
            "total": result.get("total", len(processes)),
            "page": result.get("page", page),
            "page_size": result.get("page_size", page_size),
        }
    except Exception as e:
        logger.exception("Error listing processes")
        return {"processes": [], "total": 0, "error": str(e)}


@app.get("/api/processes/{pid:int}")
async def api_process_detail(pid: int) -> dict[str, Any]:
    """Get process detail via portmanteau system_admin tool."""
    try:
        result = await _run_tool(
            "system_admin",
            operation="analyze_process",
            pid=pid,
        )
        if result.get("status") != "success":
            return {"status": "error", "message": result.get("error", "unknown")}
        return {"status": "success", "process": result.get("process", result)}
    except Exception as e:
        logger.exception("Error getting process detail")
        return {"status": "error", "message": str(e)}


@app.get("/api/services")
async def api_services(
    filter_status: str | None = None,
    filter_name: str | None = None,
    include_system: bool = True,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """List Windows services via portmanteau system_admin tool."""
    try:
        result = await _run_tool(
            "system_admin",
            operation="list_services",
            filter_status=filter_status or None,
            filter_name=filter_name or None,
            include_system=include_system,
            page=page,
            page_size=page_size,
        )
        if result.get("status") != "success":
            return {"services": [], "total": 0, "error": result.get("error", "unknown")}
        return {
            "services": result.get("services", []),
            "total": result.get("total", len(result.get("services", []))),
            "page": result.get("page", page),
            "page_size": result.get("page_size", page_size),
        }
    except Exception as e:
        logger.exception("Error listing services")
        return {"services": [], "total": 0, "error": str(e)}


@app.get("/api/crash/dumps")
async def api_crash_dumps() -> dict[str, Any]:
    """Inventory crash artefacts via portmanteau system_admin tool."""
    try:
        result = await _run_tool("system_admin", operation="list_crash_dumps")
        return result
    except Exception as e:
        logger.exception("Error listing crash dumps")
        return {"status": "error", "error": str(e)}


@app.get("/api/crash/bugcheck-history")
async def api_crash_bugcheck_history(
    days_back: int = 7,
    max_results: int = 50,
) -> dict[str, Any]:
    """Correlate shutdown/crash events via portmanteau system_admin tool."""
    try:
        result = await _run_tool(
            "system_admin",
            operation="get_bugcheck_history",
            days_back=days_back,
            max_results=max_results,
        )
        return result
    except Exception as e:
        logger.exception("Error reading bugcheck history")
        return {"status": "error", "error": str(e)}


@app.post("/api/crash/analyze-minidump")
async def api_crash_analyze_minidump(request: Request) -> dict[str, Any]:
    """Triage-parse a minidump via portmanteau system_admin tool."""
    try:
        body = await request.json()
        result = await _run_tool(
            "system_admin",
            operation="analyze_minidump",
            dump_path=body.get("dump_path") or None,
            max_results=int(body.get("max_drivers", 40)),
        )
        return result
    except Exception as e:
        logger.exception("Error analyzing minidump")
        return {"status": "error", "error": str(e)}


@app.post("/api/crash/windbg")
async def api_crash_windbg(request: Request) -> dict[str, Any]:
    """Run WinDbg !analyze -v via portmanteau system_admin tool."""
    try:
        body = await request.json()
        result = await _run_tool(
            "system_admin",
            operation="windbg_analyze",
            dump_path=body.get("dump_path") or None,
            timeout_seconds=int(body.get("timeout_seconds", 120)),
        )
        return result
    except Exception as e:
        logger.exception("Error running windbg analysis")
        return {"status": "error", "error": str(e)}


@app.get("/api/admin-toolbox")
async def api_admin_toolbox() -> dict[str, Any]:
    """Inventory admin toolbox apps via portmanteau system_admin tool."""
    try:
        result = await _run_tool("system_admin", operation="audit_admin_toolbox")
        return result
    except Exception as e:
        logger.exception("Error auditing admin toolbox")
        return {"status": "error", "error": str(e)}


def _audit_error(operation: str, e: Exception) -> dict[str, Any]:
    logger.exception(f"Error running {operation}")
    return {"status": "error", "error": str(e)}


@app.get("/api/firmware-posture")
async def api_firmware_posture() -> dict[str, Any]:
    """Firmware posture via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="get_firmware_posture")
    except Exception as e:
        return _audit_error("get_firmware_posture", e)


@app.get("/api/scheduled-tasks")
async def api_scheduled_tasks(max_results: int = 50) -> dict[str, Any]:
    """Scheduled tasks via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="audit_scheduled_tasks", max_results=max_results)
    except Exception as e:
        return _audit_error("audit_scheduled_tasks", e)


@app.get("/api/update-status")
async def api_update_status() -> dict[str, Any]:
    """Update status via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="get_update_status")
    except Exception as e:
        return _audit_error("get_update_status", e)


@app.get("/api/local-admins")
async def api_local_admins() -> dict[str, Any]:
    """Local admins via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="audit_local_admins")
    except Exception as e:
        return _audit_error("audit_local_admins", e)


@app.get("/api/smb-shares")
async def api_smb_shares() -> dict[str, Any]:
    """SMB shares via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="audit_smb_shares")
    except Exception as e:
        return _audit_error("audit_smb_shares", e)


@app.get("/api/shadow-copies")
async def api_shadow_copies() -> dict[str, Any]:
    """Shadow copies via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="list_shadow_copies")
    except Exception as e:
        return _audit_error("list_shadow_copies", e)


@app.get("/api/drivers")
async def api_drivers(class_filter: str | None = None, max_results: int = 100) -> dict[str, Any]:
    """Driver inventory via portmanteau system_admin tool."""
    try:
        return await _run_tool(
            "system_admin", operation="audit_drivers", class_filter=class_filter, max_results=max_results
        )
    except Exception as e:
        return _audit_error("audit_drivers", e)


@app.get("/api/reliability-history")
async def api_reliability_history(days_back: int = 7, max_results: int = 50) -> dict[str, Any]:
    """Reliability history via portmanteau system_admin tool."""
    try:
        return await _run_tool(
            "system_admin", operation="get_reliability_history", days_back=days_back, max_results=max_results
        )
    except Exception as e:
        return _audit_error("get_reliability_history", e)


@app.get("/api/winget-outdated")
async def api_winget_outdated(max_results: int = 30) -> dict[str, Any]:
    """Winget upgrades via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="winget_outdated", max_results=max_results)
    except Exception as e:
        return _audit_error("winget_outdated", e)


@app.get("/api/path-dross")
async def api_path_dross() -> dict[str, Any]:
    """PATH audit via portmanteau system_admin tool."""
    try:
        return await _run_tool("system_admin", operation="audit_path_dross")
    except Exception as e:
        return _audit_error("audit_path_dross", e)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("WEBAPP_PORT", 10861))
    uvicorn.run(app, host="0.0.0.0", port=port)  # noqa: S104
