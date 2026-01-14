# System Admin MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.10+ compatible MCP service for elevated system administration tasks.

## Features

- **File Recovery**: Recover deleted files from NTFS volumes
- **Security Management**: Manage file and folder permissions
- **Volume Maintenance**: Perform disk maintenance operations
- **System Diagnostics**: Collect system information and diagnostics

## Prerequisites

- Windows 10/11 or Windows Server 2016+
- Python 3.8+
- Administrator privileges (for elevated operations)

## Installation

### Option 1: For Cursor IDE

**Important:** Cursor uses system Python. Install dependencies in the Python that Cursor uses:

```powershell
cd d:\Dev\repos\system-admin-mcp
python -m pip install -e .[dev]
```

See `CURSOR_SETUP.md` for detailed Cursor configuration instructions.

### Option 2: For Claude Desktop / General Development

1. Clone the repository:

   ```powershell
   git clone https://github.com/your-username/system-admin-mcp.git
   cd system-admin-mcp
   ```

2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```powershell
   pip install -e .[dev]
   ```

### Option 3: For Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "python",
      "args": ["-m", "system_admin_mcp.__main__"],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/system-admin-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Note:** Some JSON linters object to `cwd` parameter. Using `-m` module execution with `PYTHONPATH` avoids this issue.

## Usage

### Running the MCP Server

```powershell
# Run in development mode
python -m system_admin_mcp
```

### Building the DXT Package

```powershell
# Build the package
python -m build

# The DXT package will be created in the dist/ directory
```

## Development

### Code Style

This project uses:

- Black for code formatting
- isort for import sorting
- mypy for type checking
- pylint for code quality

Run the following to format and check the code:

```powershell
# Format code
black src tests
isort src tests

# Run linters
pylint src tests
mypy src tests
```

### Testing

```powershell
# Run tests
pytest

# Run with coverage report
pytest --cov=system_admin_mcp --cov-report=html
```

## Uninstallation

### Standard Uninstallation

1. **Remove the DXT package** from your MCP client:

   ```powershell
   mcp uninstall system-admin-mcp
   ```

2. **Uninstall the Windows Service** using the uninstall script:

   ```powershell
   # Run as Administrator
   .\scripts\uninstall.ps1
   ```

   Options:
   - `-Force`: Skip confirmation prompts
   - `-KeepLogs`: Preserve log files for debugging

### Alternative: Disable Without Uninstalling

If you want to temporarily disable the bridge without uninstalling:

```powershell
# Disable the bridge
.\scripts\disable_bridge.ps1

# Re-enable later if needed
.\scripts\disable_bridge.ps1 -Revert
```

### Manual Cleanup (if needed)

If the uninstall script fails, you may need to manually remove:

1. Service registration:
   ```powershell
   sc.exe delete SystemAdminMCP
   ```

2. Installation directory:

   ```text
   %ProgramFiles%\System Admin MCP
   ```

3. Application data:

   ```text
   %LOCALAPPDATA%\SystemAdminMCP
   ```

## Troubleshooting

### Bridge Shows as Disabled

If the bridge is disabled but you want to re-enable it:

1. Run the disable script with the `-Revert` flag:

   ```powershell
   .\scripts\disable_bridge.ps1 -Revert
   ```

2. Restart your MCP client

### Service Fails to Start

1. Check the Windows Event Log for errors
2. Verify the service account has necessary permissions
3. Check if the named pipe is accessible:

   ```powershell
   Test-Path "\\.\pipe\SystemAdminMCP"
   ```

## Security Considerations

- The service runs with elevated privileges
- All operations are logged to `%LOCALAPPDATA%\SystemAdminMCP\Logs`
- The named pipe is secured to only allow local connections
- Sensitive operations require explicit user confirmation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
