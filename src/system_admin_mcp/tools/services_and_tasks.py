"""Windows Services, Tasks, Startup, and Taskbar management implementations."""

import ctypes
import logging
import os
import struct
import subprocess
import time
import winreg
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as _futures_wait
from ctypes import wintypes
from typing import Annotated, Any

import psutil
import win32service
import win32serviceutil
from pydantic import Field

from system_admin_mcp.app import mcp

logger = logging.getLogger(__name__)

from mcp.types import ToolAnnotations

# Fleet tool-annotation standard (TOOL_DESIGN_STANDARDS.md S9).
_READ_ONLY = ToolAnnotations(readOnlyHint=True)
_MUTATING = ToolAnnotations()
_DESTRUCTIVE = ToolAnnotations(destructiveHint=True)

# Per-process probing runs in a per-call pool so wedged syscalls
# (observed 2026-09-29: psutil status()/memory_info() hang forever on
# transient pids, once froze the whole single-worker event loop via
# /api/processes) cost a bounded wait, not the server. A shared pool
# would exhaust its threads on stuck probes across requests; a per-call
# pool is always fresh. Hung pids are skipped for _HUNG_PID_TTL_S.
_PROC_POOL_WORKERS = 32
_PROC_TOTAL_BUDGET_S = 15.0
_CANARY_TIMEOUT_S = 3.0
_CANARY_SAMPLES = 5
_CANARY_MIN_OK = 4
_HUNG_PID_TTL_S = 600.0
_hung_pids: dict[int, float] = {}


