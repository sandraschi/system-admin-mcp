"""
System Admin MCP - FastMCP 3.2 SOTA Implementation

Full FastMCP 3.2 conformance: sampling, skills, prompts, prefab UI,
SkillsDirectoryProvider, agentic workflows.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server import create_proxy

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastMCP):
    from system_admin_mcp.tools.monitoring import watcher_manager

    logger.info("Initializing System Admin MCP v0.3.0...")

    _ = watcher_manager  # ensure loaded

    # Register Skills provider
    try:
        from fastmcp.server.providers.skills import SkillsDirectoryProvider

        skills_dir = Path(__file__).resolve().parent.parent.parent / "skills"
        if skills_dir.is_dir():
            app.add_provider(SkillsDirectoryProvider(roots=[skills_dir]))
            logger.info(f"Skills provider registered: {skills_dir}")
        else:
            logger.warning(f"Skills dir not found at {skills_dir}")
    except ImportError:
        logger.warning("SkillsDirectoryProvider unavailable in this FastMCP build")
    except Exception as e:
        logger.warning(f"Skills provider registration failed: {e}")

    # Register Prefab tools (optional [apps] extra)
    if os.getenv("SYSADMIN_PREFAB_APPS", "1") != "0":
        try:
            from system_admin_mcp.tools.prefab import register_prefab_tools

            register_prefab_tools(app)
            logger.info("Prefab tools registered")
        except ImportError:
            logger.info("prefab-ui not installed — prefab tools skipped (uv sync --extra apps)")
        except Exception as e:
            logger.warning(f"Prefab registration failed: {e}")

    yield

    logger.info("Shutting down System Admin MCP...")
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

# MCP Bridge: proxy tools from remote MCP servers via MCP_BRIDGE_URLS
_bridge_proxies = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                mcp.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
            except Exception as e:
                logger.debug(f"Bridge proxy failed for {url}: {e}")

# Tools register at import time via @mcp.tool() decorators — importing the
# tool modules here guarantees registration no matter which entry point loads
# the package (main.py, server.py, tests, or an IDE importing `app`).
from system_admin_mcp.tools import (
    agentic_system_workflow,  # noqa: F401
    portmanteau,  # noqa: F401
    services_and_tasks,  # noqa: F401
    system_ops,  # noqa: F401
)
