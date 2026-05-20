# System Admin MCP — User Tutorials

This guide provides step-by-step tutorials for common Windows system administration tasks using the System Admin MCP server. All operations use the consolidated `system_admin` portmanteau tool.

---

## 1. Getting Started

### 1.1 Checking Server Status

Before performing any operations, verify the server is running:

```
system_admin(operation="health_check")
system_admin(operation="help")
```

The `health_check` returns CPU, memory, disk usage and overall system status.
The `help` command lists all available operations with descriptions.

### 1.2 Understanding the Portmanteau Pattern

All system operations are accessed through a single tool `system_admin` with an `operation` parameter:

```
system_admin(operation="<operation_name>", param1=value1, param2=value2)
```

This pattern reduces tool count and provides a discoverable interface.

---

## 2. System Diagnostics Tutorials

### 2.1 Quick Health Check

**Goal**: Get a snapshot of system health in under 5 seconds.

```
system_admin(operation="health_check")
```

Expected response contains:
- `status`: "healthy", "warning", or "critical"
- `cpu_percent`: Current CPU utilization
- `memory_percent`: Current RAM utilization
- `disk_percent`: System drive disk usage
- `uptime_days`: System uptime
- `reboot_required`: Whether a reboot is pending

### 2.2 Performance Deep Dive

**Goal**: Identify what is consuming system resources.

Step 1 — Get real-time metrics:
```
system_admin(operation="get_performance_metrics")
```

Step 2 — Find top CPU consumers:
```
system_admin(operation="list_processes", sort_by="cpu", filter_name="")
```

Step 3 — Find top memory consumers:
```
system_admin(operation="list_processes", sort_by="memory")
```

Step 4 — Check recent errors:
```
system_admin(operation="get_recent_event_errors", log_name="System")
```

### 2.3 Hardware Inventory

**Goal**: Document all hardware in the system.

```
system_admin(operation="get_hardware_info")
```

Returns: CPU model/cores/threads, RAM total/slots, disk models/capacities, GPU details, motherboard info.

### 2.4 Software Audit

**Goal**: List all installed software.

```
system_admin(operation="get_installed_software")
```

Filters by registry (HKLM and HKCU uninstall paths). Returns name, version, publisher, install date.

### 2.5 Full Diagnostic Report

**Goal**: Generate a comprehensive diagnostic report.

```
system_admin(operation="get_comprehensive_diagnostics")
```

Combines: health check, top resource processes, recent event errors, and primary volume usage in a single call.

---

## 3. File & Volume Management Tutorials

### 3.1 Check Disk Health

**Goal**: Verify disk health before any maintenance operation.

```
system_admin(operation="check_disk_health", drive="C:")
```

Returns: SMART status, temperature, reallocated sectors, pending sectors, overall health rating.

### 3.2 Analyze Disk Usage

**Goal**: Understand what is consuming disk space.

```
system_admin(operation="analyze_disk_usage", drive="C:")
```

Returns breakdown of space used by: system files, applications, documents, temp files, and available space.

### 3.3 Analyze Top Folder Sizes

**Goal**: Find the largest folders on a drive.

```
system_admin(operation="analyze_top_folder_sizes", path="C:\\")
```

Returns the 20 largest folders sorted by size. Use this to identify space hogs before cleanup.

### 3.4 Safe Disk Cleanup

**Goal**: Free up disk space safely.

Step 1 — Preview what will be cleaned:
```
system_admin(operation="disk_cleanup", drive="C:", cleanup_targets=["temp_files", "recycle_bin", "windows_temp"], dry_run=True)
```

Step 2 — Review the estimated space recovery.

Step 3 — Execute the cleanup:
```
system_admin(operation="disk_cleanup", drive="C:", cleanup_targets=["temp_files", "recycle_bin", "windows_temp"], dry_run=False)
```

Available cleanup targets: `temp_files`, `recycle_bin`, `windows_temp`, `prefetch`, `delivery_optimization`, `old_windows_installations`.

### 3.5 Volume Information

**Goal**: Get detailed volume information.

```
system_admin(operation="get_volume_info", drive="C:")
```

Returns: filesystem type, total/used/free space, cluster size, volume serial number, compression status.

### 3.6 Defragment HDD

**Goal**: Defragment a traditional hard disk drive.

WARNING: Only use on HDDs. NEVER defragment SSDs.

```
system_admin(operation="defragment_disk", drive="D:", thorough=False)
```

For thorough defragmentation:
```
system_admin(operation="defragment_disk", drive="D:", thorough=True)
```

### 3.7 Optimize SSD

**Goal**: Optimize a Solid State Drive with TRIM.

```
system_admin(operation="optimize_ssd", drive="C:")
```

---

## 4. NTFS File Recovery Tutorials

### 4.1 Critical: Stop All Writes

