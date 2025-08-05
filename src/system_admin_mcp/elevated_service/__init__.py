"""System Admin MCP Elevated Service.

This module contains the elevated service that runs with admin privileges
and handles privileged operations.
"""

__all__ = ["ElevatedService"]

from .service import ElevatedService
