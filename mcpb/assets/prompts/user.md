# System Admin MCP — User Tutorials (4000+ words, 15 tutorials)

This comprehensive guide provides step-by-step tutorials for Windows system administration using the System Admin MCP server. All operations use the consolidated `system_admin` portmanteau tool and dedicated tool functions. The server supports over 40 operations covering process management, services, network, disk operations, users, logs, performance monitoring, scheduled tasks, security, backup, and system diagnostics.

## 1. Getting Started

### 1.1 Server Connectivity Check
Before any administration, verify the server is responsive:
```
ping()
system_admin(operation="health_check")
```
The `ping` tool checks basic service connectivity. The `health_check` returns CPU, memory, and disk usage with comprehensive health status.

### 1.2 The Portmanteau Pattern
Most system operations use a single tool `system_admin` with an `operation` parameter:
```
system_admin(operation="<operation_name>", param1=value1, param2=value2)
```
This pattern keeps the tool surface discoverable while providing access to 40+ operations. Each operation has its own parameters documented inline.

### 1.3 Service Overview
```
status(level="intermediate")
```
Returns server status, registered tools, and configuration details.

## 2. System Diagnostics — 6 Tutorials

### 2.1 Quick Health Assessment
Goal: Get a complete system health snapshot in under 5 seconds.
```
system_admin(operation="health_check")
```
Returns: overall status (healthy/needs_attention), CPU load, memory usage, disk usage for each partition, and timestamp. Use this as your first diagnostic step for any system issue.

### 2.2 Performance Deep Dive
Goal: Identify what is consuming system resources.
```
system_admin(operation="get_performance_metrics")
```
Returns comprehensive metrics:
- CPU: per-core and total utilization percentage
- Memory: total, used, available bytes and percentage
- Swap: total, used bytes
- Disk I/O: read/write bytes and operation counts
- Network: bytes and packets sent/received
- Top 10 processes by CPU and by memory

Use the per-core CPU data to identify single-threaded bottlenecks. High disk I/O with low CPU suggests a storage bottleneck.

### 2.3 Advanced Event Log Analysis
Goal: Investigate system errors across multiple logs with filtering.
```
system_admin(operation="get_event_log", log_name="System", level="Error", hours_back=24)
system_admin(operation="get_event_log", log_name="Application", level="Warning", hours_back=48)
system_admin(operation="get_event_log", log_name="Security", level="Error", hours_back=72)
```
Each query returns events with timestamp, source, event ID, type classification, and formatted message. Cross-reference errors between System and Application logs to correlate driver failures with application crashes.

### 2.4 Complete Hardware Inventory
Goal: Document all hardware in the system for asset management or upgrade planning.
```
system_admin(operation="get_hardware_info")
```
Returns detailed hardware inventory:
- CPU: name, manufacturer, physical cores, logical cores, frequency, architecture
- Memory: total capacity, utilization
- Disks: device, mountpoint, filesystem type, capacity by partition
- Network: all interfaces with IP addresses
- GPU: name, adapter RAM, driver version (when WMI is available)

Use this before hardware upgrades to verify compatibility and after installation to confirm detection.

### 2.5 Software Audit and License Tracking
Goal: List all installed software for compliance or migration planning.
```
system_admin(operation="get_installed_software")
```
Returns every installed application from HKLM and HKCU Uninstall registry paths including name, version, publisher, and install date. Filter results client-side to identify outdated software needing updates or unused applications for cleanup.

### 2.6 Comprehensive Diagnostic Report
Goal: Generate a unified diagnostic report for troubleshooting or system handoff.
```
get_comprehensive_diagnostics()
```
Combines health check, top resource processes, recent event errors, and primary volume usage into a single structured report. This is the recommended starting point when a user reports an unspecified system problem.

## 3. Process Management — 3 Tutorials

### 3.1 Process Discovery and Analysis
Goal: Find and investigate processes by name, user, or resource usage.
```
system_admin(operation="list_processes", filter_name="python", sort_by="memory")
system_admin(operation="list_processes", filter_name="explorer", sort_by="cpu")
```
Sort options: cpu, memory, name, pid. Filter by process name substring. The results include PID, name, CPU, and memory usage. After identifying suspicious or problematic processes, drill down:

