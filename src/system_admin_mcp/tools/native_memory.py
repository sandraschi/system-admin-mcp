"""Native Windows NT kernel memory metrics and list purges.

Uses direct NTDLL (NtQuerySystemInformation / NtSetSystemInformation with
SystemMemoryListInformation, class 80), GlobalMemoryStatusEx, and GetPerformanceInfo.
"""

from __future__ import annotations

import ctypes
import logging
import os
from ctypes import wintypes

logger = logging.getLogger(__name__)

SYSTEM_MEMORY_LIST_INFORMATION_CLASS = 80  # 0x50

# SYSTEM_MEMORY_LIST_COMMAND constants
MEMORY_CAPTURE_ACCESSED_BITS = 0
MEMORY_CAPTURE_AND_RESET_ACCESSED_BITS = 1
MEMORY_EMPTY_WORKING_SETS = 2
MEMORY_FLUSH_MODIFIED_LIST = 3
MEMORY_PURGE_STANDBY_LIST = 4
MEMORY_PURGE_PRIORITY0_LIST = 5

TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_PRIVILEGE_ENABLED = 0x00000002


class SYSTEM_MEMORY_LIST_INFORMATION(ctypes.Structure):
    """x64 layout matching winsiderss/phnt (Process Hacker Native API)."""

    _fields_ = [
        ("ZeroPageCount", ctypes.c_size_t),
        ("FreePageCount", ctypes.c_size_t),
        ("ModifiedPageCount", ctypes.c_size_t),
        ("ModifiedNoWritePageCount", ctypes.c_size_t),
        ("BadPageCount", ctypes.c_size_t),
        ("PageCountByPriority", ctypes.c_size_t * 8),
        ("RepurposedPagesByPriority", ctypes.c_size_t * 8),
        ("ModifiedPageCountPageFile", ctypes.c_size_t),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


class PERFORMANCE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t),
        ("HandleCount", wintypes.DWORD),
        ("ProcessCount", wintypes.DWORD),
        ("ThreadCount", wintypes.DWORD),
    ]


class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]


class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Luid", LUID),
        ("Attributes", wintypes.DWORD),
    ]


class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Privileges", LUID_AND_ATTRIBUTES * 1),
    ]


def enable_privilege(privilege_name: str) -> bool:
    """Attempt to enable a Windows token privilege (e.g. SeProfileSingleProcessPrivilege)."""
    if os.name != "nt":
        return False
    try:
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32
        token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(),
            TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
            ctypes.byref(token),
        ):
            return False

        try:
            luid = LUID()
            if not advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
                return False

            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

            res = advapi32.AdjustTokenPrivileges(token, False, ctypes.byref(tp), 0, None, None)
            err = kernel32.GetLastError()
            return res != 0 and err == 0
        finally:
            kernel32.CloseHandle(token)
    except Exception as e:
        logger.debug(f"Failed to enable privilege {privilege_name}: {e}")
        return False