def is_admin() -> bool:
    """Check if running as administrator."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


# ============================================================================
# WINDOWS SERVICES OPERATIONS
# ============================================================================


def _get_service_status_name(status_code: int) -> str:
    """Convert service status code to readable name."""
    status_map = {
        win32service.SERVICE_STOPPED: "Stopped",
        win32service.SERVICE_START_PENDING: "Start Pending",
        win32service.SERVICE_STOP_PENDING: "Stop Pending",
        win32service.SERVICE_RUNNING: "Running",
        win32service.SERVICE_CONTINUE_PENDING: "Continue Pending",
        win32service.SERVICE_PAUSE_PENDING: "Pause Pending",
        win32service.SERVICE_PAUSED: "Paused",
    }
    return status_map.get(status_code, f"Unknown ({status_code})")


def _get_startup_type_name(startup_type: int) -> str:
    """Convert startup type code to readable name."""
    startup_map = {
        win32service.SERVICE_AUTO_START: "Automatic",
        win32service.SERVICE_DEMAND_START: "Manual",
        win32service.SERVICE_DISABLED: "Disabled",
        win32service.SERVICE_BOOT_START: "Boot",
        win32service.SERVICE_SYSTEM_START: "System",
    }
    return startup_map.get(startup_type, f"Unknown ({startup_type})")


def list_services(
    filter_status: Annotated[str | None, Field(description='Filter by status ("running", "stopped", "all")')] = None,
    filter_name: Annotated[str | None, Field(description="Filter by service name (partial match)")] = None,
    include_system: Annotated[bool, Field(description="Include system services")] = True,
    page: Annotated[int, Field(description="Page number (1-based)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="Items per page", ge=1)] = 50,
) -> dict[str, Any]:
    """List Windows services with filtering and pagination.

    Returns a dictionary with the services list.
    """
    try:
        if not is_admin():
            return {
                "status": "error",
                "operation": "list_services",
                "error": "Administrator privileges required",
            }

        services = []
        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)

        try:
            services_list = win32service.EnumServicesStatus(manager)

        finally:
            win32service.CloseServiceHandle(manager)

        for service_name, display_name, _ in services_list:
            if not include_system and service_name.startswith(("Win", "W32", "Rpc", "Net", "Sys")):
                continue

            if filter_name and filter_name.lower() not in service_name.lower():
                if filter_name.lower() not in display_name.lower():
                    continue

            try:
                status_info = win32serviceutil.QueryServiceStatus(service_name)
                status_code = status_info[1]
                status_name = _get_service_status_name(status_code)
            except Exception:
                status_code = win32service.SERVICE_STOPPED
                status_name = "Unknown"

            if filter_status and filter_status != "all":
                if filter_status == "running" and status_code != win32service.SERVICE_RUNNING:
                    continue
                if filter_status == "stopped" and status_code != win32service.SERVICE_STOPPED:
                    continue

            try:
                config = win32serviceutil.QueryServiceConfig(service_name)  # type: ignore[reportAttributeAccessIssue]
                startup_type = config[1]
                startup_name = _get_startup_type_name(startup_type)
            except Exception:
                startup_type = win32service.SERVICE_DEMAND_START
                startup_name = "Unknown"

            services.append(
                {
                    "name": service_name,
                    "display_name": display_name,
                    "status": status_name,
                    "status_code": status_code,
                    "startup_type": startup_name,
                    "startup_code": startup_type,
                }
            )

        total = len(services)
        start = (page - 1) * page_size
        end = start + page_size
        page_services = services[start:end]

        return {
            "status": "success",
            "operation": "list_services",
            "services": page_services,
            "count": len(page_services),
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    except Exception as e:
        logger.exception("Error listing services")
        return {"status": "error", "operation": "list_services", "error": str(e)}


def get_service_stats() -> dict[str, Any]:
    """Get statistics about Windows services.

    Returns:
        Dictionary with service statistics
    """
    try:
        if not is_admin():
            return {
                "status": "error",
                "operation": "get_service_stats",
                "error": "Administrator privileges required",
            }

        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)

        try:
            services_list = win32service.EnumServicesStatus(manager)
            total = len(services_list)

            running = 0
            stopped = 0
            auto_start = 0
            manual_start = 0
            disabled = 0

            for service_name, _, _ in services_list:
                try:
                    status_info = win32serviceutil.QueryServiceStatus(service_name)
                    status_code = status_info[1]

                    if status_code == win32service.SERVICE_RUNNING:
                        running += 1
                    elif status_code == win32service.SERVICE_STOPPED:
                        stopped += 1

                    config = win32serviceutil.QueryServiceConfig(service_name)  # type: ignore[reportAttributeAccessIssue]
                    startup_type = config[1]

                    if startup_type == win32service.SERVICE_AUTO_START:
                        auto_start += 1
                    elif startup_type == win32service.SERVICE_DEMAND_START:
                        manual_start += 1
                    elif startup_type == win32service.SERVICE_DISABLED:
                        disabled += 1
                except Exception:
                    logger.debug("skipping process/service entry after query failure", exc_info=True)
                    continue

        finally:
            win32service.CloseServiceHandle(manager)

        return {
            "status": "success",
            "operation": "get_service_stats",
            "total_services": total,
            "running": running,
            "stopped": stopped,
            "automatic_startup": auto_start,
            "manual_startup": manual_start,
            "disabled": disabled,
        }

    except Exception as e:
        logger.exception("Error getting service stats")
        return {"status": "error", "operation": "get_service_stats", "error": str(e)}


def start_service(
    service_name: Annotated[str, Field(description="Name of the service to start")],
    wait_timeout: Annotated[int, Field(description="Max seconds to wait for start", ge=1)] = 30,
) -> dict[str, Any]:
    """Start a Windows service.

    Returns a dictionary with the operation result.
    """
    try:
        if not is_admin():
            return {
                "status": "error",
                "operation": "start_service",
                "error": "Administrator privileges required",
            }

        win32serviceutil.StartService(service_name)

        # Wait for service to start
        start_time = time.time()
        while time.time() - start_time < wait_timeout:
            try:
                status_info = win32serviceutil.QueryServiceStatus(service_name)
                status_code = status_info[1]

                if status_code == win32service.SERVICE_RUNNING:
                    return {
                        "status": "success",
                        "operation": "start_service",
                        "service_name": service_name,
                        "message": "Service started successfully",
                    }

                if status_code == win32service.SERVICE_STOPPED:
                    return {
                        "status": "error",
                        "operation": "start_service",
                        "error": "Service failed to start",
                    }

                time.sleep(1)
            except Exception:
                time.sleep(1)

        return {
            "status": "error",
            "operation": "start_service",
            "error": f"Service start timed out after {wait_timeout} seconds",
        }

    except Exception as e:
        logger.exception(f"Error starting service {service_name}")
        return {"status": "error", "operation": "start_service", "error": str(e)}


def stop_service(
    service_name: Annotated[str, Field(description="Name of the service to stop")],
    wait_timeout: Annotated[int, Field(description="Max seconds to wait for stop", ge=1)] = 30,
) -> dict[str, Any]:
    """Stop a Windows service.

    Returns a dictionary with the operation result.
    """
    try:
        if not is_admin():
            return {
                "status": "error",
                "operation": "stop_service",
                "error": "Administrator privileges required",
            }

        win32serviceutil.StopService(service_name)

        # Wait for service to stop
        start_time = time.time()
        while time.time() - start_time < wait_timeout:
            try:
                status_info = win32serviceutil.QueryServiceStatus(service_name)
                status_code = status_info[1]

                if status_code == win32service.SERVICE_STOPPED:
                    return {
                        "status": "success",
                        "operation": "stop_service",
                        "service_name": service_name,
                        "message": "Service stopped successfully",
                    }

                time.sleep(1)
            except Exception:
                time.sleep(1)

        return {
            "status": "error",
            "operation": "stop_service",
            "error": f"Service stop timed out after {wait_timeout} seconds",
        }

    except Exception as e:
        logger.exception(f"Error stopping service {service_name}")
        return {"status": "error", "operation": "stop_service", "error": str(e)}


def get_service_info(service_name: Annotated[str, Field(description="Name of the service to query")]) -> dict[str, Any]:
    """Get detailed information about a Windows service.

    Returns a dictionary with service details.
    """
    try:
        if not is_admin():
            return {
                "status": "error",
                "operation": "get_service_info",
                "error": "Administrator privileges required",
            }

        service_info = {}
        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)

        try:
            handle = win32service.OpenService(
                manager,
                service_name,
                win32service.SERVICE_QUERY_CONFIG | win32service.SERVICE_QUERY_STATUS,
            )

            # Implementation...
            status = win32service.QueryServiceStatusEx(handle)
            config = win32service.QueryServiceConfig(handle)

            service_info = {
                "name": service_name,
                "display_name": config[2],
                "status": _get_service_status_name(status["CurrentState"]),  # type: ignore[reportArgumentType]
                "startup_type": _get_startup_type_name(config[1]),
                "binary_path": config[3],
                "account": config[6],
                "pid": status["ProcessId"],  # type: ignore[reportArgumentType]
            }

            return {"status": "success", "service": service_info}
        finally:
            win32service.CloseServiceHandle(manager)
    except Exception as e:
        logger.exception(f"Error getting service info for {service_name}")
        return {"status": "error", "operation": "get_service_info", "error": str(e)}


def set_service_startup(
    service_name: Annotated[str, Field(description="Name of the service")],
    startup_type: Annotated[str, Field(description='Startup type ("automatic", "manual", "disabled)')],
) -> dict[str, Any]:
    """Set service startup type.

    Returns a dictionary with the operation result.
    """
    try:
        if not is_admin():
            return {
                "status": "error",
                "operation": "set_service_startup",
                "error": "Administrator privileges required",
            }

        startup_map = {
            "automatic": win32service.SERVICE_AUTO_START,
            "manual": win32service.SERVICE_DEMAND_START,
            "disabled": win32service.SERVICE_DISABLED,
        }

        if startup_type.lower() not in startup_map:
            return {
                "status": "error",
                "operation": "set_service_startup",
                "error": f"Invalid startup type: {startup_type}. Must be 'automatic', 'manual', or 'disabled'",
            }

        win32serviceutil.ChangeServiceConfig(  # type: ignore[reportArgumentType]
            service_name,
            None,  # service type
            startup_map[startup_type.lower()],
            None,  # error control
            None,  # binary path  # type: ignore[reportArgumentType]
            None,  # load order group
            None,  # tag id
            None,  # dependencies
            None,  # account
            None,  # password
            None,  # display name
        )

        return {
            "status": "success",
            "operation": "set_service_startup",
            "service_name": service_name,
            "startup_type": startup_type,
        }

    except Exception as e:
        logger.exception(f"Error setting service startup for {service_name}")
        return {"status": "error", "operation": "set_service_startup", "error": str(e)}


# ============================================================================
# TASKS/PROCESSES OPERATIONS
# ============================================================================


def _probe_process_safe(pid: int) -> dict[str, Any] | None:
    """Safe-tier probe: pid/name/username only.

    Measured 2026-09-29 on a box where 768/1041 pids wedge psutil's heavy
    per-process syscalls (status/memory_info/cpu_times/create_time): the
    name/username family completes for ALL pids. Never add a heavy call
    here without re-measuring first.
    """
    try:
        proc = psutil.Process(pid)
        return {
            "pid": pid,
            "name": proc.name(),
            "username": proc.username(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def _probe_process_heavy(pid: int) -> dict[str, Any] | None:
    """Heavy-tier probe: status/memory/cpu/create_time. May wedge per pid."""
    try:
        proc = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
    try:
        # oneshot batches the per-process syscalls into one shot:
        # fewer kernel round-trips per proc, smaller hang surface.
        with proc.oneshot():
            return {
                "cpu_percent": proc.cpu_percent(interval=0),
                "memory_info": proc.memory_info()._asdict(),
                "status": proc.status(),
                "create_time": proc.create_time(),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def _psutil_heavy_ok(pool: ThreadPoolExecutor, pids: list[int]) -> bool:
    """Canary: heavy-probe a small pid sample through the heavy syscall family.

    A single self-probe is not representative — measured 2026-09-29 with
    self passing while 600+ other pids wedged. Sample several pids in
    parallel; proceed only when nearly all succeed. Costs <= _CANARY_TIMEOUT_S.
    """
    if not pids:
        return True
    step = max(1, len(pids) // _CANARY_SAMPLES)
    sample = pids[::step][:_CANARY_SAMPLES]
    futures = {pool.submit(_probe_process_heavy, pid): pid for pid in sample}
    try:
        done, not_done = _futures_wait(futures.keys(), timeout=_CANARY_TIMEOUT_S)
        ok = 0
        for future in done:
            try:
                if future.result(timeout=0) is not None:
                    ok += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                ok += 1  # exited/masked pid: query path itself works
            except Exception:
                logger.debug("process query future failed; excluding from count", exc_info=True)
        for future in not_done:
            future.cancel()
        return ok >= min(_CANARY_MIN_OK, len(sample))
    except Exception:
        return False


def list_processes(
    filter_name: Annotated[str | None, Field(description="Filter by process name (partial match)")] = None,
    filter_user: Annotated[str | None, Field(description="Filter by username")] = None,
    sort_by: Annotated[str, Field(description='Sort by "cpu", "memory", "name", or "pid"')] = "cpu",
    page: Annotated[int, Field(description="Page number (1-based)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="Items per page", ge=1)] = 50,
) -> dict[str, Any]:
    """List running processes with filtering, sorting, and pagination.

    Returns a dictionary with the processes list, count, page, and page_size.
    """
    try:
        processes = []
        degraded = False
        degraded_reason = ""
        now = time.monotonic()
        # Drop expired hang-skips so a recovered pid rejoins automatically.
        for pid in [p for p, ts in _hung_pids.items() if now - ts > _HUNG_PID_TTL_S]:
            del _hung_pids[pid]

        # pids() is one syscall with no per-process queries — unlike
        # process_iter(attrs) + proc.info, it cannot hang on a wedged proc.
        pids = [pid for pid in psutil.pids() if pid not in _hung_pids]

        # Fresh pool per call: a shared pool would exhaust its threads on
        # stuck probes across requests. Never `with` it — context exit waits
        # for stuck threads forever; shutdown(wait=False) instead.
        pool = ThreadPoolExecutor(max_workers=_PROC_POOL_WORKERS, thread_name_prefix="proc-probe")
        try:
            # Tier 1 (safe): pid/name/username complete even when heavy
            # per-process syscalls wedge box-wide.
            safe_futures = {pool.submit(_probe_process_safe, pid): pid for pid in pids}
            safe_done, safe_not_done = _futures_wait(safe_futures.keys(), timeout=_PROC_TOTAL_BUDGET_S)
            for future in safe_not_done:
                pid = safe_futures[future]
                future.cancel()
                _hung_pids[pid] = time.monotonic()
            by_pid: dict[int, dict[str, Any]] = {}
            for future in safe_done:
                try:
                    info = future.result(timeout=0)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception:
                    logger.debug("skipping process/service entry after query failure", exc_info=True)
                    continue
                if info is not None:
                    by_pid[info["pid"]] = info

            # Tier 2 (heavy): gated by a sampled canary. When the environment is
            # wedging heavy queries, skip the pass entirely (degraded) rather
            # than burning the full budget on hundreds of stuck probes.
            if _psutil_heavy_ok(pool, pids):
                heavy_skipped = 0
                heavy_futures = {pool.submit(_probe_process_heavy, pid): pid for pid in by_pid}
                heavy_done, heavy_not_done = _futures_wait(heavy_futures.keys(), timeout=_PROC_TOTAL_BUDGET_S)
                for future in heavy_done:
                    pid = heavy_futures[future]
                    try:
                        heavy = future.result(timeout=0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        by_pid.pop(pid, None)
                        continue
                    except Exception:
                        logger.debug("heavy process query failed for pid %s; dropping entry", pid, exc_info=True)
                        by_pid.pop(pid, None)
                        continue
                    if heavy is None:
                        by_pid.pop(pid, None)
                    else:
                        by_pid[pid].update(heavy)
                for future in heavy_not_done:
                    pid = heavy_futures[future]
                    future.cancel()
                    heavy_skipped += 1
                    _hung_pids[pid] = time.monotonic()
                    by_pid.pop(pid, None)
                if heavy_skipped:
                    degraded = True
                    degraded_reason = (
                        f"{heavy_skipped} pids unqueryable for status/memory on this host; "
                        "returning pid/name/username for the rest"
                    )
                    logger.warning("list_processes: %s", degraded_reason)
            else:
                degraded = True
                degraded_reason = (
                    "per-process status/memory queries are wedged on this host; returning pid/name/username only"
                )
                logger.warning("list_processes: %s", degraded_reason)

            for proc_info in by_pid.values():
                if filter_name and filter_name.lower() not in proc_info["name"].lower():
                    continue
                if filter_user and proc_info.get("username") != filter_user:
                    continue
                processes.append(proc_info)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        if sort_by == "cpu":
            processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x.get("memory_percent", 0), reverse=True)
        elif sort_by == "name":
            processes.sort(key=lambda x: x.get("name", "").lower())
        elif sort_by == "pid":
            processes.sort(key=lambda x: x.get("pid", 0))

        total = len(processes)
        start = (page - 1) * page_size
        end = start + page_size
        page_procs = processes[start:end]

        return {
            "status": "success",
            "operation": "list_processes",
            "processes": page_procs,
            "count": len(page_procs),
            "total": total,
            "page": page,
            "page_size": page_size,
            "degraded": degraded,
            "degraded_reason": degraded_reason,
        }

    except Exception as e:
        logger.exception("Error listing processes")
        return {"status": "error", "operation": "list_processes", "error": str(e)}


def analyze_process(pid: Annotated[int, Field(description="Process ID")]) -> dict[str, Any]:
    """Analyze a specific process in detail including CPU, Memory, and IO metrics."""
    try:
        process = psutil.Process(pid)

        with process.oneshot():
            info = {
                "pid": process.pid,
                "name": process.name(),
                "exe": process.exe(),
                "cmdline": process.cmdline(),
                "status": process.status(),
                "create_time": process.create_time(),
                "username": process.username(),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_info": process.memory_info()._asdict(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_handles": process.num_handles(),
                "io_counters": process.io_counters()._asdict() if process.io_counters() else None,
                "cpu_affinity": process.cpu_affinity(),
                "nice": process.nice(),
                "ppid": process.ppid(),
                "parent": process.parent().pid if process.parent() else None,  # type: ignore[reportAttributeAccessIssue]
                "children": [p.pid for p in process.children(recursive=False)],
                "connections": [
                    {
                        "fd": conn.fd,
                        "family": str(conn.family),
                        "type": str(conn.type),
                        "laddr": conn.laddr,
                        "raddr": conn.raddr,
                        "status": conn.status,
                    }
                    for conn in process.connections()
                ],
            }

        return {
            "status": "success",
            "operation": "analyze_process",
            "process": info,
        }

    except psutil.NoSuchProcess:
        return {
            "status": "error",
            "operation": "analyze_process",
            "error": f"Process with PID {pid} not found",
        }
    except Exception as e:
        logger.exception(f"Error analyzing process {pid}")
        return {"status": "error", "operation": "analyze_process", "error": str(e)}


def kill_process(
    pid: Annotated[int, Field(description="Process ID")],
    force: Annotated[bool, Field(description="If True, force kill (SIGKILL equivalent)")] = False,
) -> dict[str, Any]:
    """Kill a process.

    Returns a dictionary with the operation result.
    """
    try:
        process = psutil.Process(pid)
        process_name = process.name()

        if force:
            process.kill()
        else:
            process.terminate()

        # Wait for process to terminate
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            # Force kill if terminate didn't work
            process.kill()
            process.wait(timeout=5)

        return {
            "status": "success",
            "operation": "kill_process",
            "pid": pid,
            "process_name": process_name,
            "force": force,
        }

    except psutil.NoSuchProcess:
        return {
            "status": "error",
            "operation": "kill_process",
            "error": f"Process with PID {pid} not found",
        }
    except psutil.AccessDenied:
        return {
            "status": "error",
            "operation": "kill_process",
            "error": f"Access denied - cannot kill process {pid}",
        }
    except Exception as e:
        logger.exception(f"Error killing process {pid}")
        return {"status": "error", "operation": "kill_process", "error": str(e)}


# ============================================================================
# WINDOWS STARTUP OPERATIONS
# ============================================================================


@mcp.tool(annotations=_READ_ONLY)
def list_startup_programs() -> dict[str, Any]:
    """List programs that start with Windows.

    Returns:
        Dictionary with startup programs list
    """
    try:
        startup_programs = []

        # Check registry locations for startup programs
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]

        for hkey, path in registry_paths:
            try:
                key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
                try:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_programs.append(
                                {
                                    "name": name,
                                    "command": value,
                                    "location": "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM",
                                    "path": path,
                                }
                            )
                            i += 1
                        except OSError:
                            break
                finally:
                    winreg.CloseKey(key)
            except Exception:
                logger.debug("skipping registry/service entry after query failure", exc_info=True)
                continue

        # Also check Startup folder
        startup_folder = os.path.join(
            os.environ.get("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        if os.path.exists(startup_folder):
            for item in os.listdir(startup_folder):
                item_path = os.path.join(startup_folder, item)
                if os.path.isfile(item_path):
                    startup_programs.append(
                        {
                            "name": item,
                            "command": item_path,
                            "location": "Startup Folder",
                            "path": startup_folder,
                        }
                    )

        return {
            "status": "success",
            "operation": "list_startup_programs",
            "programs": startup_programs,
            "count": len(startup_programs),
        }

    except Exception as e:
        logger.exception("Error listing startup programs")
        return {"status": "error", "operation": "list_startup_programs", "error": str(e)}


@mcp.tool(annotations=_DESTRUCTIVE)
def add_startup_program(
    name: Annotated[str, Field(description="Program name")],
    command: Annotated[str, Field(description="Command to execute")],
    location: Annotated[str, Field(description='"HKCU" (current user) or "HKLM" (all users, requires admin)')] = "HKCU",
) -> dict[str, Any]:
    """Add a program to Windows startup.

    ## Return Format
    `{status: "success" | "error", ...}` with the operation result.

    ## Examples
    ```python
    add_startup_program("MyApp", "C:\\Apps\\app.exe")
    ```
    """
    try:
        if location == "HKLM" and not is_admin():
            return {
                "status": "error",
                "operation": "add_startup_program",
                "error": "Administrator privileges required for HKLM",
            }

        hkey = winreg.HKEY_CURRENT_USER if location == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        key = winreg.OpenKey(hkey, path, 0, winreg.KEY_WRITE)
        try:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
        finally:
            winreg.CloseKey(key)

        return {
            "status": "success",
            "operation": "add_startup_program",
            "name": name,
            "command": command,
            "location": location,
        }

    except Exception as e:
        logger.exception(f"Error adding startup program {name}")
        return {"status": "error", "operation": "add_startup_program", "error": str(e)}


@mcp.tool(annotations=_DESTRUCTIVE)
def remove_startup_program(
    name: Annotated[str, Field(description="Program name")],
    location: Annotated[str, Field(description='"HKCU" (current user) or "HKLM" (all users, requires admin)')] = "HKCU",
) -> dict[str, Any]:
    """Remove a program from Windows startup.

    ## Return Format
    `{status: "success" | "error", ...}` with the operation result.

    ## Examples
    ```python
    remove_startup_program("MyApp")
    ```
    """
    try:
        if location == "HKLM" and not is_admin():
            return {
                "status": "error",
                "operation": "remove_startup_program",
                "error": "Administrator privileges required for HKLM",
            }

        hkey = winreg.HKEY_CURRENT_USER if location == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        key = winreg.OpenKey(hkey, path, 0, winreg.KEY_WRITE)
        try:
            winreg.DeleteValue(key, name)
        finally:
            winreg.CloseKey(key)

        return {
            "status": "success",
            "operation": "remove_startup_program",
            "name": name,
            "location": location,
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "operation": "remove_startup_program",
            "error": f"Startup program '{name}' not found",
        }
    except Exception as e:
        logger.exception(f"Error removing startup program {name}")
        return {"status": "error", "operation": "remove_startup_program", "error": str(e)}


# ============================================================================
# TASKBAR OPERATIONS
# ============================================================================


@mcp.tool(annotations=_READ_ONLY)
def get_taskbar_settings() -> dict[str, Any]:
    """Get current taskbar settings.

    Returns:
        Dictionary with taskbar settings
    """
    try:
        # Read taskbar settings from registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3",
            0,
            winreg.KEY_READ,
        )

        try:
            settings = winreg.QueryValueEx(key, "Settings")[0]
            # Settings is a binary blob, parse it
            # Byte 8 (0-indexed) contains autohide flag
            autohide = bool(settings[8] & 0x01) if len(settings) > 8 else False
            lock_taskbar = bool(settings[8] & 0x02) if len(settings) > 8 else False

            return {
                "status": "success",
                "operation": "get_taskbar_settings",
                "autohide": autohide,
                "lock_taskbar": lock_taskbar,
            }
        finally:
            winreg.CloseKey(key)

    except Exception as e:
        logger.exception("Error getting taskbar settings")
        return {"status": "error", "operation": "get_taskbar_settings", "error": str(e)}


@mcp.tool(annotations=_MUTATING)
def set_taskbar_autohide(
    enabled: Annotated[bool, Field(description="True to enable autohide, False to disable")],
) -> dict[str, Any]:
    """Set taskbar autohide setting.

    ## Return Format
    `{status: "success" | "error", ...}` with the operation result.

    ## Examples
    ```python
    set_taskbar_autohide(True)
    ```
    """
    try:
        # Use PowerShell to set taskbar autohide
        ps_script = f"""
        $regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StuckRects3"
        $regName = "Settings"

        try {{
            $settings = Get-ItemProperty -Path $regPath -Name $regName -ErrorAction Stop
            $bytes = $settings.Settings

            # Modify byte 8 (0-indexed) to set autohide flag
            if ($bytes.Length -gt 8) {{
                if ({str(enabled).lower()}) {{
                    $bytes[8] = $bytes[8] -bor 0x01
                }} else {{
                    $bytes[8] = $bytes[8] -band 0xFE
                }}

                Set-ItemProperty -Path $regPath -Name $regName -Value $bytes -Type Binary

                # Restart Explorer to apply changes
                Stop-Process -Name explorer -Force
                Start-Sleep -Seconds 2
                Start-Process explorer

                Write-Output "SUCCESS"
            }} else {{
                Write-Output "ERROR: Invalid settings format"
            }}
        }} catch {{
            Write-Output "ERROR: $($_.Exception.Message)"
        }}
        """

        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if "SUCCESS" in result.stdout:
            return {
                "status": "success",
                "operation": "set_taskbar_autohide",
                "autohide": enabled,
                "message": "Taskbar autohide setting updated. Explorer restarted.",
            }
        else:
            return {
                "status": "error",
                "operation": "set_taskbar_autohide",
                "error": result.stdout.strip() or "Failed to set taskbar autohide",
            }

    except Exception as e:
        logger.exception("Error setting taskbar autohide")
        return {"status": "error", "operation": "set_taskbar_autohide", "error": str(e)}


def find_taskbar_blocking_processes() -> dict[str, Any]:
    """Find processes that prevent taskbar autohide.

    These are typically processes with windows that extend to the screen edge.

    Returns:
        Dictionary with blocking processes
    """
    try:
        blocking_processes = []

        # Get all processes with windows
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                # Check if process has windows
                if not proc.is_running():
                    continue

                # Use Windows API to check for top-level windows
                # Processes with windows that might block taskbar
                # This is a heuristic - we check for processes with visible windows
                try:
                    # Get process handles to check for windows
                    # This is simplified - real detection would require EnumWindows
                    proc_info = {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "exe": proc.exe() if hasattr(proc, "exe") else None,
                    }

                    # Common processes that can block taskbar
                    blocking_names = [
                        "explorer",
                        "dwm",
                        "winlogon",
                        "sihost",
                        "ShellExperienceHost",
                        "SearchUI",
                        "StartMenuExperienceHost",
                    ]

                    if proc.name().lower() in [n.lower() for n in blocking_names]:
                        blocking_processes.append(proc_info)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            except Exception:
                logger.debug("skipping registry/service entry after query failure", exc_info=True)
                continue

        return {
            "status": "success",
            "operation": "find_taskbar_blocking_processes",
            "processes": blocking_processes,
            "count": len(blocking_processes),
            "note": "This is a heuristic list. Use kill_taskbar_blocking_processes to kill specific processes.",
        }

    except Exception as e:
        logger.exception("Error finding taskbar blocking processes")
        return {
            "status": "error",
            "operation": "find_taskbar_blocking_processes",
            "error": str(e),
        }


def kill_taskbar_blocking_processes(
    process_names: Annotated[
        list[str] | None, Field(description="Process names to kill (None kills common blockers)")
    ] = None,
    force: Annotated[bool, Field(description="Force kill processes")] = False,
) -> dict[str, Any]:
    """Kill processes that prevent taskbar autohide.

    Returns a dictionary with the operation result.
    """
    try:
        if process_names is None:
            # Default list of processes that commonly block taskbar
            process_names = [
                "ShellExperienceHost",
                "SearchUI",
                "StartMenuExperienceHost",
            ]

        killed = []
        errors = []

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.name() in process_names:
                    proc.terminate() if not force else proc.kill()
                    killed.append({"pid": proc.pid, "name": proc.name()})
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                errors.append({"name": proc.name(), "error": str(e)})
            except Exception as e:
                errors.append({"name": proc.name(), "error": str(e)})

        return {
            "status": "success",
            "operation": "kill_taskbar_blocking_processes",
            "killed": killed,
            "errors": errors,
            "killed_count": len(killed),
        }

    except Exception as e:
        logger.exception("Error killing taskbar blocking processes")
        return {
            "status": "error",
            "operation": "kill_taskbar_blocking_processes",
            "error": str(e),
        }


def forensic_scan() -> dict[str, Any]:
    """Scan system for suspicious services and processes.

    Flags items based on local heuristics: unusual paths, random-looking names,
    missing descriptions, high resource usage, network connections to uncommon
    ports. Does NOT perform web lookups - use ctx.sample() with the findings
    for LLM-driven analysis.

    Returns:
        Dictionary with flagged services, processes, and network items.
    """
    findings: dict[str, list[dict]] = {
        "suspicious_services": [],
        "suspicious_processes": [],
        "notable_connections": [],
        "resource_hogs": [],
    }

    try:
        # --- Services scan ---
        try:
            manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
            try:
                svc_list = win32service.EnumServicesStatus(manager)
            finally:
                win32service.CloseServiceHandle(manager)

            for svc_name, display_name, _ in svc_list:
                flags = []
                try:
                    config = win32serviceutil.QueryServiceConfig(svc_name)  # type: ignore[reportAttributeAccessIssue]
                    bin_path = config[3] if len(config) > 3 else ""
                except Exception:
                    bin_path = ""

                if bin_path and any(p in bin_path.lower() for p in [r"\temp", r"\tmp", r"\appdata\local\temp"]):
                    flags.append("runs_from_temp")
                if not display_name or display_name == svc_name:
                    flags.append("missing_display_name")
                if not bin_path:
                    flags.append("no_binary_path")
                try:
                    status_info = win32serviceutil.QueryServiceStatus(svc_name)
                    if status_info[1] == win32service.SERVICE_STOPPED:
                        config_info = win32serviceutil.QueryServiceConfig(svc_name)  # type: ignore[reportAttributeAccessIssue]
                        if config_info[1] == win32service.SERVICE_AUTO_START:
                            flags.append("stopped_but_auto_start")
                except Exception:
                    logger.debug("Skipped status query for service %s", svc_name)
                if flags:
                    findings["suspicious_services"].append(
                        {
                            "name": svc_name,
                            "display_name": display_name,
                            "binary_path": bin_path[:120] if bin_path else "",
                            "flags": flags,
                        }
                    )
        except Exception:
            logger.debug("Forensic services scan failed")

        # --- Processes scan ---
        suspicious_paths = [r"\temp", r"\tmp", r"\appdata\local\temp", r"\users\public"]
        for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "exe"]):
            try:
                info = proc.info
                flags = []
                exe = info.get("exe") or ""
                name = info.get("name") or ""

                if exe and any(p in exe.lower() for p in suspicious_paths):
                    flags.append("runs_from_suspicious_path")
                cpu = info.get("cpu_percent") or 0
                mem = info.get("memory_percent") or 0
                if cpu > 50:
                    flags.append("high_cpu")
                    findings["resource_hogs"].append(
                        {
                            "pid": info["pid"],
                            "name": name,
                            "type": "cpu",
                            "value": round(cpu, 1),
                        }
                    )
                if mem > 20:
                    flags.append("high_memory")
                    findings["resource_hogs"].append(
                        {
                            "pid": info["pid"],
                            "name": name,
                            "type": "memory",
                            "value": round(mem, 1),
                        }
                    )
                if flags:
                    findings["suspicious_processes"].append(
                        {
                            "pid": info["pid"],
                            "name": name,
                            "username": info.get("username"),
                            "exe": exe[:120] if exe else "",
                            "cpu": round(cpu, 1),
                            "memory": round(mem, 1),
                            "flags": flags,
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # --- Network connections ---
        uncommon_ports = {22, 23, 3389, 5900, 5901, 4444, 1337, 31337, 6660, 6667}
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                for conn in proc.connections():
                    if conn.raddr and conn.raddr.port in uncommon_ports:
                        findings["notable_connections"].append(
                            {
                                "pid": proc.pid,
                                "process": proc.name(),
                                "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                                "remote": f"{conn.raddr.ip}:{conn.raddr.port}",
                                "status": conn.status,
                            }
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return {
            "status": "success",
            "operation": "forensic_scan",
            "findings": findings,
            "summary": {
                "suspicious_services": len(findings["suspicious_services"]),
                "suspicious_processes": len(findings["suspicious_processes"]),
                "notable_connections": len(findings["notable_connections"]),
                "resource_hogs": len(findings["resource_hogs"]),
            },
        }
    except Exception as e:
        logger.exception("Error during forensic scan")
        return {"status": "error", "operation": "forensic_scan", "error": str(e)}


# ---------------------------------------------------------------------------
# Taskbar windows + notification-area (tray) icons
# ---------------------------------------------------------------------------

_TASKBAR_SKIP_CLASSES = frozenset(
    {
        "ProgMan",
        "WorkerW",
        "Shell_TrayWnd",
        "Shell_SecondaryTrayWnd",
        "NotifyIconOverflowWindow",
        "Windows.UI.Core.CoreWindow",
        "Xaml_WindowedPopupClass",
    }
)

# ToolbarWindow32 control messages (tray icon scraping)
_TB_BUTTONCOUNT = 0x0418
_TB_GETBUTTON = 0x0417
_TB_GETBUTTONTEXTW = 0x044B
_TBBUTTON_SIZE = 32
_TBBUTTON_ISTRING_OFFSET = 24
_TBSTATE_HIDDEN = 0x08

# OpenProcess rights for cross-process toolbar reads (explorer.exe)
_PROCESS_VM_OPERATION = 0x0008
_PROCESS_VM_READ = 0x0010
_PROCESS_VM_WRITE = 0x0020
_PROCESS_QUERY = 0x0400
_MEM_COMMIT_RESERVE = 0x3000
_MEM_RELEASE = 0x8000
_PAGE_READWRITE = 0x04


def _startup_exe_map() -> dict[str, dict[str, Any]]:
    """Map exe basename (lower) -> startup entry for autostart cross-reference."""
    mapping: dict[str, dict[str, Any]] = {}
    try:
        result = list_startup_programs()
        entries = result.get("startup_programs") or result.get("programs") or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            command = str(entry.get("command") or "")
            # First quoted token or first token is usually the executable.
            candidate = command.strip()
            if candidate.startswith('"'):
                candidate = candidate[1:].split('"', 1)[0]
            else:
                candidate = candidate.split(" ", 1)[0].strip().strip('"')
            base = os.path.basename(candidate).lower()
            if base:
                mapping.setdefault(
                    base,
                    {
                        "name": entry.get("name", ""),
                        "location": entry.get("location", ""),
                        "command": command[:260],
                    },
                )
    except Exception:
        logger.debug("startup cross-reference failed", exc_info=True)
    return mapping


def _proc_identity(pid: int) -> tuple[str, str]:
    """Return (process name, exe path) for a pid; empty strings on failure."""
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            return proc.name() or "", proc.exe() or ""
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "", ""
    except Exception:
        logger.debug("process identity failed for pid %s", pid, exc_info=True)
        return "", ""


def _autostart_flag(exe: str, startup_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    base = os.path.basename(exe or "").lower()
    entry = startup_map.get(base) if base else None
    if entry:
        return {"autostart": True, "startup_name": entry["name"], "startup_location": entry["location"]}
    return {"autostart": False, "startup_name": "", "startup_location": ""}


def list_taskbar_windows(
    include_untitled: Annotated[bool, Field(description="Include visible windows with empty titles")] = False,
) -> dict[str, Any]:
    """List visible taskbar windows with owning process and autostart flags.

    Enumerates top-level windows (EnumWindows): only visible, titled, uncloaked
    windows are taskbar buttons. Each entry carries pid/process/exe plus whether
    the owning executable is registered to autostart — the "forgotten app" view.
    """
    user32 = ctypes.windll.user32
    windows: list[dict[str, Any]] = []
    startup_map = _startup_exe_map()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum_proc(hwnd, _lparam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0 and not include_untitled:
                return True
            buf = ctypes.create_unicode_buffer(min(length + 1, 512) if length else 2)
            user32.GetWindowTextW(hwnd, buf, len(buf))
            title = buf.value or ""
            if not title and not include_untitled:
                return True
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            class_name = class_buf.value or ""
            if class_name in _TASKBAR_SKIP_CLASSES:
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            name, exe = _proc_identity(pid.value)
            entry = {
                "hwnd": int(hwnd),
                "title": title[:260],
                "pid": pid.value,
                "process": name,
                "exe": exe,
                "class_name": class_name,
            }
            entry.update(_autostart_flag(exe, startup_map))
            windows.append(entry)
        except Exception:
            logger.debug("taskbar window probe failed", exc_info=True)
        return True

    try:
        user32.EnumWindows(_enum_proc, 0)
    except Exception as e:
        return {"status": "error", "operation": "list_taskbar_windows", "error": str(e)}
    windows.sort(key=lambda w: (w["process"] or "").lower())
    return {"status": "success", "operation": "list_taskbar_windows", "count": len(windows), "windows": windows}


def _find_tray_toolbars() -> list[tuple[int, str]]:
    """Locate notification-area toolbars: (hwnd, area). Best effort."""
    user32 = ctypes.windll.user32
    found: list[tuple[int, str]] = []

    def _child(parent: int, class_name: str) -> int:
        return int(user32.FindWindowExW(parent, 0, class_name, None) or 0)

    tray = int(user32.FindWindowW("Shell_TrayWnd", None) or 0)
    if tray:
        notify = _child(tray, "TrayNotifyWnd")
        if notify:
            # Win11: toolbar directly under TrayNotifyWnd; Win10: via SysPager.
            direct = _child(notify, "ToolbarWindow32")
            if direct:
                found.append((direct, "main"))
            else:
                pager = _child(notify, "SysPager")
                if pager:
                    bar = _child(pager, "ToolbarWindow32")
                    if bar:
                        found.append((bar, "main"))
    overflow = int(user32.FindWindowW("NotifyIconOverflowWindow", None) or 0)
    if overflow:
        bar = _child(overflow, "ToolbarWindow32")
        if bar:
            found.append((bar, "overflow"))
    return found


def _read_tray_buttons(hwnd: int) -> list[dict[str, Any]]:
    """Scrape button tooltips from a ToolbarWindow32 in explorer.exe.

    There is no public API for tray icons; this uses the documented
    TB_BUTTONCOUNT/TB_GETBUTTON/TB_GETBUTTONTEXT control messages with
    cross-process memory. Raises on OpenProcess/virtual-alloc failure so the
    caller can degrade to a partial result with a note.
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    count = int(user32.SendMessageW(hwnd, _TB_BUTTONCOUNT, 0, 0))
    if count <= 0:
        return []
    rights = _PROCESS_VM_OPERATION | _PROCESS_VM_READ | _PROCESS_VM_WRITE | _PROCESS_QUERY
    proc = kernel32.OpenProcess(rights, False, _tray_toolbar_pid(hwnd))
    if not proc:
        raise OSError("OpenProcess on explorer.exe failed (elevation may be required)")
    buttons: list[dict[str, Any]] = []
    try:
        remote_btn = kernel32.VirtualAllocEx(proc, None, _TBBUTTON_SIZE, _MEM_COMMIT_RESERVE, _PAGE_READWRITE)
        remote_txt = kernel32.VirtualAllocEx(proc, None, 1024, _MEM_COMMIT_RESERVE, _PAGE_READWRITE)
        if not remote_btn or not remote_txt:
            raise OSError("VirtualAllocEx in explorer.exe failed")
        try:
            for index in range(min(count, 256)):
                raw = (ctypes.c_ubyte * _TBBUTTON_SIZE)()
                if not user32.SendMessageW(hwnd, _TB_GETBUTTON, index, remote_btn):
                    continue
                read = wintypes.DWORD(0)
                if not kernel32.ReadProcessMemory(proc, remote_btn, raw, _TBBUTTON_SIZE, ctypes.byref(read)):
                    continue
                _bitmap, cmd, state = struct.unpack_from("<iiB", bytes(raw))
                istring = struct.unpack_from("<q", bytes(raw), _TBBUTTON_ISTRING_OFFSET)[0]
                length = int(user32.SendMessageW(hwnd, _TB_GETBUTTONTEXTW, cmd, remote_txt))
                tooltip = ""
                if length > 0:
                    tbuf = (ctypes.c_ubyte * 1024)()
                    if kernel32.ReadProcessMemory(proc, remote_txt, tbuf, 1024, ctypes.byref(read)):
                        try:
                            tooltip = bytes(tbuf[: length * 2]).decode("utf-16-le", errors="replace")
                        except Exception:
                            tooltip = ""
                buttons.append(
                    {
                        "index": index,
                        "id_command": int(cmd),
                        "hidden": bool(state & _TBSTATE_HIDDEN),
                        "tooltip": tooltip[:260],
                        "icon_ref": int(istring),
                    }
                )
        finally:
            kernel32.VirtualFreeEx(proc, remote_btn, 0, _MEM_RELEASE)
            kernel32.VirtualFreeEx(proc, remote_txt, 0, _MEM_RELEASE)
    finally:
        kernel32.CloseHandle(proc)
    return buttons