```
system_admin(operation="analyze_process", pid=1234)
```
Returns full process details: executable path, command line, CPU/memory/thread/handle counts, open network connections, and child processes. Use this to verify a process is legitimate before termination.

### 3.2 Top Resource Consumer Identification
Goal: Find which processes are consuming the most system resources.
```
system_admin(operation="get_top_resource_processes", count=10)
```
Returns the top N processes by CPU and memory consumption. This is the fastest way to identify runaway processes. Common culprits include browser tabs, antivirus scans, Windows Update, and indexing services.

### 3.3 Safe Process Termination
Goal: End a problematic process safely.
```
system_admin(operation="kill_process", pid=1234, force=False)
```
Always start with force=False (graceful termination via WM_CLOSE). Only use force=True if the process does not respond within a few seconds. Check with `list_processes` afterward to confirm termination. Avoid terminating critical system processes (System, svchost.exe, csrss.exe, winlogon.exe, services.exe).

## 4. Windows Services — 3 Tutorials

### 4.1 Service Discovery and Inventory
Goal: List and categorize all Windows services.
```
system_admin(operation="list_services", filter_status="running")
system_admin(operation="list_services", filter_name="sql")
system_admin(operation="list_services", filter_status="stopped")
```
The first returns only running services for a quick health check. The second shows SQL-related services. The third lists stopped services that might need attention. Combine with name filtering for targeted searches.

### 4.2 Service Statistics and Health
Goal: Get an overview of service states.
```
system_admin(operation="get_service_stats")
```
Returns counts of running, stopped, and disabled services plus services with the highest CPU and memory consumption. A high ratio of running-to-stopped non-Microsoft services may indicate unnecessary resource usage.

### 4.3 Service Lifecycle Management
Goal: Start, stop, and configure service startup.

Step 1 — Inspect current state:
```
system_admin(operation="get_service_info", service_name="Spooler")
```
Returns display name, current status, startup type (Auto, Manual, Disabled), binary path, service account, dependencies, and description.

Step 2 — Start a stopped service:
```
system_admin(operation="start_service", service_name="Spooler", wait_timeout=30)
```
The wait_timeout controls how long to wait for the service to reach running state. Services with long dependency chains may need higher timeouts (60-90 seconds).

Step 3 — Stop a running service:
```
system_admin(operation="stop_service", service_name="Spooler", wait_timeout=30)
```

Step 4 — Change startup type:
```
system_admin(operation="set_service_startup", service_name="Spooler", startup_type="Auto")
system_admin(operation="set_service_startup", service_name="Spooler", startup_type="Manual")
system_admin(operation="set_service_startup", service_name="Spooler", startup_type="Disabled")
```
Startup types: Auto (starts at boot), Manual (starts on demand), Disabled (cannot start). Use Disabled for services that should never run, Manual for infrequently used services.

## 5. Network and Security — 3 Tutorials

### 5.1 Network Port Audit
Goal: Inventory all listening and established network connections.
```
system_admin(operation="audit_network_ports", include_system=True)
```
Returns every TCP and UDP connection with: protocol, local address and port, remote address and port, connection state (LISTEN, ESTABLISHED, TIME_WAIT, CLOSE_WAIT), PID, and process name. Filter results for unexpected listening ports (especially high ports 49152-65535) which may indicate unauthorized services or malware.

### 5.2 File Permission Audit
Goal: Review and audit permissions on sensitive directories.
```
system_admin(operation="get_permissions", path="C:/SharedFolder")
system_admin(operation="audit_permissions", path="C:/SensitiveData")
```
The audit tool automatically identifies security issues including Everyone with FullControl, empty permission entries, and inherited vs explicit permissions. For critical directories, always run the audit before and after making permission changes.

### 5.3 Permission Management
Goal: Grant, modify, and revoke permissions securely.

Step 1 — Document current permissions:
```
system_admin(operation="get_permissions", path="D:/Projects")
```