def query_nt_memory_info(detailed: bool = False) -> dict | None:
    """Query NT kernel memory lists directly via NtQuerySystemInformation."""
    if os.name != "nt":
        return None

    try:
        ntdll = ctypes.windll.ntdll
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi

        mem_info = SYSTEM_MEMORY_LIST_INFORMATION()
        ret_len = wintypes.ULONG()

        status = ntdll.NtQuerySystemInformation(
            SYSTEM_MEMORY_LIST_INFORMATION_CLASS,
            ctypes.byref(mem_info),
            ctypes.sizeof(mem_info),
            ctypes.byref(ret_len),
        )
        if status != 0:
            return None

        perf = PERFORMANCE_INFORMATION()
        perf.cb = ctypes.sizeof(PERFORMANCE_INFORMATION)
        has_perf = bool(psapi.GetPerformanceInfo(ctypes.byref(perf), perf.cb))

        page_size = perf.PageSize if has_perf and perf.PageSize else 4096
        mb = 1024 * 1024

        mstatus = MEMORYSTATUSEX()
        mstatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        has_status = bool(kernel32.GlobalMemoryStatusEx(ctypes.byref(mstatus)))

        total_phys_mb = (
            round((mstatus.ullTotalPhys / mb), 0) if has_status else round((perf.PhysicalTotal * page_size) / mb, 0)
        )
        avail_phys_mb = (
            round((mstatus.ullAvailPhys / mb), 0) if has_status else round((perf.PhysicalAvailable * page_size) / mb, 0)
        )
        used_phys_mb = max(0, total_phys_mb - avail_phys_mb)

        standby_counts = list(mem_info.PageCountByPriority)
        standby_total_pages = sum(standby_counts)
        standby_total_mb = round((standby_total_pages * page_size) / mb, 0)

        zeroed_mb = round((mem_info.ZeroPageCount * page_size) / mb, 0)
        free_mb = round((mem_info.FreePageCount * page_size) / mb, 0)
        modified_mb = round((mem_info.ModifiedPageCount * page_size) / mb, 0)
        modified_nowrite_mb = round((mem_info.ModifiedNoWritePageCount * page_size) / mb, 0)
        bad_mb = round((mem_info.BadPageCount * page_size) / mb, 0)

        cache_mb = round((perf.SystemCache * page_size) / mb, 0) if has_perf else standby_total_mb
        commit_total_mb = round((perf.CommitTotal * page_size) / mb, 0) if has_perf else 0
        commit_limit_mb = round((perf.CommitLimit * page_size) / mb, 0) if has_perf else 0
        kernel_paged_mb = round((perf.KernelPaged * page_size) / mb, 0) if has_perf else 0
        kernel_nonpaged_mb = round((perf.KernelNonpaged * page_size) / mb, 0) if has_perf else 0

        categories = {
            "total_mb": total_phys_mb,
            "available_mb": avail_phys_mb,
            "used_mb": used_phys_mb,
            "system_cache_mb": cache_mb,
            "standby_total_mb": standby_total_mb,
            "modified_mb": modified_mb,
            "modified_nowrite_mb": modified_nowrite_mb,
            "free_mb": free_mb,
            "zeroed_mb": zeroed_mb,
            "bad_mb": bad_mb,
            "commit_total_mb": commit_total_mb,
            "commit_limit_mb": commit_limit_mb,
            "kernel_paged_mb": kernel_paged_mb,
            "kernel_nonpaged_mb": kernel_nonpaged_mb,
        }

        res: dict = {
            "status": "success",
            "operation": "get_ram_map",
            "categories": categories,
        }

        if detailed:
            res["standby_priorities_mb"] = {
                str(pri): round((cnt * page_size) / mb, 1) for pri, cnt in enumerate(standby_counts)
            }
            res["perf_counts"] = {
                "handles": perf.HandleCount if has_perf else 0,
                "processes": perf.ProcessCount if has_perf else 0,
                "threads": perf.ThreadCount if has_perf else 0,
            }

        return res
    except Exception as e:
        logger.debug(f"NT memory info query failed: {e}")
        return None


def execute_memory_purge(target: str) -> dict:
    """Execute memory purge via NtSetSystemInformation."""
    if os.name != "nt":
        return {"status": "error", "message": "Only supported on Windows NT"}

    cmd_map = {
        "standby": MEMORY_PURGE_STANDBY_LIST,
        "working_sets": MEMORY_EMPTY_WORKING_SETS,
        "modified": MEMORY_FLUSH_MODIFIED_LIST,
        "priority0": MEMORY_PURGE_PRIORITY0_LIST,
    }
    cmd_val = cmd_map.get(target, MEMORY_PURGE_STANDBY_LIST)

    before = query_nt_memory_info(detailed=False)

    enable_privilege("SeProfileSingleProcessPrivilege")
    enable_privilege("SeIncreaseQuotaPrivilege")

    try:
        ntdll = ctypes.windll.ntdll
        command_var = wintypes.ULONG(cmd_val)
        status = ntdll.NtSetSystemInformation(
            SYSTEM_MEMORY_LIST_INFORMATION_CLASS,
            ctypes.byref(command_var),
            ctypes.sizeof(command_var),
        )
        if status == 0:
            after = query_nt_memory_info(detailed=False)
            freed_mb = None
            if before and after:
                if target == "standby":
                    freed_mb = max(
                        0.0, before["categories"]["standby_total_mb"] - after["categories"]["standby_total_mb"]
                    )
                elif target == "working_sets":
                    freed_mb = max(0.0, before["categories"]["used_mb"] - after["categories"]["used_mb"])

            return {
                "status": "success",
                "operation": "purge_standby_memory",
                "target": target,
                "freed_mb": freed_mb,
                "message": f"Successfully executed memory purge for {target}",
            }
        elif status == -1073741727 or status == -1073741790:
            return {
                "status": "error",
                "operation": "purge_standby_memory",
                "target": target,
                "message": "Administrator privilege required. Start System Admin MCP with elevated administrator privileges.",
            }
        else:
            return {
                "status": "error",
                "operation": "purge_standby_memory",
                "target": target,
                "message": f"NtSetSystemInformation returned NTSTATUS {status:#x}",
            }
    except Exception as e:
        return {"status": "error", "operation": "purge_standby_memory", "target": target, "message": str(e)}
