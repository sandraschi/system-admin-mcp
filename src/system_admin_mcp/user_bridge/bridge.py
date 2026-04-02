"""User bridge implementation for System Admin MCP.

This module implements a FastMCP 2.10 compatible bridge that communicates
with the elevated Windows service via named pipes. It provides a user-level
interface for system administration operations that require elevation.
"""

import json
import logging
import os
import subprocess
import sys
import time
from typing import Any

import pywintypes
import win32api
import win32file
import win32pipe
import win32service
import win32serviceutil
import winerror

# Configure logging
log_dir = os.path.expandvars(r"%LOCALAPPDATA%\SystemAdminMCP")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "bridge.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Named pipe configuration
PIPE_NAME = r"\\.\pipe\SystemAdminMCP"
BUFFER_SIZE = 65536  # 64KB buffer for large responses
CONNECTION_TIMEOUT = 5000  # 5 seconds in milliseconds


class UserBridge:
    """User bridge for communicating with the elevated service.

    This class implements the FastMCP 2.10 protocol and forwards requests
    to the elevated service via named pipes.
    """

    def __init__(self):
        """Initialize the user bridge with service status checks."""
        self.marker_path = os.path.expandvars(r"%LOCALAPPDATA%\SystemAdminMCP\.bridge_disabled")
        self._check_disabled_state()
        self.service_installed = self._is_service_installed() if not self._disabled else False
        self.service_running = False
        self.pipe_handle = None
        self._check_service_status()
        logger.info("UserBridge initialized")

        # Register cleanup on program exit
        import atexit

        atexit.register(self.cleanup)

    def _check_disabled_state(self) -> None:
        """Check if the bridge has been disabled via marker file."""
        self._disabled = os.path.exists(self.marker_path)
        if self._disabled:
            logger.warning(
                "Bridge is disabled via marker file. To re-enable, run: "
                "powershell -ExecutionPolicy Bypass -File path\\to\\disable_bridge.ps1 -Revert"
            )

    def _is_service_installed(self) -> bool:
        """Check if the service is installed."""
        if getattr(self, "_disabled", False):
            return False

        try:
            # Try to open the service manager
            status = win32serviceutil.QueryServiceStatus("SystemAdminMCP")
            logger.debug(f"Service is installed (state: {status[1]})")
            return True
        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
                logger.debug("Service is not installed")
            else:
                logger.warning(f"Error checking service status: {e}")
            return False

    def _check_service_status(self) -> None:
        """Check if the service is running and update the status.

        This method updates both the service_installed and service_running flags.
        """
        try:
            import win32serviceutil

            # This will raise if service is not installed
            status = win32serviceutil.QueryServiceStatus("SystemAdminMCP")
            self.service_installed = True
            self.service_running = status[1] == win32service.SERVICE_RUNNING

            logger.debug(
                f"Service status - installed: {self.service_installed}, "
                f"running: {self.service_running}"
            )

        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
                self.service_installed = False
                self.service_running = False
                logger.warning("Service is not installed")
            else:
                logger.error(f"Error checking service status: {e}")
                self.service_running = False
            return False

    def ensure_service_running(self) -> bool:
        """Ensure the elevated service is running.

        Returns:
            bool: True if the service is running, False otherwise
        """
        if self.service_running:
            return True

        if not self.service_installed:
            logger.info("Service not installed. Installing...")
            if not self.install_service():
                return False

        try:
            import win32serviceutil

            logger.info("Starting service...")
            win32serviceutil.StartService("SystemAdminMCP")
            self.service_running = True
            return True
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False

    def install_service(self) -> bool:
        """Install the elevated service.

        Returns:
            bool: True if installation was successful, False otherwise
        """
        try:
            # Get the path to the Python interpreter
            python_exe = sys.executable
            script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "elevated_service",
                "service.py",
            )

            # Build the command to install the service
            cmd = [
                python_exe,
                script_path,
                "--startup",
                "auto",
                "install",
            ]

            logger.info(f"Installing service with command: {' '.join(cmd)}")

            # Run with UAC elevation
            shell = True
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                shell = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd,
                shell=shell,
                check=True,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.service_installed = True
                logger.info("Service installed successfully")
                return True
            else:
                logger.error(f"Failed to install service: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Service installation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during installation: {e}")
            return False

    def _get_service_status(self) -> dict[str, Any]:
        """Get detailed service status information.

        Returns:
            Dict with service status information
        """
        status = {"installed": False, "running": False, "error": None, "solution": None}

        try:
            # Check if service exists and get its status
            status_info = win32serviceutil.QueryServiceStatus("SystemAdminMCP")
            status["installed"] = True
            status["running"] = status_info[1] == win32service.SERVICE_RUNNING

            if not status["running"]:
                status["error"] = "Service is not running"
                status["solution"] = "Start the service using: net start SystemAdminMCP"

        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
                status["error"] = "System Admin MCP service is not installed"
                status["solution"] = "Install the service using the provided MSI installer"
            else:
                status["error"] = (
                    f"Error checking service status: {win32api.FormatMessage(e.winerror)}"
                )
                status["solution"] = "Verify service installation and permissions"

        return status

    def _connect_to_service(self) -> bool:
        """Establish a connection to the named pipe server.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self.pipe_handle:
            return True

        # Check service status first
        status = self._get_service_status()
        if not status["installed"]:
            logger.error(f"Service not installed: {status['error']}")
            return False

        if not status["running"]:
            logger.warning("Service is not running, attempting to start...")
            try:
                win32serviceutil.StartService("SystemAdminMCP")
                time.sleep(2)  # Give it a moment to start
            except Exception as e:
                logger.error(f"Failed to start service: {e}")
                return False

        try:
            # Try to open the named pipe with a reasonable timeout
            self.pipe_handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,  # No sharing
                None,  # Default security attributes
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_OVERLAPPED,  # Use overlapped I/O for timeouts
                None,  # No template file
            )

            # Set read mode to message mode
            res = win32pipe.SetNamedPipeHandleState(
                self.pipe_handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
            )

            if res is None:
                error = win32api.GetLastError()
                if error == winerror.ERROR_PIPE_BUSY:
                    logger.warning("Pipe is busy, waiting...")
                    if not win32pipe.WaitNamedPipe(PIPE_NAME, 5000):  # 5 second timeout
                        logger.error("Timed out waiting for pipe")
                        return False
                    return self._connect_to_service()
                else:
                    logger.error(f"Failed to set pipe state: {win32api.FormatMessage(error)}")
                    return False

            logger.debug("Successfully connected to service")
            return True

        except pywintypes.error as e:
            error_msg = win32api.FormatMessage(e.winerror)
            logger.error(f"Failed to connect to service: {error_msg}")

            # Provide helpful error messages
            if e.winerror == winerror.ERROR_FILE_NOT_FOUND:
                logger.error("The service pipe was not found. Is the service running?")
            elif e.winerror == winerror.ERROR_ACCESS_DENIED:
                logger.error("Access denied. Make sure you have sufficient privileges.")

            return False

    def _send_request(self, action: str, params: dict[str, Any] = None) -> dict[str, Any]:
        """Send a request to the elevated service via named pipe.

        Args:
            action: The action to perform
            params: Optional parameters for the action

        Returns:
            Dictionary containing the response from the service
        """
        if getattr(self, "_disabled", False):
            return {
                "status": "error",
                "message": "System Admin MCP bridge is disabled. "
                "To re-enable, run: powershell -ExecutionPolicy Bypass -File path\\to\\disable_bridge.ps1 -Revert",
            }

        if not self.service_installed:
            return {
                "status": "error",
                "message": "System Admin MCP service is not installed",
            }

        if not self.service_running:
            # Try to start the service if it's not running
            try:
                win32serviceutil.StartService("SystemAdminMCP")
                time.sleep(2)  # Give the service time to start
                self.service_running = True
            except Exception as e:
                logger.error(f"Failed to start service: {e}")
                return {"status": "error", "message": f"Failed to start service: {e}"}

        if not self.pipe_handle and not self._connect_to_service():
            return {
                "status": "error",
                "error": {
                    "code": "connection_failed",
                    "message": "Failed to connect to the elevated service",
                },
            }

        request = {"command": action, "params": params or {}}

        max_retries = 2
        retry_delay = 1  # seconds

        for attempt in range(max_retries + 1):
            try:
                # Convert request to JSON and ensure it's bytes
                request_data = json.dumps(request).encode("utf-8")

                # Write the request
                win32file.WriteFile(self.pipe_handle, request_data)

                # Read the response
                result, data = win32file.ReadFile(
                    self.pipe_handle,
                    BUFFER_SIZE,
                    None,  # No overlapped I/O for now
                )

                if result != 0:
                    error_msg = win32api.FormatMessage(result)
                    logger.error(f"Error reading from pipe: {error_msg}")
                    return {
                        "status": "error",
                        "error": {
                            "code": "pipe_read_error",
                            "message": f"Failed to read from pipe: {error_msg}",
                        },
                    }

                # Parse and return the response
                response = json.loads(data.decode("utf-8"))
                logger.debug(f"Received response: {json.dumps(response, indent=2)}")
                return response

            except pywintypes.error as e:
                self.pipe_handle = None  # Force reconnect on next attempt

                if attempt < max_retries:
                    logger.warning(
                        f"Error communicating with service (attempt {attempt + 1}/"
                        f"{max_retries}): {win32api.FormatMessage(e.winerror)}"
                    )
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue

                logger.error("Max retries exceeded when communicating with service")
                return {
                    "status": "error",
                    "error": {
                        "code": "communication_error",
                        "message": f"Failed to communicate with service: {win32api.FormatMessage(e.winerror)}",
                    },
                }

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from service: {str(e)}")
                return {
                    "status": "error",
                    "error": {
                        "code": "invalid_response",
                        "message": "Received invalid response from service",
                    },
                }

            except Exception as e:
                logger.exception("Unexpected error in _send_request")
                return {
                    "status": "error",
                    "error": {
                        "code": "unexpected_error",
                        "message": f"An unexpected error occurred: {str(e)}",
                    },
                }

    # Public API methods
    def cleanup(self) -> None:
        """Clean up resources used by the bridge."""
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)
                logger.debug("Closed connection to service")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
            finally:
                self.pipe_handle = None

    # High-level API methods
    def get_system_info(self) -> dict[str, Any]:
        """Get system information from the service.

        Returns:
            Dict containing system information or error details
        """
        response = self._send_request("get_system_info")
        if response.get("status") == "success":
            return response.get("result", {})
        return response

    def ping(self) -> bool:
        """Check if the service is responsive.

        Returns:
            bool: True if service responds to ping, False otherwise
        """
        response = self._send_request("ping")
        return response.get("status") == "success" and response.get("result") == "pong"

    def get_file_owner(self, path: str) -> str:
        """Get the owner of a file.

        Args:
            path: Path to the file (must be a string)

        Returns:
            str: The owner of the file or an error message

        Example:
            >>> bridge = UserBridge()
            >>> owner = bridge.get_file_owner("C:\\Windows\\notepad.exe")
            >>> print(f"File owner: {owner}")
        """
        if not isinstance(path, str) or not path.strip():
            return "Error: Invalid file path"

        response = self._send_request("get_file_owner", {"path": os.path.abspath(path)})

        if response.get("status") == "success":
            return response.get("result", "Unknown owner")

        error = response.get("error", {})
        return f"Error: {error.get('message', 'Failed to get file owner')}"

    def list_volumes(self) -> dict[str, Any]:
        """List all available volumes.

        Returns:
            Dictionary containing volume information
        """
        return self._send_request("list_volumes", {})

    def recover_file(self, source_path: str, destination_path: str) -> dict[str, Any]:
        """Recover a deleted file.

        Args:
            source_path: Path to the deleted file
            destination_path: Where to save the recovered file

        Returns:
            Dictionary with recovery status
        """
        return self._send_request(
            "recover_file",
            {"source": source_path, "destination": destination_path},
        )


# FastMCP 2.10 Server Implementation
class SystemAdminMCP:
    """FastMCP 2.10 compatible server for System Admin MCP."""

    def __init__(self):
        """Initialize the MCP server with a bridge instance."""
        self.bridge = UserBridge()
        self.name = "system-admin-mcp"
        self.version = "1.0.0"
        logger.info(f"Initialized {self.name} v{self.version}")

    async def execute(self, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Dictionary of parameters for the tool

        Returns:
            Dict containing the result or error information
        """
        logger.info(f"Executing tool: {tool_name}")

        # Route the tool to the appropriate bridge method
        handler_name = f"tool_{tool_name}"
        if not hasattr(self, handler_name):
            return {
                "status": "error",
                "error": {
                    "code": "unknown_tool",
                    "message": f"Unknown tool: {tool_name}",
                },
            }

        try:
            handler = getattr(self, handler_name)
            result = await handler(parameters)
            return {"status": "success", "result": result}

        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            return {
                "status": "error",
                "error": {
                    "code": "execution_error",
                    "message": f"Error executing {tool_name}: {str(e)}",
                },
            }

    # Tool implementations
    async def tool_get_file_owner(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get the owner of a file."""
        path = params.get("path")
        if not path or not isinstance(path, str):
            raise ValueError("Missing or invalid 'path' parameter")

        owner = self.bridge.get_file_owner(path)
        return {"path": path, "owner": owner}

    async def tool_list_volumes(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """List all volumes on the system."""
        return self.bridge.list_volumes()

    async def tool_get_disk_usage(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get disk usage information for a path."""
        path = params.get("path")
        if not path or not isinstance(path, str):
            raise ValueError("Missing or invalid 'path' parameter")

        return self.bridge.get_disk_usage(path)

    async def tool_get_process_info(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get information about a running process."""
        pid = params.get("pid")
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("Missing or invalid 'pid' parameter (must be a positive integer)")

        return self.bridge.get_process_info(pid)

    async def tool_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        """Check if the service is responsive."""
        is_alive = self.bridge.ping()
        return {"status": "pong" if is_alive else "error"}


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Test the bridge directly
        print("Testing UserBridge...")
        bridge = UserBridge()
        print(f"Service installed: {bridge.service_installed}")
        print(f"Service running: {bridge.service_running}")

        if bridge.service_running:
            # Test ping
            print("\nPinging service...")
            if bridge.ping():
                print("✓ Service is responsive")

                # Test system info
                print("\nGetting system info...")
                sys_info = bridge.get_system_info()
                if sys_info:
                    print(f"OS: {sys_info.get('os', {}).get('platform', 'Unknown')}")
                    print(f"Python: {sys_info.get('python', {}).get('version', 'Unknown')}")

            # Test file owner
            test_file = os.path.abspath(__file__)
            print(f"\nGetting owner of: {test_file}")
            owner = bridge.get_file_owner(test_file)
            print(f"Owner: {owner}")

            # List volumes
            print("\nListing volumes...")
            volumes = bridge.list_volumes()
            for vol in volumes:
                print(
                    f"- {vol.get('name')}: {vol.get('label', 'No label')} "
                    f"({vol.get('size_gb', 0):.2f} GB)"
                )

    # Run the test
    asyncio.run(main())
