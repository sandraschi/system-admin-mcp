# System Admin MCP

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.2.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A FastMCP 3.2.0+ compatible MCP service for elevated system administration tasks on Windows.

## Features

- **File Recovery**: Recover deleted files from NTFS volumes
- **Security Management**: Manage file and folder permissions
- **Volume Maintenance**: Perform disk maintenance operations (Check Disk, Defragment, SSD Optimize)
- **System Diagnostics**: Collect hardware, OS, and performance information
- **Software Management**: List installed software from the registry

## Prerequisites

- Windows 10/11 or Windows Server 2016+
- **Python 3.12+**
- [uv](https://docs.astral.sh/uv/) (RECOMMENDED)
- Administrator privileges (for elevated operations)

##  Installation

###  Quick Start
Run immediately via `uvx`:
```bash
uvx system-admin-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/system-admin-mcp", "run", "system-admin-mcp"]
    }
  }
}
```

### Alternative: Manual Setup
1. Clone the repository.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   uv pip install -e .[dev]
   ```

## Development

### Code Quality & Linting
This project uses **Ruff** for unified linting and formatting, adhering to modern Python standards.

```powershell
# Check and fix linting issues
uv run ruff check src --fix

# Format code
uv run ruff format src
```

### Testing
```powershell
# Run tests
uv run pytest

# Run with coverage report
uv run pytest --cov=system_admin_mcp --cov-report=html
```

##  Webapp Dashboard

This MCP server includes a premium web interface for monitoring and control.
By default, the web dashboard runs on port **10860**.
*(Assigned ports: **10860** (Frontend), **10861** (Backend/API))*

To start the webapp dashboard:
1. Navigate to the `web_sota` directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10860` in your browser.

## Security Considerations

- **Elevated Privileges**: The service requires administrator rights for disk and NTFS operations.
- **Logging**: All operations are logged to `%LOCALAPPDATA%\SystemAdminMCP\Logs`.
- **Local Connectivity**: Named pipes and web APIs are secured for local connections by default.
- **User Confirmation**: Critical operations (like file recovery) should be confirmed via the client interface.


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