def _tray_toolbar_pid(hwnd: int) -> int:
    user32 = ctypes.windll.user32
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


# Win11 24H2+ hosts tray icons in per-app top-level windows instead of the
# explorer toolbar. These classes identify them (exact PID attribution).
_TRAY_HOST_PATTERNS = ("NotifyIcon", "TrayIcon", "StatusTray", "SysTrayIcon")


def _find_tray_host_windows() -> list[dict[str, Any]]:
    """Enumerate per-app tray host windows with exact owning PIDs."""
    user32 = ctypes.windll.user32
    hosts: list[dict[str, Any]] = []
    class_buf = ctypes.create_unicode_buffer(256)
    title_buf = ctypes.create_unicode_buffer(256)

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum_proc(hwnd, _lparam):
        try:
            user32.GetClassNameW(hwnd, class_buf, 256)
            class_name = class_buf.value or ""
            if not any(p in class_name for p in _TRAY_HOST_PATTERNS):
                return True
            if class_name in ("NotifyIconOverflowWindow",):
                return True
            user32.GetWindowTextW(hwnd, title_buf, 256)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            name, exe = _proc_identity(pid.value)
            hosts.append(
                {
                    "hwnd": int(hwnd),
                    "class_name": class_name,
                    "title": (title_buf.value or "")[:260],
                    "pid": pid.value,
                    "process": name,
                    "exe": exe,
                }
            )
        except Exception:
            logger.debug("tray host probe failed", exc_info=True)
        return True

    try:
        user32.EnumWindows(_enum_proc, 0)
    except Exception:
        logger.debug("tray host enumeration failed", exc_info=True)
    return hosts