If a file was recently deleted:
1. STOP all operations on the affected drive immediately
2. Do not save, download, or install anything to that drive
3. Every write operation reduces recovery probability

### 4.2 Scan for Deleted Files

**Goal**: Find a deleted file in the NTFS MFT.

```
system_admin(operation="scan_volume", drive="C:", file_pattern="*.docx", max_results=50)
```

Parameters:
- `file_pattern`: Use wildcards (e.g., `*.docx`, `report*.*`, `*tax*`)
- `max_results`: Limit results for performance (default 100)

### 4.3 Recover the File

**Goal**: Restore the deleted file.

```
system_admin(operation="recover_file", source_path="C:/Users/sandra/Documents/report.docx", destination_path="D:/Recovery/report.docx")
```

Rules:
- Recover to a DIFFERENT drive than the source
- Preserve the original extension
- Add timestamp to filename if recovering multiple versions

### 4.4 Validate Recovery

**Goal**: Verify recovered file integrity.

```
system_admin(operation="validate_recovery", destination_path="D:/Recovery/report.docx")
```

Returns: file size match, header signature validation, content hash, overall integrity score.

### 4.5 Batch Recovery

**Goal**: Recover multiple files at once.

```
system_admin(operation="batch_recover", source_path="C:/DeletedFolder/*.docx", destination_path="D:/Recovery/")
```

---

## 5. Security & Permissions Tutorials

### 5.1 Audit Permissions

**Goal**: Review current permissions on a file or folder.

```
system_admin(operation="audit_permissions", path="C:/SharedFolder")
```

Returns: list of all ACE entries, inheritance settings, effective permissions per user/group.

### 5.2 View Current Permissions

**Goal**: Get detailed ACL information.

```
system_admin(operation="get_permissions", path="C:/SharedFolder")
```

Returns: owner, group, permission entries with inheritance flags, audit entries.

### 5.3 Set Permissions

**Goal**: Grant or modify permissions.

```
system_admin(operation="set_permissions", path="D:/Projects", principal="DOMAIN\\sandra", rights="Modify", inheritance="container_inherit")
```

Rights: `Read`, `Write`, `Modify`, `FullControl`, `ReadAndExecute`, `ListDirectory`.
Inheritance: `none`, `container_inherit`, `object_inherit`, `both`.

### 5.4 Remove Permission

**Goal**: Revoke a user's access.

```
system_admin(operation="remove_permission", path="D:/Projects", principal="DOMAIN\\former_employee")
```

### 5.5 Take Ownership

**Goal**: Take ownership of a file or folder.

```
system_admin(operation="take_ownership", path="C:/StubbornFile.txt")
```

Requires administrator privileges. After taking ownership, grant yourself permissions:
```
system_admin(operation="set_permissions", path="C:/StubbornFile.txt", principal="BUILTIN\\Administrators", rights="FullControl")
```

### 5.6 Network Port Audit

**Goal**: Inventory open network ports.

```
system_admin(operation="audit_network_ports", include_system=True)
```

Returns: listening ports, associated processes, connection states, foreign addresses.

---

## 6. Windows Services Tutorials

### 6.1 List All Services

**Goal**: View all Windows services with filtering.

```
system_admin(operation="list_services", filter_status="running")
```

Filters: `running`, `stopped`, `all`. Also supports `filter_name="wind"` for partial name match.

### 6.2 Get Service Statistics

**Goal**: Summary of service states.

```
system_admin(operation="get_service_stats")
```

Returns: counts of running, stopped, disabled services; top CPU/memory consuming services.

### 6.3 Get Service Details

**Goal**: Detailed information about a specific service.

```
system_admin(operation="get_service_info", service_name="Spooler")
```

Returns: display name, status, startup type, binary path, account, dependencies, description.

### 6.4 Start a Service

**Goal**: Start a stopped service.

```
system_admin(operation="start_service", service_name="Spooler", wait_timeout=30)
```

### 6.5 Stop a Service

**Goal**: Stop a running service.

```
system_admin(operation="stop_service", service_name="Spooler", wait_timeout=30)
```

### 6.6 Change Service Startup Type

**Goal**: Modify how a service starts.

```
system_admin(operation="set_service_startup", service_name="Spooler", startup_type="Auto")
```

Startup types: `Auto`, `Manual`, `Disabled`.

---

## 7. Process Management Tutorials

### 7.1 List Running Processes

**Goal**: View running processes with sorting.

```
system_admin(operation="list_processes", sort_by="cpu")
```

Sort options: `cpu`, `memory`, `name`, `pid`. Filter by name: `filter_name="chrome"`.

### 7.2 Analyze a Process

**Goal**: Get detailed information about a specific process.

```
system_admin(operation="analyze_process", pid=1234)
```

Returns: name, executable path, command line, status, CPU/memory usage, threads, handles, open connections, child processes.

