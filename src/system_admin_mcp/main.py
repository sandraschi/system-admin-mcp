"""Main entry point for the System Admin MCP service."""

import logging
import sys
from typing import Any

from fastmcp import FastMCP

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # Use stderr for logging (stdout is for MCP protocol)
)
logger = logging.getLogger(__name__)

# Import the FastMCP instance
from system_admin_mcp.app import mcp  # noqa: E402

from .transport import run_server  # noqa: E402

# Import tools to trigger @mcp.tool() decorators
# Wrap imports in try/except to prevent startup failures
try:
    from system_admin_mcp.prompts import register_all_prompts

    register_all_prompts(mcp)
except Exception as e:
    logger.warning(f"Failed to register prompts: {e}")

try:
    from system_admin_mcp.tools import system_ops  # noqa: F401
except Exception as e:
    logger.warning(f"Failed to import system_ops: {e}. Some tools may not be available.")

try:
    from system_admin_mcp.tools import portmanteau  # noqa: F401
except Exception as e:
    logger.warning(f"Failed to import portmanteau: {e}. Some tools may not be available.")

try:
    from system_admin_mcp.tools import agentic_system_workflow  # noqa: F401
except Exception as e:
    logger.warning(f"Failed to import agentic_system_workflow: {e}. SEP-1577 tools may not be available.")


def create_app(config: dict[str, Any] | None = None) -> FastMCP:
    """Create and configure the MCP application.

    Args:
        config: Optional configuration dictionary (not used in FastMCP 2.13+)

    Returns:
        Configured FastMCP instance
    """
    # Tools are auto-registered via @mcp.tool() decorators when modules are imported
    # The import above triggers the decorators

    logger.info("System Admin MCP initialized")
    return mcp


async def main_async() -> None:
    """Run the MCP server asynchronously."""
    try:
        app = create_app()
        # FastMCP 2.14+ requires run_stdio_async()
        logger.info("Starting MCP server with stdio transport...")
        run_server(app, server_name="system-admin-mcp")
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error starting server: {e}", exc_info=True)
        sys.exit(1)


def main() -> None:
    """Run the MCP server."""
    import argparse
    import os

    import uvicorn

    parser = argparse.ArgumentParser(description="System Admin MCP server")
    parser.add_argument("--web", action="store_true", help="Start the FastAPI web server")
    args = parser.parse_args()

    if args.web:
        port = int(os.getenv("WEBAPP_PORT", 10861))
        logger.info(f"Starting FastAPI web server on port {port}...")
        uvicorn.run("system_admin_mcp.server:app", host="0.0.0.0", port=port, reload=True)  # noqa: S104
    else:
        app = create_app()
        run_server(app, server_name="system-admin-mcp")


if __name__ == "__main__":
    main()
