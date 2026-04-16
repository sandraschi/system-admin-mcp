"""
Prefab Tools Registry — System Admin MCP v0.3.0
"""

import logging

logger = logging.getLogger(__name__)


def register_prefab_tools(mcp) -> None:
    """Register Prefab UI tools. Called only when prefab-ui is installed."""
    from system_admin_mcp.tools.prefab.system_cards import (
        system_health_card,
        top_processes_card,
    )

    mcp.tool(app=True)(system_health_card)
    mcp.tool(app=True)(top_processes_card)

    logger.info("Prefab tools registered: system_health_card, top_processes_card")


__all__ = ["register_prefab_tools"]
