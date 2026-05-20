"""MCP server entry point for System Admin MCP.

This is the MCPB-compliant server wrapper that launches the System Admin MCP server.
"""

import sys
from pathlib import Path

# Add parent directory to path to import main server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import and run main server
try:
    from system_admin_mcp.__main__ import main
except ImportError:
    # Fallback
    import system_admin_mcp

    main = system_admin_mcp.main

if __name__ == "__main__":
    main()
