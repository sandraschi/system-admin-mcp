import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from system_admin_mcp.main import main

if __name__ == "__main__":
    main()
