"""MCPB-compliant entry point for System Admin MCP.

This module allows the MCPB runtime to discover and launch the server
via `python server/__main__.py`.
"""

import sys
from pathlib import Path

parent_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(parent_dir))

from system_admin_mcp.main import main  # noqa: E402

if __name__ == "__main__":
    main()
