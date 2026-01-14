# System Admin MCP - Cursor IDE Setup Guide

**Quick setup guide for running System Admin MCP in Cursor IDE.**

## Prerequisites

1. **Python 3.8+** installed and in PATH
2. **Windows 10/11 or Windows Server 2016+**
3. **Administrator privileges** (for elevated operations)
4. **System Admin MCP** installed in editable mode

## Installation

**Important:** Cursor uses the system Python, so dependencies must be installed globally or in the Python that Cursor uses.

```powershell
cd d:\Dev\repos\system-admin-mcp

# Option 1: Install in system Python (recommended for Cursor)
# Find your system Python path (usually shown in Cursor error logs)
# Example: C:\Users\sandr\AppData\Local\Programs\Python\Python310\python.exe
python -m pip install -e .[dev]

# Option 2: Install in virtual environment (if using venv in config)
python -m venv venv
venv\Scripts\activate
pip install -e .[dev]
```

**Note:** Dependencies are defined in `pyproject.toml`. The package includes FastMCP 2.14+, pywin32, psutil, and wmi (Windows-specific).

## Cursor Configuration

Add to your Cursor MCP configuration file:
**Location**: `%APPDATA%\Cursor\User\globalStorage\cursor-storage\mcp_config.json`

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "python",
      "args": [
        "-m",
        "system_admin_mcp.__main__"
      ],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/system-admin-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Note:** Some JSON linters object to `cwd` parameter. Using `-m` module execution with `PYTHONPATH` avoids this issue.

### Using Virtual Environment

If using a virtual environment:

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "d:\\Dev\\repos\\system-admin-mcp\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "system_admin_mcp.__main__"
      ],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/system-admin-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Alternative: Using main.py with Absolute Path

If you prefer using `main.py` directly (avoids `cwd` which some linters reject):

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "python",
      "args": [
        "D:/Dev/repos/system-admin-mcp/src/system_admin_mcp/main.py"
      ],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/system-admin-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Verification

1. **Check Python import:**
   ```powershell
   python -c "import sys; sys.path.insert(0, 'src'); from system_admin_mcp.app import mcp; print('SUCCESS')"
   ```

2. **Test MCP server startup:**
   ```powershell
   python -m system_admin_mcp.__main__
   ```
   Should start without errors and wait for JSON-RPC messages on stdin.

3. **Check Cursor logs:**
   - Location: `%APPDATA%\Cursor\logs\`
   - Look for `system-admin-mcp` in log files
   - Check for any import errors or startup failures

## Troubleshooting

### ImportError: No module named 'fastmcp' / ModuleNotFoundError: Missing dependencies

**Solution:**
1. **Critical:** Cursor uses system Python, not your current shell's Python
2. Find system Python path from Cursor error logs (e.g., `C:\Users\sandr\AppData\Local\Programs\Python\Python310\python.exe`)
3. Install dependencies in system Python:
   ```powershell
   C:\Users\sandr\AppData\Local\Programs\Python\Python310\python.exe -m pip install -e .[dev]
   ```
4. Or install globally: `python -m pip install -e .[dev]` (if `python` points to system Python)

### ModuleNotFoundError: No module named 'system_admin_mcp'

**Solution:**
1. Ensure package is installed in the Python that Cursor uses: `python -m pip install -e .[dev]`
2. Set PYTHONPATH in Cursor config: `"PYTHONPATH": "D:/Dev/repos/system-admin-mcp/src"`
3. Use absolute path to Python executable in venv if using virtual environment

### Windows-Specific Module Errors (pywin32, wmi)

**Solution:**
1. Ensure you're on Windows (this MCP server is Windows-only)
2. Install Windows-specific dependencies:
   ```powershell
   pip install pywin32 wmi
   ```
3. For pywin32, you may need to run post-install script:
   ```powershell
   python Scripts/pywin32_postinstall.py -install
   ```

### Server starts but tools don't appear

**Solution:**
1. Check Cursor logs for JSON-RPC errors
2. Verify FastMCP version: `pip show fastmcp` (should be >=2.14.0,<3.0.0)
3. Restart Cursor after configuration changes
4. Check that tools are properly imported (see `main.py` for tool imports)

### Administrator Privileges Required

**Solution:**
1. Some operations require administrator privileges
2. Ensure Cursor is running with appropriate permissions
3. Check Windows Event Log for permission errors
4. The elevated service may need to be installed separately (see `README.md`)

## Available Tools

System Admin MCP provides portmanteau tools for:
- **File Recovery**: Recover deleted files from NTFS volumes
- **Security Management**: Manage file and folder permissions
- **Volume Maintenance**: Perform disk maintenance operations
- **System Diagnostics**: Collect system information and diagnostics

## Architecture Notes

**Important:** This MCP server uses an elevated Windows service for privileged operations:
- **MCP Server**: Runs natively (stdio transport for Claude Desktop/Cursor)
- **Elevated Service**: Windows service for privileged operations (optional, see `README.md`)
- **User Bridge**: Named pipe communication between MCP server and service

**What runs where:**
- ✅ **MCP server**: Native Python (stdio for Claude Desktop/Cursor)
- ✅ **Elevated service**: Windows service (if installed, see `scripts/uninstall.ps1`)

## Reference

- **Generalized Setup Guide**: `mcp-central-docs/docs/patterns/WEBAPP_SETUP_GUIDE.md`
- **Cursor Standards**: `mcp-central-docs/docs/ecosystem/cursor/README.md`
- **MCP Standards**: `mcp-central-docs/STANDARDS.md`
- **Project README**: `README.md`