### 7.3 Kill a Process

**Goal**: Terminate a problematic process.

```
system_admin(operation="kill_process", pid=1234, force=False)
```

Use `force=True` if the process does not respond to normal termination.

---

## 8. Startup Programs Tutorials

### 8.1 List Startup Programs

**Goal**: View all programs that start with Windows.

```
system_admin(operation="list_startup_programs")
```

Returns: name, command/path, registry location (HKCU/HKLM/Startup Folder).

### 8.2 Add a Startup Program

**Goal**: Add a program to Windows startup.

```
system_admin(operation="add_startup_program", startup_name="MyApp", startup_command="C:/MyApp/app.exe", startup_location="HKCU")
```

### 8.3 Remove a Startup Program

**Goal**: Remove a program from Windows startup.

```
system_admin(operation="remove_startup_program", startup_name="MyApp", startup_location="HKCU")
```

---

## 9. Taskbar Management Tutorials

### 9.1 View Taskbar Settings

**Goal**: Check current taskbar state.

```
system_admin(operation="get_taskbar_settings")
```

Returns: autohide status, lock taskbar status.

### 9.2 Enable/Disable Autohide

**Goal**: Toggle taskbar autohide.

```
system_admin(operation="set_taskbar_autohide", autohide=True)
```

### 9.3 Find Taskbar Blockers

**Goal**: Identify processes preventing taskbar autohide.

```
system_admin(operation="find_taskbar_blocking_processes")
```

### 9.4 Kill Taskbar Blockers

**Goal**: Terminate processes blocking the taskbar.

```
system_admin(operation="kill_taskbar_blocking_processes")
```

---

## 10. Agentic Workflows (SEP-1577)

### 10.1 Autonomous Diagnostics

**Goal**: Let the AI autonomously diagnose system issues.

```
agentic_system_workflow(
    workflow_prompt="Diagnose why the system is running slowly and identify the top 3 resource bottlenecks",
    available_tools=["get_performance_metrics", "list_processes", "get_recent_event_errors"],
    max_iterations=5
)
```

The server uses `ctx.sample()` to analyze findings and determine next actions without client round-trips.

### 10.2 Autonomous Troubleshooter

**Goal**: Three-phase autonomous problem diagnosis.

```
autonomous_system_troubleshooter(
    user_complaint="System is slow after startup, takes 5 minutes to become responsive"
)
```

Phase 1: Scans health, events, and processes.
Phase 2: Samples an LLM for root cause analysis.
Phase 3: Provides structured findings and remediation steps.

---

## 11. Background Filesystem Monitoring

### 11.1 Start Watching a Directory

```
manage_filesystem_watch(operation="start", path="C:/Important", recursive=True)
```

### 11.2 Get Captured Events

```
manage_filesystem_watch(operation="get_events", path="C:/Important")
```

### 11.3 List Active Watches

```
manage_filesystem_watch(operation="list")
```

### 11.4 Stop Watching

```
manage_filesystem_watch(operation="stop", path="C:/Important")
```

---

## 12. Web Dashboard Access

The server includes a React web dashboard at:
- Frontend: http://localhost:10860
- Backend API: http://localhost:10861

Available dashboard pages:
- **Dashboard**: System health overview with cards
- **Status**: Detailed system metrics
- **Processes**: Process list with detail modals
- **Services**: Windows service management
- **Volumes**: Volume and disk management
- **File Owner**: File/folder ownership viewer
- **File Recovery**: NTFS file recovery interface
- **Logs**: System log viewer
- **Tools**: Browse available MCP tools
- **Apps**: Prefab UI applications (if enabled)
- **Settings**: Server configuration

To start the dashboard:
```powershell
# Start backend API (port 10861)
just web

# In a separate terminal, start frontend (port 10860)
just web-frontend
```

---

## 13. Safety Best Practices

### 13.1 Always Run Dry-Run First

For destructive operations, always preview first:
```
system_admin(operation="disk_cleanup", drive="C:", dry_run=True)
system_admin(operation="set_permissions", path="D:/Projects", principal="DOMAIN\\user", rights="Modify", dry_run=True)
```

### 13.2 Document Before Changes

Before modifying permissions:
1. `system_admin(operation="get_permissions", path="<target>")`
2. Document current ACLs
3. Apply changes
4. Verify with another `get_permissions`

### 13.3 SSD vs HDD Awareness

Check drive type before optimization:
```
system_admin(operation="get_volume_info", drive="C:")
```

- SSDs: Use `optimize_ssd` only
- HDDs: `defragment_disk` is safe

### 13.4 File Recovery Golden Rules

1. Stop all writes to the affected drive immediately
2. Recover to a different physical drive
3. Validate the recovered file before use
4. Time is critical — every hour reduces success probability
