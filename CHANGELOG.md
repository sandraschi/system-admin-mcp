# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-02

### Changed
- **Async Tool Resolution**: Refactored `server.py` to correctly `await mcp.get_tool(name)`, resolving `TypeError` when calling tools in FastMCP 3.1+.
- **Modernized Linting**: Replaced legacy linters (Black, isort, pylint, mypy) with **Ruff** for faster, unified linting and formatting.
- **Type Annotations**: Modernized type hints to Python 3.9+ standards (using `dict` instead of `Dict`, etc.) via `ruff --fix`.

### Fixed
- Resolved `RuntimeWarning: coroutine 'FastMCP.get_tool' was never awaited` which prevented tool execution.
- Fixed 157 linting and formatting issues across the codebase.
- Improved error handling in `_run_tool` with async resolution logic.

---

## [0.1.0] - 2025-10-21

---

## How to Update This File

When making changes, add them under the appropriate section:
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
