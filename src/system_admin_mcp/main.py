"""Main entry point for the System Admin MCP service."""
import logging
from typing import Any, Dict

from mcp import Application

from system_admin_mcp.tools import system_ops

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config: Dict[str, Any] = None) -> Application:
    """Create and configure the MCP application.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured MCP Application instance
    """
    if config is None:
        config = {}

    app = Application("system-admin-mcp", config=config)

    # Register tool modules
    app.register_tool_module(system_ops)

    logger.info("System Admin MCP initialized")
    return app


def main() -> None:
    """Run the MCP server."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
