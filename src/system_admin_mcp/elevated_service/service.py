"""Elevated service implementation for System Admin MCP.

This module contains the elevated service that runs with admin privileges
and handles privileged operations. It communicates with the user bridge via
named pipes for secure IPC.
"""

import json
import logging
import os
import sys
import time
from typing import Any

import pywintypes
import win32api
import win32con
import win32event
import win32file
import win32pipe
import win32security
import win32service
import win32serviceutil
import winerror

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(r"C:\ProgramData\SystemAdminMCP\service.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Named pipe configuration
PIPE_NAME = r"\\.\pipe\SystemAdminMCP"
BUFFER_SIZE = 65536  # 64KB buffer for large responses
PIPE_TIMEOUT = 30000  # 30 seconds timeout for pipe operations

# Security attributes for the named pipe
SECURITY_ATTRIBUTES = win32security.SECURITY_ATTRIBUTES()
sd = win32security.GetNamedSecurityInfo(
    ".", win32security.SE_FILE_OBJECT, win32security.DACL_SECURITY_INFORMATION
).GetSecurityDescriptorDacl()

# Allow Everyone to read/write to the pipe
sid_everyone = win32security.ConvertStringSidToSid("S-1-1-0")
sd.AddAccessAllowedAce(
    win32security.ACL_REVISION,
    win32con.FILE_GENERIC_READ | win32con.FILE_GENERIC_WRITE,
    sid_everyone,
)

SECURITY_ATTRIBUTES.SECURITY_DESCRIPTOR = win32security.GetSecurityInfo(
    None, win32security.SE_KERNEL_OBJECT, win32security.DACL_SECURITY_INFORMATION
).GetSecurityDescriptorDacl()


class ElevatedService(win32serviceutil.ServiceFramework):
    """Windows Service that runs with elevated privileges.

    This service handles privileged operations on behalf of the user bridge.
    It runs with SYSTEM privileges and exposes a secure named pipe for IPC.
    """

    _svc_name_ = "SystemAdminMCP"
    _svc_display_name_ = "System Admin MCP Service"
    _svc_description_ = "Handles elevated system operations for System Admin MCP"
    _svc_deps_ = ["EventLog"]  # type: ignore  # noqa: RUF012

    def __init__(self, args):
        """Initialize the service with proper error handling."""
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.halt_event = win32event.CreateEvent(None, 0, 0, None)
            self.pipe_handle = None
            self.running = False
            self._setup_logging()
            logger.info("Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize service: {e!s}")
            raise

    def SvcStop(self):
        """Stop the service gracefully.

        Sets the stop event and cleans up resources.
        """
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        if self.halt_event:
            win32event.SetEvent(self.halt_event)
        if self.pipe_handle:
            try:
                win32file.FlushFileBuffers(self.pipe_handle)
                win32pipe.DisconnectNamedPipe(self.pipe_handle)
                win32file.CloseHandle(self.pipe_handle)
                self.pipe_handle = None
            except Exception as e:
                logger.error(f"Error cleaning up pipe: {e!s}")
        logger.info("Service stopped")

    def SvcDoRun(self):
        """Main service loop.

        Handles the main service execution, including error recovery
        and proper service status reporting.
        """
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.running = True
            self._create_pipe()
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            logger.info("Service started and running")

            while self.running:
                try:
                    self._run_pipe_server()
                except pywintypes.error as e:
                    if e.winerror == winerror.ERROR_BROKEN_PIPE:
                        logger.warning("Client disconnected")
                        continue
                    logger.exception("Pipe server error")
                    time.sleep(1)  # Prevent tight loop on errors
                except Exception:
                    logger.exception("Unexpected error in pipe server")
                    time.sleep(5)  # Back off on critical errors

        except Exception:
            logger.exception("Fatal service error")
            self.SvcStop()
            raise
        finally:
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            logger.info("Service execution completed")

    def _create_pipe(self) -> None:
        """Create and configure the named pipe with proper security settings."""
        try:
            # Create the named pipe
            self.pipe_handle = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                win32pipe.PIPE_UNLIMITED_INSTANCES,
                BUFFER_SIZE,  # Output buffer size
                BUFFER_SIZE,  # Input buffer size
                PIPE_TIMEOUT,  # Default timeout
                SECURITY_ATTRIBUTES,
            )
            logger.info(f"Created named pipe: {PIPE_NAME}")
        except Exception as e:
            logger.error(f"Failed to create named pipe: {e!s}")
            raise

    def _run_pipe_server(self) -> None:
        """Run one iteration of the pipe server.

        Handles a single client connection and processes one request.
        """
        if not self.pipe_handle:
            self._create_pipe()

        try:
            # Wait for a client to connect with timeout
            logger.debug("Waiting for client connection...")
            win32pipe.ConnectNamedPipe(self.pipe_handle, None)
            logger.info("Client connected to pipe")

            # Read the request
            try:
                result, data = win32file.ReadFile(
                    self.pipe_handle,
                    BUFFER_SIZE,
                    None,  # No overlapped I/O for now
                )

                if result != 0:
                    raise RuntimeError(f"Failed to read from pipe: {win32api.FormatMessage(result)}")

                request = json.loads(data.decode("utf-8"))
                logger.debug(f"Received request: {json.dumps(request, indent=2)}")

                # Process the request
                response = self._handle_request(request)

                # Send the response
                response_data = json.dumps(response).encode("utf-8")
                win32file.WriteFile(self.pipe_handle, response_data)
                logger.debug("Response sent successfully")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e!s}")
                self._send_error("invalid_json", "Invalid JSON format")
            except Exception as e:
                logger.exception("Error processing request")
                self._send_error("processing_error", str(e))

        except pywintypes.error as e:
            if e.winerror != winerror.ERROR_NO_DATA:  # Ignore client disconnect
                logger.error(f"Pipe error: {win32api.FormatMessage(e.winerror)}")
            raise
        finally:
            # Clean up the pipe for the next connection
            if self.pipe_handle:
                try:
                    win32file.FlushFileBuffers(self.pipe_handle)
                    win32pipe.DisconnectNamedPipe(self.pipe_handle)
                    win32file.CloseHandle(self.pipe_handle)
                    self.pipe_handle = None
                except Exception:
                    logger.exception("Error cleaning up pipe")
                    self.pipe_handle = None  # Force recreation on next iteration

    def _setup_logging(self) -> None:
        """Configure logging for the service."""
        log_dir = r"C:\ProgramData\SystemAdminMCP"
        os.makedirs(log_dir, exist_ok=True)

        # Set up file handler
        file_handler = logging.FileHandler(os.path.join(log_dir, "service.log"), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)

        # Log to console when running interactively
        if sys.stderr:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            root_logger.addHandler(console_handler)

    def _send_error(self, error_code: str, message: str) -> None:
        """Send an error response to the client.

        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
        """
        if not self.pipe_handle:
            return

        try:
            response = {
                "status": "error",
                "error": {"code": error_code, "message": message},
            }
            win32file.WriteFile(self.pipe_handle, json.dumps(response).encode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to send error response: {e!s}")

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a request from the client.

        Args:
            request: The request from the client with 'command' and 'params' keys.

        Returns:
            Dict containing the response with 'status' and result/error information.

        Raises:
            Exception: For unhandled errors that should be logged and returned to the client.
        """
        try:
            if not isinstance(request, dict):
                raise ValueError("Invalid request: expected a dictionary")

            command = request.get("command")
            if not command:
                raise ValueError("Missing 'command' in request")

            params = request.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("'params' must be a dictionary")

            logger.info(f"Processing command: {command}")

            # Route the command to the appropriate handler
            handler_name = f"_handle_{command}"
            if not hasattr(self, handler_name):
                raise ValueError(f"Unknown command: {command}")

            handler = getattr(self, handler_name)
            result = handler(**params)

            return {"status": "success", "result": result}

        except Exception as e:
            logger.exception(f"Error handling command: {command}")
            return {
                "status": "error",
                "error": {"code": "command_error", "message": str(e)},
            }

    # Command handlers
    def _handle_ping(self) -> str:
        """Handle ping command (for testing)."""
        return "pong"

    def _handle_get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return {
            "os": {
                "name": os.name,
                "platform": sys.platform,
                "version": sys.getwindowsversion()._asdict(),
            },
            "python": {"version": sys.version, "executable": sys.executable},
            "service": {
                "name": self._svc_name_,
                "display_name": self._svc_display_name_,
                "description": self._svc_description_,
            },
        }

    def _handle_get_file_owner(self, path: str) -> str:
        """Get the owner of a file."""
        from . import file_ops  # Import here to avoid circular imports

        return file_ops.get_file_owner(path)

    def _handle_list_volumes(self) -> list[str]:
        """List available volumes."""
        from . import volume_ops

        return volume_ops.list_volumes()

    def _handle_recover_file(self, source: str, destination: str) -> bool:
        """Recover a file."""
        from . import file_ops

        return file_ops.recover_file(source, destination)


def main() -> None:
    """Entry point for running the service.

    Handles both service registration/management and direct execution.
    """
    import servicemanager

    # Ensure required directories exist
    os.makedirs(r"C:\ProgramData\SystemAdminMCP", exist_ok=True)

    if len(sys.argv) == 1:
        # Run as a service
        try:
            logger.info("Starting service in service mode")
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(ElevatedService)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception:
            logger.exception("Service failed to start")
            raise
    else:
        # Handle command line arguments
        logger.info(f"Running with arguments: {sys.argv[1:]}")
        try:
            win32serviceutil.HandleCommandLine(ElevatedService)
        except Exception as e:
            logger.exception("Command line handling failed")
            print(f"Error: {e!s}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
