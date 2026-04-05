"""FastMCP application instance for System Admin MCP."""

from fastmcp import FastMCP

# Create FastMCP instance at module level
mcp = FastMCP("system-admin-mcp")

@mcp.on_startup
async def on_startup():
    from system_admin_mcp.tools.monitoring import watcher_manager
    logger = mcp.logger
    logger.info("Initializing System Admin Monitoring Services...")
    # The watcher_manager handles its own observer start in __init__
    # but we ensure it's loaded here.
    _ = watcher_manager

@mcp.on_shutdown
async def on_shutdown():
    from system_admin_mcp.tools.monitoring import watcher_manager
    logger = mcp.logger
    logger.info("Shutting down System Admin Monitoring Services...")
    watcher_manager.shutdown()
