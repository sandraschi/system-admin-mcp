# System Diagnostics Guide - System Admin MCP

## System Information Collection

### Hardware Information
```python
# Get comprehensive hardware details
hw_info = get_hardware_info()

Returns:
- CPU: Model, cores, threads, frequency
- RAM: Total, available, used, speed
- Motherboard: Manufacturer, model, BIOS version
- Storage: Drives, capacities, types (HDD/SSD)
- GPU: Model, VRAM, driver version
- Network: Adapters, MAC addresses, speeds
```

### Operating System Details
```python
# Get OS information
os_info = get_os_info()

Returns:
- Windows version (10, 11, Server)
- Build number
- Edition (Home, Pro, Enterprise)
- Install date
- Last update
- Activation status
- System uptime
```

### Software Inventory
```python
# List installed software
software = get_installed_software()

Useful for:
- Audit software licenses
- Identify outdated software
- Find unused applications
- Security vulnerability assessment
- Compliance reporting
```

## Performance Monitoring

### Real-Time Metrics
```python
# Current system performance
performance = get_performance_metrics()

Key metrics:
- CPU: Usage %, per-core breakdown
- RAM: Used/available, commit charge
- Disk: Read/write speeds, queue length
- Network: Bandwidth usage, packets/sec
- Processes: Top CPU/RAM consumers
```

### Performance Baselines
```
Establish normal ranges:
- CPU: <30% average (desktop), <60% (server)
- RAM: <80% used
- Disk queue: <2 (HDD), <1 (SSD)
- Disk response: <10ms (HDD), <1ms (SSD)
- Network latency: <50ms local

Anomalies indicate issues
```

### Resource Alerts
```
Warning thresholds:
⚠️ CPU > 80% for >10 minutes (investigate)
⚠️ RAM > 90% (memory leak or insufficient RAM)
⚠️ Disk queue > 10 (bottleneck)
⚠️ Disk usage > 95% (urgent cleanup)
⚠️ Temperature > 80°C (cooling issue)
```

## Event Log Analysis

### Windows Event Logs
```python
# Review system event logs
events = get_event_log(
    log_name="System",  # or Application, Security
    level="Error",      # or Warning, Information
    hours_back=24
)

Critical logs:
- System: Hardware, drivers, services
- Application: Software errors
- Security: Authentication, access
- Setup: Installations, updates
```

### Common Event IDs
```
Critical Event IDs to monitor:
- 41: Unexpected shutdown
- 1001: System crash (BSOD)
- 6008: Improper shutdown
- 7000: Service failed to start
- 4625: Failed login (security)
- 4720: User account created
- 1074: Shutdown initiated

Event log best practices:
- Review daily for errors
- Investigate warnings
- Archive logs periodically
- Alert on critical events
```

## System Health Checks

### Comprehensive Health Assessment
```python
# Full system health check
health = comprehensive_health_check()

Checks:
✅ Disk errors (chkdsk status)
✅ SMART status (all drives)
✅ Memory test (Windows Memory Diagnostic)
✅ System file integrity (sfc /scannow)
✅ Windows Update status
✅ Driver issues
✅ Service status (critical services running)
✅ Security status (antivirus, firewall)
✅ Pending reboots
```

### System File Integrity
```powershell
# System File Checker
sfc /scannow

Checks:
- Windows system files
- Replaces corrupted files
- Reports integrity violations

Common issues found:
- Corrupted DLLs
- Modified system files
- Missing system files

Run if:
- Unexplained errors
- Program crashes
- System instability
```

### Component Diagnostics
```
Windows built-in tools:
- Memory: mdsched.exe (Windows Memory Diagnostic)
- Disk: chkdsk (File system check)
- System files: sfc /scannow
- Windows Image: DISM /Online /Cleanup-Image
- DirectX: dxdiag
- Network: pathping, tracert, nslookup
```

## Performance Optimization

### Startup Optimization
```python
# Analyze startup programs
startup_programs = get_startup_programs()

Disable unnecessary:
- Cloud sync (OneDrive, Dropbox) - start manually if needed
- Updaters (Adobe, Java) - check manually
- Rarely-used software
- Manufacturer bloatware

Keep enabled:
- Antivirus
- Driver utilities (if needed)
- Critical business software
```

### Service Management
```python
# Review Windows services
services = get_service_status()

Optimization:
- Disable unused services (carefully!)
- Set to Manual instead of Automatic
- Don't disable system-critical services

Services safe to disable:
- Windows Search (if not used)
- Superfetch (on SSDs)
- Print Spooler (if no printer)
- Fax service
- Xbox services (on work PCs)
```

