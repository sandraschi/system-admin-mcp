"""
System Admin MCP - FastMCP 3.2 SOTA Implementation

Full FastMCP 3.2 conformance: sampling, skills, prompts, prefab UI,
SkillsDirectoryProvider, agentic workflows.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP


@asynccontextmanager
async def lifespan(app: FastMCP):
    from system_admin_mcp.tools.monitoring import watcher_manager
    app.logger.info("Initializing System Admin MCP v0.3.0...")

    _ = watcher_manager  # ensure loaded

    # Register Skills provider
    try:
        from fastmcp.server.providers.skills import SkillsDirectoryProvider
        skills_dir = Path(__file__).resolve().parent.parent.parent / "skills"
        if skills_dir.is_dir():
            app.add_provider(SkillsDirectoryProvider(roots=[skills_dir]))
            app.logger.info(f"Skills provider registered: {skills_dir}")
        else:
            app.logger.warning(f"Skills dir not found at {skills_dir}")
    except ImportError:
        app.logger.warning("SkillsDirectoryProvider unavailable in this FastMCP build")
    except Exception as e:
        app.logger.warning(f"Skills provider registration failed: {e}")

    # Register Prefab tools (optional [apps] extra)
    if os.getenv("SYSADMIN_PREFAB_APPS", "1") != "0":
        try:
            from system_admin_mcp.tools.prefab import register_prefab_tools
            register_prefab_tools(app)
            app.logger.info("Prefab tools registered")
        except ImportError:
            app.logger.info("prefab-ui not installed — prefab tools skipped (uv sync --extra apps)")
        except Exception as e:
            app.logger.warning(f"Prefab registration failed: {e}")

    yield

    app.logger.info("Shutting down System Admin MCP...")
    watcher_manager.shutdown()


# FastMCP 3.2 instance
mcp = FastMCP(
    "system-admin-mcp",
    version="0.3.0",
    lifespan=lifespan,
    instructions=(
        "SOTA v0.3.0: Windows System Administration Hub — "
        "elevated ops, file recovery, security, diagnostics, services, processes. "
        "Full FastMCP 3.2 conformance: sampling, skills, prompts, prefab UI."
    ),
    strict_input_validation=True,
    mask_error_details=True,
    client_log_level="info",
)