def _guess_tray_owner(tooltip: str, table: list[tuple[int, str, str]]) -> tuple[dict[str, Any] | None, str]:
    """Best-effort attribution of a tray tooltip to a running process.

    table: [(pid, name, exe)]. Returns (identity dict | None, confidence).
    Tooltips usually name the app; matching is substring-based and honest
    about uncertainty — never presented as authoritative.
    """
    text = (tooltip or "").lower()
    if not text:
        return None, "none"
    best: dict[str, Any] | None = None
    level = "none"
    for pid, name, exe in table:
        base = os.path.basename(exe or name or "").lower()
        stem = base[:-4] if base.endswith(".exe") else base
        if len(stem) >= 4 and stem in text:
            if text.startswith(stem) or stem in text.split(" "):
                return {"pid": pid, "process": name, "exe": exe}, "high"
            best = {"pid": pid, "process": name, "exe": exe}
            level = "medium"
    return best, level


def list_tray_icons(
    include_main_area: Annotated[
        bool, Field(description="Include the always-visible tray area (not just overflow)")
    ] = True,
) -> dict[str, Any]:
    """List notification-area (tray) icons with owners and autostart flags.

    Two sources, merged: (1) classic explorer.exe toolbar scraping (pre-24H2
    shells) with heuristic tooltip attribution; (2) per-app tray host windows
    (Win11 24H2+, exact PID via GetWindowThreadProcessId). Host-window hits
    carry confidence "exact"; toolbar guesses carry high/medium. Entries also
    flag autostart registration — the "forgotten app" view.
    """
    note = ""
    try:
        toolbars = _find_tray_toolbars()
    except Exception as e:
        toolbars = []
        note = f"toolbar lookup failed: {e}"
    table: list[tuple[int, str, str]] = []
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            table.append((proc.pid, proc.info.get("name") or "", proc.info.get("exe") or ""))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    startup_map = _startup_exe_map()
    icons: list[dict[str, Any]] = []
    for hwnd, area in toolbars:
        if area == "main" and not include_main_area:
            continue
        try:
            buttons = _read_tray_buttons(hwnd)
        except Exception as e:
            note = f"{note} {area} area unreadable: {e}".strip()
            logger.debug("tray scrape failed for %s area", area, exc_info=True)
            continue
        for b in buttons:
            guess, confidence = _guess_tray_owner(b["tooltip"], table)
            entry: dict[str, Any] = {
                "area": area,
                "index": b["index"],
                "tooltip": b["tooltip"],
                "hidden": b["hidden"],
                "source": "toolbar",
                "process_guess": guess,
                "confidence": confidence,
            }
            entry.update(_autostart_flag((guess or {}).get("exe", ""), startup_map))
            icons.append(entry)
    try:
        hosts = _find_tray_host_windows()
    except Exception as e:
        hosts = []
        note = f"{note} host enumeration failed: {e}".strip()
    for h in hosts:
        guess: dict[str, Any] | None = None
        if h["pid"]:
            guess = {"pid": h["pid"], "process": h["process"], "exe": h["exe"]}
        entry = {
            "area": "tray",
            "index": -1,
            "tooltip": h["title"] or h["process"] or os.path.basename(h["exe"] or ""),
            "hidden": False,
            "source": "window",
            "process_guess": guess,
            "confidence": "exact" if guess else "none",
        }
        entry.update(_autostart_flag(h["exe"], startup_map))
        icons.append(entry)
    if not toolbars and hosts:
        note = f"{note} classic toolbar absent on this shell (Win11 24H2+); host windows used.".strip()
    status = "success" if icons else "error"
    result: dict[str, Any] = {"status": status, "operation": "list_tray_icons", "count": len(icons), "icons": icons}
    if note:
        result["note"] = note
    if status == "error" and not note:
        result["error"] = "no icons found (elevation may be required)"
    return result
