"""
System Admin MCP - FastMCP 3.2 Prompts Registry
4 high-quality prompts (3-4-100 rule) derived from assets/prompts/ content.
"""

from fastmcp import FastMCP


def register_all_prompts(mcp: FastMCP) -> None:
    """Register all SOTA 2026 prompt templates."""

    @mcp.prompt(
        name="system_diagnostics_expert",
        description=(
            "Load expert guidance for systematic Windows diagnostics: hardware, OS, "
            "performance, event logs, health checks, and diagnostic workflows."
        ),
        tags={"diagnostics", "performance", "health", "windows"},
    )
    def system_diagnostics_expert(focus: str = "general") -> str:
        """Expert guide for Windows system diagnostics and health analysis."""
        base = """
### System Admin MCP — Diagnostics Expert Mode

You are a senior Windows systems engineer. Use the `system_admin` portmanteau tool for all operations.

**Primary diagnostic sequence:**
1. `system_admin(operation="health_check")` — baseline system health
2. `system_admin(operation="get_performance_metrics")` — real-time CPU/RAM/disk/network
3. `system_admin(operation="get_recent_event_errors", log_name="System")` — recent errors
4. `system_admin(operation="get_top_resource_processes")` — top consumers

**Performance thresholds to watch:**
- CPU > 80% sustained → investigate with `list_processes` sorted by cpu
- RAM > 90% → memory leak or insufficient RAM
- Disk queue > 5 → I/O bottleneck
- Disk usage > 95% → urgent cleanup via `disk_cleanup`

**Event IDs worth flagging:** 41 (unexpected shutdown), 7000 (service failure), 4625 (failed login), 1001 (BSOD)
"""
        if focus == "performance":
            return base + """
**Performance deep-dive:**
- `system_admin(operation="get_performance_metrics")` for real-time metrics
- `system_admin(operation="list_processes", sort_by="cpu")` for CPU hogs
- `system_admin(operation="list_processes", sort_by="memory")` for RAM hogs
- Use `ctx.sample()` to interpret anomalies and recommend fixes
"""
        if focus == "events":
            return base + """
**Event log focus:**
- Query System, Application, and Security logs via `get_event_log`
- Cross-reference Event IDs with recent changes (updates, installs, config)
- Correlate timestamps with user-reported issues
"""
        return base

    @mcp.prompt(
        name="security_hardening_expert",
        description=(
            "Load expert guidance for Windows security: NTFS permissions, ACLs, ownership, "
            "least-privilege enforcement, and security auditing."
        ),
        tags={"security", "permissions", "acl", "hardening", "windows"},
    )
    def security_hardening_expert(scope: str = "general") -> str:
        """Expert guide for Windows security management and hardening."""
        base = """
### System Admin MCP — Security Expert Mode

You are a Windows security specialist. Use `system_admin` for all permission and security operations.

**Core security workflow:**
1. `system_admin(operation="audit_permissions", path="<target>")` — baseline audit
2. `system_admin(operation="get_permissions", path="<target>")` — current ACLs
3. Apply least privilege: `set_permissions` with minimum required rights
4. Verify: re-audit after changes

**Principle of Least Privilege (PoLP):**
- Users get minimum required permissions — never Full Control unless justified
- Assign permissions to groups, not individuals
- Use Read-only where write is not needed
- Remove old employee/service account entries immediately

**Safe mode for destructive operations:**
- Always `get_permissions` first (document current state)
- Test on a single file before recursive application
- `dry_run=True` where available before committing
"""
        if scope == "ownership":
            return base + """
**Ownership workflow:**
- `system_admin(operation="take_ownership", path="<target>")` to reclaim
- After ownership: grant yourself Full Control, then re-restrict
- Recursive ownership: use carefully — can break system files
"""
        if scope == "audit":
            return base + """
**Audit focus:**
- `system_admin(operation="audit_permissions", path="<target>")` for ACL review
- `system_admin(operation="audit_network_ports")` for open port inventory
- Look for: Everyone=FullControl, missing inheritance, orphaned SIDs
"""
        return base

    @mcp.prompt(
        name="system_troubleshooter",
        description=(
            "Systematic troubleshooting guide for Windows issues: access denied, "
            "disk errors, performance problems, service failures, and BSOD recovery."
        ),
        tags={"troubleshooting", "diagnosis", "recovery", "windows"},
    )
    def system_troubleshooter(problem: str = "general") -> str:
        """Systematic troubleshooting guide for common Windows administration problems."""
        base = """
### System Admin MCP — Troubleshooter Mode

You are a Windows troubleshooting specialist. Work systematically: observe → diagnose → fix → verify.

**General diagnostic order:**
1. `system_admin(operation="get_recent_event_errors")` — what does the system know?
2. `system_admin(operation="get_performance_metrics")` — resource pressure?
3. `system_admin(operation="list_processes", sort_by="cpu")` — process suspects?
4. Use `ctx.sample()` to reason about findings before acting

**Safe operations first rule:** always `health_check` and `get_event_log` before any remediation.
"""
        if problem == "access_denied":
            return base + """
**"Access Denied" checklist:**
1. `system_admin(operation="get_permissions", path="<target>")` — what do ACLs say?
2. Check effective permissions vs. inherited (inheritance may override)
3. `system_admin(operation="take_ownership")` if ownership is wrong
4. Check if file is locked: `system_admin(operation="list_processes")` for handles
5. UAC elevation required? Run server as administrator
"""
        if problem == "performance":
            return base + """
**"System is slow" checklist:**
1. CPU > 80%? → `list_processes` sort by cpu, identify culprit
2. RAM > 90%? → `list_processes` sort by memory, check for leaks
3. Disk queue high? → `check_disk_health` for SMART status
4. Disk near full? → `analyze_disk_usage` then `disk_cleanup` dry_run=True first
5. Too many startup items? → `list_startup_programs`
"""
        if problem == "services":
            return base + """
**Service failure checklist:**
1. `system_admin(operation="get_service_info", service_name="<name>")` — current state
2. `system_admin(operation="get_event_log", log_name="System", level="Error")` — failure events
3. Check dependencies: a service may fail because its dependency is stopped
4. `system_admin(operation="start_service", service_name="<name>", wait_timeout=30)`
5. If recurring: `set_service_startup` to Automatic, investigate root cause
"""
        return base

    @mcp.prompt(
        name="volume_maintenance_expert",
        description=(
            "Expert guidance for Windows volume maintenance: disk health, cleanup, "
            "defragmentation, SSD optimization, and NTFS file recovery."
        ),
        tags={"volume", "disk", "recovery", "ntfs", "maintenance"},
    )
    def volume_maintenance_expert(volume_type: str = "general") -> str:
        """Expert guide for Windows volume maintenance and file recovery."""
        base = """
### System Admin MCP — Volume Maintenance Expert Mode

You are a Windows storage specialist. Use `system_admin` for all disk and volume operations.

**Maintenance sequence (safe order):**
1. `system_admin(operation="check_disk_health", drive="C:")` — SMART status first
2. `system_admin(operation="get_volume_info", drive="C:")` — capacity and filesystem
3. `system_admin(operation="analyze_disk_usage", drive="C:")` — space breakdown
4. `system_admin(operation="disk_cleanup", drive="C:", dry_run=True)` — preview before commit

**SSD vs HDD rules:**
- SSDs: use `optimize_ssd` (TRIM), NEVER `defragment_disk`
- HDDs: `defragment_disk` OK, but only when >10% fragmented
- Always `check_disk_health` before any optimization
"""
        if volume_type == "recovery":
            return base + """
**NTFS File Recovery workflow:**
1. STOP all writes to the affected drive immediately
2. `system_admin(operation="scan_volume", drive="C:", file_pattern="*.docx")` — locate MFT entry
3. `system_admin(operation="recover_file", source_path="<mft_path>", destination_path="D:/Recovery/")` — recover to different drive
4. `system_admin(operation="validate_recovery", destination_path="D:/Recovery/file.docx")` — verify integrity
5. Work on a copy, never the original drive

**Recovery success factors:** recent deletion, no overwrites since deletion, NTFS volume (not FAT32/exFAT)
"""
        if volume_type == "cleanup":
            return base + """
**Disk cleanup workflow:**
1. `system_admin(operation="analyze_top_folder_sizes", path="C:\\")` — find space hogs
2. `system_admin(operation="disk_cleanup", drive="C:", dry_run=True)` — preview what will be freed
3. Review results, then re-run with `dry_run=False` to commit
4. Target: keep >15% free on system drive for optimal performance
"""
        return base


__all__ = ["register_all_prompts"]
