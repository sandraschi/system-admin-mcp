import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

import psutil
from fastapi import FastAPI, Request
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10860",
        "http://127.0.0.1:10860",
    ],
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
                        schema = params.model_json_schema()
                    elif hasattr(params, "schema"):
                        schema = params.schema()

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
    try:
        body = await request.json()
        tool_name = body.get("name")
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
        logger.error(f"Error calling tool {tool_name if 'tool_name' in locals() else 'unknown'}: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/metrics")
async def get_metrics() -> dict[str, Any]:
    """Extended system metrics for monitoring."""
    net_io = psutil.net_io_counters()
    return {
        "cpu_count": psutil.cpu_count(),
        "load_average": os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0],
        "network": {"bytes_sent": net_io.bytes_sent, "bytes_recv": net_io.bytes_recv},
    }


async def _run_tool(name: str, **kwargs: Any) -> Any:
    """Run an MCP tool by name; handles FastMCP 3.1+ tool lookup."""
    try:
        # FastMCP 3.1+ get_tool is async
        tool = await mcp.get_tool(name)

        # Extract function from tool object
        fn = getattr(tool, "fn", tool)

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
                    fn = getattr(tool, "fn", tool)
                    if asyncio.iscoroutinefunction(fn):
                        return await fn(**kwargs)
                    return await asyncio.to_thread(fn, **kwargs)
        except Exception as e2:
            logger.error(f"Fallback resolution failed for '{name}': {e2}")
        raise ValueError(f"Tool '{name}' not found or failed to execute: {e}") from e


@app.get("/api/logs")
async def get_logs(tail: int = 200, file: str | None = None) -> dict[str, Any]:
    """Read log files from SystemAdminMCP log directory."""
    log_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "SystemAdminMCP" / "Logs"
    if not log_dir.is_dir():
        return {"lines": [], "source": str(log_dir), "message": "Log directory not found"}
    try:
        if file:
            log_path = log_dir / file
            if not log_path.is_file():
                return {"lines": [], "source": str(log_path), "message": "File not found"}
            paths = [log_path]
        else:
            paths = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not paths:
                return {"lines": [], "source": str(log_dir), "message": "No log files"}
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
    """List volumes via MCP list_volumes."""
    try:
        result = await _run_tool("list_volumes")
        return {"volumes": result if isinstance(result, list) else result.get("volumes", [])}
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
    """List processes via portmanteau system_admin tool."""
    try:
        result = await _run_tool(
            "system_admin",
            operation="list_processes",
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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("WEBAPP_PORT", 10861))
    uvicorn.run(app, host="0.0.0.0", port=port)  # noqa: S104
