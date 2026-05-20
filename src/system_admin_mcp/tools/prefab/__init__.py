"""
Prefab Tools Registry — System Admin MCP v0.4.0
"""

import logging

logger = logging.getLogger(__name__)


def register_prefab_tools(mcp) -> None:
    """Register Prefab UI tools. Called when prefab-ui is installed."""
    from system_admin_mcp.tools.prefab.system_cards import (
        list_services_card,
        system_health_card,
        top_processes_card,
        volume_status_card,
    )

    mcp.tool(app=True)(system_health_card)
    mcp.tool(app=True)(top_processes_card)
    mcp.tool(app=True)(list_services_card)
    mcp.tool(app=True)(volume_status_card)

    logger.info(
        "Prefab tools registered: system_health_card, top_processes_card, list_services_card, volume_status_card"
    )


__all__ = ["register_prefab_tools"]