Step 2 — Grant access with dry-run mode:
```
system_admin(operation="set_permissions", path="D:/Projects", principal="DOMAIN\\user", rights="Modify", inheritance="both")
```

Step 3 — Revoke access when no longer needed:
```
system_admin(operation="remove_permission", path="D:/Projects", principal="DOMAIN\\user")
```

Step 4 — Take ownership when permissions are locked:
```
system_admin(operation="take_ownership", path="C:/RestrictedFile.txt")
```
After taking ownership, grant yourself explicit permissions to access the file. Available rights: Read, Write, Modify, FullControl, ReadAndExecute, ListDirectory. Inheritance options: none, container_inherit, object_inherit, both.

## 6. Disk and Volume Management — 5 Tutorials

### 6.1 Physical Disk Health Check
Goal: Verify physical disk health before any maintenance.
```
system_admin(operation="check_disk_health", drive="C:")
```
Returns model, serial number, size, and WMI status. When available, includes SMART health data. Run this monthly for proactive failure detection.

### 6.2 Detailed Disk Space Analysis
Goal: Understand what is consuming disk space.
```
system_admin(operation="analyze_disk_usage", drive="C:")
system_admin(operation="analyze_top_folder_sizes", path="C:\\")
```
The first returns total/used/free space with percentage. The second returns the 20 largest folders on the drive, sorted by size descending. Use these together to identify space hogs before cleanup operations.

### 6.3 Safe Disk Cleanup
Goal: Free disk space with preview before execution.

Step 1 — Preview what will be freed:
```
system_admin(operation="disk_cleanup", drive="C:", cleanup_targets=["temp_files", "recycle_bin", "windows_temp", "prefetch", "delivery_optimization"], dry_run=True)
```

Step 2 — Review the estimated space recovery report.

Step 3 — Execute cleanup when satisfied:
```
system_admin(operation="disk_cleanup", drive="C:", cleanup_targets=["temp_files", "recycle_bin", "windows_temp"], dry_run=False)
```
Cleanup targets: temp_files (user TEMP), recycle_bin (Recycle Bin), windows_temp (Windows Temp), prefetch (Prefetch cache), delivery_optimization (Windows Update cache), old_windows_installations (previous Windows versions).

### 6.4 Drive Optimization (SSD and HDD)
Goal: Optimize storage performance based on drive type.

First check the drive type:
```
system_admin(operation="get_volume_info", drive="C:")
```

For HDD optimization:
```
system_admin(operation="defragment_disk", drive="D:", thorough=False)
system_admin(operation="defragment_disk", drive="D:", thorough=True)
```

For SSD optimization (TRIM):
```
system_admin(operation="optimize_ssd", drive="C:")
```

The defrag tool automatically detects SSDs and refuses to defragment them. Always verify drive type before optimization. SSDs require TRIM only; HDDs benefit from periodic defragmentation.

### 6.5 Volume Information
Goal: Get detailed volume data.
```
system_admin(operation="get_volume_info", drive="C:")
system_admin(operation="get_volume_info", drive="D:")
```
Returns filesystem type (NTFS, FAT32, exFAT), volume label, drive type (fixed, removable, remote, cdrom), capacity, usage, and cluster size.

## 7. Startup and Taskbar Management — 2 Tutorials

### 7.1 Startup Program Management
Goal: Review and manage programs that start automatically.
```
system_admin(operation="list_startup_programs")
system_admin(operation="add_startup_program", startup_name="MyApp", startup_command="C:/MyApp/app.exe", startup_location="HKCU")
system_admin(operation="remove_startup_program", startup_name="MyApp", startup_location="HKCU")
```
Startup locations: HKCU (current user), HKLM (all users). Review list periodically to remove programs that slow boot time. Be cautious about removing startup entries for security software and hardware drivers.

### 7.2 Taskbar Autohide Management
Goal: Troubleshoot and manage taskbar behavior.
```
system_admin(operation="get_taskbar_settings")
system_admin(operation="set_taskbar_autohide", autohide=True)
system_admin(operation="find_taskbar_blocking_processes")
system_admin(operation="kill_taskbar_blocking_processes")
```
Taskbar autohide can be blocked by full-screen applications, notification popups, or system processes. Use the find tool to identify blockers and the kill tool to remove them.

