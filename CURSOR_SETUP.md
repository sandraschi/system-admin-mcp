# System Admin MCP - Cursor IDE Setup Guide

**Quick setup guide for running System Admin MCP in Cursor IDE.**

## Prerequisites

1. **Python 3.12+** installed and in PATH
2. **Windows 10/11 or Windows Server 2016+**
3. **Administrator privileges** (for elevated operations)
4. **System Admin MCP** installed in editable mode

## Installation

**Important:** Cursor uses its own internal extension host logic. For the best experience, install the package in "editable" mode in your primary Python environment.

```powershell
cd d:\Dev\repos\system-admin-mcp

# Recommended: Install using uv
uv pip install -e .[dev]

# Alternatively, using standard pip:
python -m pip install -e .[dev]
```

**Note:** Dependencies are defined in `pyproject.toml`. The package requires **FastMCP 3.1+**, pywin32, psutil, and wmi.

## Cursor Configuration

Add to your Cursor MCP configuration:
**Settings** -> **Features** -> **MCP Servers** -> **Add New MCP Server**

- **Name**: `system-admin-mcp`
- **Type**: `command`
- **Command**: `uv --directory D:/Dev/repos/system-admin-mcp run system-admin-mcp`

### Manual JSON Configuration
If editing `%APPDATA%\Cursor\User\globalStorage\cursor-storage\mcp_config.json` directly:

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "D:/Dev/repos/system-admin-mcp",
        "run",
        "system-admin-mcp"
      ]
    }
  }
}
```

## Verification

1. **Check Python import:**
   ```powershell
   uv run python -c "import system_admin_mcp; print('SUCCESS')"
   ```

2. **Test MCP server startup:**
   ```powershell
   uv run system-admin-mcp
   ```
   Should start without errors (Wait for JSON-RPC messages on stdin).

3. **Check Cursor logs:**
   - Location: `%APPDATA%\Cursor\logs\main.log` or the "Output" panel in Cursor.
   - Look for `system-admin-mcp` startup entries.

## Troubleshooting

### `coroutine 'FastMCP.get_tool' was never awaited`
**Solution:** Ensure you are running **FastMCP 3.1.0 or higher**. This error occurs in legacy versions or when calling tools synchronously in the new async registry. The `system-admin-mcp` server has been patched for 3.1+ compatibility.

### `ModuleNotFoundError: No module named 'fastmcp'`
**Solution:**
1. Ensure the package is installed in the environment Cursor is using.
2. If using `uv`, always use the `uv --directory ... run ...` pattern to ensure the correct virtual environment is loaded.

### `Windows-Specific Module Errors (pywin32, wmi)`
**Solution:**
1. Ensure you are on Windows.
2. For `pywin32`, if imports fail even after installation, run the post-install script:
   ```powershell
   uv run python Scripts/pywin32_postinstall.py -install
   ```

## Available Tools

System Admin MCP provides high-level "portmanteau" tools:
- **`list_volumes`**: List all available volumes with status and type.
- **`get_hardware_info`**: Detailed hardware diagnostics (CPU, GPU, RAM).
- **`audit_permissions`**: Analyze security and permissions for paths.
- **`disk_cleanup`**: Perform system and temp file cleanup (Admin required).
- **`recover_file`**: Advanced NTFS file recovery logic.

## Reference

- **Project README**: `README.md`
- **Changelog**: `CHANGELOG.md`
- **FastMCP Standards**: [AGENT_PROTOCOLS.md](file:///D:/Dev/repos/mcp-central-docs/standards/AGENT_PROTOCOLS.md)

---
*Updated: 2026-04-02*