### Background Processes
```
Task Manager analysis:
- Sort by CPU (find intensive processes)
- Sort by Memory (find memory leaks)
- Sort by Disk (find disk bottlenecks)
- Sort by Network (find bandwidth hogs)

Investigate:
- Unknown processes (malware?)
- High resource usage (inefficient software)
- Multiple instances (duplicate processes)
- Legacy software (32-bit on 64-bit)
```

## Network Diagnostics

### Connection Testing
```python
# Test network connectivity
network_status = test_network_connectivity(
    target="google.com",
    include_traceroute=True,
    include_dns=True
)

Returns:
- Ping latency and packet loss
- Traceroute (path to destination)
- DNS resolution status
- Network adapter status
```

### Bandwidth Monitoring
```python
# Monitor network usage
bandwidth = monitor_bandwidth(
    duration_seconds=60
)

Metrics:
- Download/upload speeds
- Packets sent/received
- Connection errors
- Top bandwidth consumers (processes)
```

---

## Diagnostic Workflows

### "Computer is Slow" Diagnosis
```
Systematic approach:
1. Check CPU usage (>80% sustained?)
2. Check RAM usage (>90%?)
3. Check disk queue (>5?)
4. Check disk space (<10% free?)
5. Review startup programs
6. Check for malware
7. Review event logs
8. Consider hardware limitations

Common fixes:
- Add RAM (if maxing out)
- SSD upgrade (if HDD bottleneck)
- Disable startup programs
- Malware removal
- Software uninstall (bloatware)
```

### "Cannot Access File/Folder" Diagnosis
```
Checklist:
1. Check permissions (effective permissions)
2. Check ownership (are you owner?)
3. Check if file is in use (locked)
4. Check path length (<260 chars)
5. Check for hidden/system attributes
6. Check for encryption (EFS)
7. Check disk errors
8. Try safe mode access
```

### "Disk Errors" Diagnosis
```
Investigation:
1. Run chkdsk /scan (online scan)
2. Check SMART status
3. Review event logs (Event ID 7, 11, 15)
4. Listen for clicking (physical damage?)
5. Check cables/connections
6. Run manufacturer diagnostic tool

Actions based on findings:
- Software error: chkdsk /f /r
- Bad sectors: Clone to new drive
- Clicking sounds: IMMEDIATE backup + replace
- Cable issues: Replace cables
```

---

## Diagnostic Tools Reference

### Built-in Windows Tools
```
- perfmon.exe: Performance Monitor
- resmon.exe: Resource Monitor
- taskmgr.exe: Task Manager
- eventvwr.msc: Event Viewer
- diskmgmt.msc: Disk Management
- devmgmt.msc: Device Manager
- msinfo32.exe: System Information
- dxdiag.exe: DirectX Diagnostic
- mdsched.exe: Memory Diagnostic
- cleanmgr.exe: Disk Cleanup
```

### PowerShell Cmdlets
```powershell
# System info
Get-ComputerInfo
Get-WmiObject Win32_OperatingSystem
Get-WmiObject Win32_Processor

# Performance
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Process | Sort-Object CPU -Descending | Select -First 10

# Disk
Get-PhysicalDisk
Get-Disk | Get-StorageReliabilityCounter
Get-Volume

# Network
Get-NetAdapter
Test-Connection
Get-NetTCPConnection
```

## Reporting

### System Health Report
```python
# Generate comprehensive report
report = generate_system_report(
    include_hardware=True,
    include_performance=True,
    include_security=True,
    include_recommendations=True
)

Report includes:
- Executive summary
- Hardware inventory
- Performance metrics
- Security status
- Identified issues
- Recommendations
- Compliance status
```

### Trend Analysis
```python
# Track metrics over time
trends = analyze_performance_trends(
    days=30,
    metrics=["cpu", "ram", "disk_space"]
)

Identify:
- Gradual degradation (aging hardware)
- Sudden changes (new software, malware)
- Cyclic patterns (scheduled tasks)
- Growth trends (disk space)
```

---

## Best Practices

### Regular Diagnostics:
- ✅ Daily: Event log review (errors)
- ✅ Weekly: Disk space check
- ✅ Monthly: Full health check
- ✅ Quarterly: Hardware inspection
- ✅ Yearly: Component refresh planning

### Documentation:
- ✅ Maintain hardware inventory
- ✅ Track software changes
- ✅ Log performance baselines
- ✅ Document issues and resolutions
- ✅ Keep diagnostic reports

### Proactive Monitoring:
- ✅ Set up automated alerts
- ✅ Monitor trends, not just snapshots
- ✅ Establish baselines for comparison
- ✅ Investigate anomalies promptly
- ✅ Plan upgrades based on data

---

**Austrian Engineering**: Measure everything, track trends, prevent problems! 🇦🇹📊

