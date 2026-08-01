# System Admin MCP — Copilot Instructions

You can manage this Windows machine through MCP tools: services, processes, NTFS file
recovery, ACLs/permissions, disk health, event logs, startup programs, and taskbar
settings.

**Before starting work:**
1. Check system health: `system_admin(operation="health_check")`
2. List services if relevant: `system_admin(operation="list_services", filter_status="running")`

**At end of work:**
- Summarize any changes made (services, permissions, recovered files)
- Note that recovery/defrag/ownership operations require an elevated server.
