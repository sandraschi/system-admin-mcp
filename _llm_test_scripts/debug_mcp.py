import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from system_admin_mcp.app import mcp
from system_admin_mcp.tools import system_ops, portmanteau, services_and_tasks

print(f"MCP Instance: {mcp}")
print(f"Attributes: {dir(mcp)}")

# Check for tools in common locations correctly
if hasattr(mcp, "_tools"):
    print(f"Tools in _tools: {list(mcp._tools.keys())}")
else:
    print("No _tools attribute found")

# Iterate through members to find where tools are stored if not in _tools
for attr in dir(mcp):
    val = getattr(mcp, attr)
    if isinstance(val, dict) and any("ping" in str(k) for k in val.keys()):
        print(f"Found tools-like dict in attribute: {attr}")

# Try to find a tool manually
try:

    @mcp.tool()
    def diagnostic_ping():
        return "pong"

    print("Successfully registered diagnostic tool")
    if hasattr(mcp, "_tools"):
        print(f"Tools after manual reg: {list(mcp._tools.keys())}")
except Exception as e:
    print(f"Manual registration error: {e}")
