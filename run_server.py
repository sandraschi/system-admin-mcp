import os
import sys

# Frozen (PyInstaller onefile, console=False): sys.stderr/stdout can be None,
# which crashes logging/uvicorn at import. Point them at devnull first.
# (Tauri checklist §J + isatty pitfall.)
if getattr(sys, "frozen", False):
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Eager stdlib C extensions: PyInstaller misses lazy imports (_strptime pitfall).
import _datetime  # noqa: F401
import _strptime  # noqa: F401

# Freeze the mcp bootstrap before fastmcp touches it (frozen Image crash pitfall).
import mcp.types  # noqa: F401

from system_admin_mcp.main import main

if __name__ == "__main__":
    main()