## 8. NTFS File Recovery — 2 Tutorials

### 8.1 Volume Scan for Deleted Files
Goal: Find recoverable deleted files on an NTFS volume.
```
system_admin(operation="scan_volume", drive="C:", file_pattern="*.docx", max_results=50)
system_admin(operation="scan_volume", drive="D:", file_pattern="*report*", max_results=100)
```
Patterns support wildcards (*.docx, *report*). Stop all writes to the affected drive before scanning to maximize recovery chances. Recovery probability decreases with time since deletion.

### 8.2 File Recovery and Validation
Goal: Recover and verify deleted files.
```
system_admin(operation="recover_file", source_path="C:/deleted/document.docx", destination_path="D:/Recovery/document.docx")
system_admin(operation="validate_recovery", destination_path="D:/Recovery/document.docx")
```
Always recover to a different physical drive than the source to prevent overwriting. The validation step verifies file size, calculates SHA-256 hash, and checks readability.

## 9. Agentic Workflows — 2 Tutorials

### 9.1 Autonomous Performance Diagnosis
Goal: Let the server autonomously diagnose performance issues using ctx.sample().
```
agentic_system_workflow(
    workflow_prompt="Diagnose why the system is running slowly and identify the top 3 resource bottlenecks",
    available_tools=["get_performance_metrics", "list_processes", "get_recent_event_errors"],
    max_iterations=5
)
```
The workflow collects metrics, samples an LLM for analysis, and returns prioritized findings with remediation steps. Available diagnostics are collected automatically based on the tool list provided.

### 9.2 Autonomous Problem Troubleshooter
Goal: Three-phase autonomous diagnosis for user-reported problems.
```
autonomous_system_troubleshooter(problem_description="System is slow after startup, takes 5 minutes to become responsive")
```
Phase 1: automatically collects health check, event errors, performance metrics, and top processes.
Phase 2: samples for root cause analysis with categorization (Permissions, Process conflict, Service failure, Resource exhaustion, Hardware, Network).
Phase 3: returns structured findings with root cause, verification steps, and remediation.

## 10. Background Filesystem Monitoring

Goal: Monitor directories for real-time filesystem changes.
```
manage_filesystem_watch(operation="start", path="C:/Important", recursive=True)
manage_filesystem_watch(operation="get_events", path="C:/Important")
manage_filesystem_watch(operation="list")
manage_filesystem_watch(operation="stop", path="C:/Important")
```
Use for monitoring configuration file changes, tracking document modifications, or detecting unauthorized file system activity. Events include created, modified, deleted, and renamed files with timestamps.

## 11. Getting System Information

Goal: Retrieve comprehensive system details for documentation.
```
get_system_info()
```
Returns OS version, system manufacturer, model, BIOS version, processor, total physical memory, and available memory. Use this for system documentation before changes or for remote inventory.

## 12. Safety Best Practices

### 12.1 Always Preview Destructive Operations
```
system_admin(operation="disk_cleanup", drive="C:", dry_run=True)
system_admin(operation="set_permissions", path="D:/Projects", principal="DOMAIN\\user", rights="Modify", dry_run=True)
```

### 12.2 Document Before Changes
Before modifying permissions: run get_permissions to document current ACLs. Before terminating processes: run analyze_process to verify the process is safe to kill.

### 12.3 Drive Type Awareness
Always check drive type before optimization: SSDs use TRIM, HDDs use defragmentation. The server rejects defrag on SSDs, but awareness prevents unnecessary operations.

### 12.4 File Recovery Golden Rules
Stop all writes to the affected drive immediately. Recover to a different physical drive. Validate the recovered file before use. Time is critical — every hour reduces success probability.

### 12.5 Permission Change Protocol
Backup current permissions before changes. Make one change at a time. Verify each change with get_permissions. Document the before and after state for audit purposes.
