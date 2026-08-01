---
name: session-context
description: System Admin MCP tool awareness — health check and service listing at session start
---

## Session Context (System Admin MCP)

You can manage this Windows machine: services, processes, NTFS file recovery, ACLs,
disk health, event logs, startup programs, and taskbar settings.

**Before starting work:**
1. Check system health: `system_admin(operation="health_check")`
2. List services if relevant: `system_admin(operation="list_services", filter_status="running")`

**At end of work, save state:**
- Summarize any changes made (services started/stopped, permissions changed, files recovered)
- Flag anything needing elevation: run the server as Administrator for recovery/defrag/ownership ops
