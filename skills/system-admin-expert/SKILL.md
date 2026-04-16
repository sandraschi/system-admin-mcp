# Skill: Windows System Administration Expert

### Name: system-admin-expert
### Description: Expert in Windows system administration — elevated operations, NTFS file recovery, security/ACL management, disk maintenance, service orchestration, and process diagnostics.

---

## Overview

This skill provides operational logic and safe-mode patterns for managing Windows systems at an industrial grade via the `system_admin` portmanteau tool. It prioritizes safety (dry-run first, audit before modify) and leverages SEP-1577 sampling for autonomous diagnostics.

---

## Tool Interaction Patterns

### 1. System Diagnostics (`system_admin`)
- **Baseline**: Always run `health_check` and `get_performance_metrics` before any remediation
- **Events**: Query `get_event_log` with `level="Error"` for System and Application logs
- **Sequence**: health → performance → events → process analysis → remediation

### 2. Security & Permissions
- **Audit first**: `get_permissions` / `audit_permissions` before any ACL change
- **Least privilege**: Grant minimum required rights; use groups not individuals
- **Ownership**: `take_ownership` only when explicitly needed; restore permissions after
- **Dry-run**: Use `dry_run=True` where available; document current state before changes

### 3. Volume Maintenance
- **SSD rule**: NEVER `defragment_disk` on SSDs — use `optimize_ssd` (TRIM) instead
- **Health first**: Always `check_disk_health` (SMART) before optimization
- **Cleanup**: `disk_cleanup` with `dry_run=True` first; review before committing
- **Recovery**: Stop all writes immediately; recover to a *different* drive than source

### 4. Service & Process Management
- **State check**: `get_service_info` before start/stop; check dependencies
- **Process kill**: Confirm PID with `analyze_process` before `kill_process`; prefer `force=False` first
- **Startup**: `list_startup_programs` regularly; disable non-essential items

---

## Agentic Workflows (FastMCP 3.2+)

### Autonomous Diagnostics Pattern (SEP-1577)
1. **Inventory**: `system_admin(operation="get_comprehensive_diagnostics")` — full snapshot
2. **Event scan**: `system_admin(operation="get_recent_event_errors")` — recent failures
3. **Sampling**: `ctx.sample()` with system prompt "You are a Windows admin expert. Analyze this inventory and identify the top 3 issues with remediation steps."
4. **Act**: Execute sampling recommendations using `system_admin` operations
5. **Verify**: Re-run `health_check` to confirm improvement

### "System is Slow" Autonomous Flow
1. `get_performance_metrics` → identify bottleneck (CPU/RAM/disk)
2. `list_processes` sort_by=bottleneck → identify culprit
3. `ctx.sample()` for root cause analysis
4. Apply fix (kill process / adjust service / disk cleanup)
5. Monitor via `get_performance_metrics` again

---

## Safety Protocols
1. **Dry-run mandatory**: Always `dry_run=True` for cleanup, defrag, and bulk permission changes
2. **Audit trail**: Document permissions before ACL changes
3. **Recovery order**: scan_volume → recover to different drive → validate_recovery
4. **Sampling before bulk actions**: Use `ctx.sample()` to confirm policy alignment before mass remediation
5. **Event log correlation**: Cross-reference operation timestamps with event log entries

---

## Port Reference
- Web dashboard: **10860** (frontend), **10861** (backend API)
- MCP transport: stdio (Claude Desktop) or HTTP port 10861

---

*Author: Sandra Schipal (Vienna, AT)*
*Industrial Grade v0.3.0 — FastMCP 3.2 Full Conformance*
