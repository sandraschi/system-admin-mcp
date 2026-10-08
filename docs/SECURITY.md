# Security — system-admin-mcp

Safety-critical surface: every mutating ability here can destroy data, break
logon, or cut the machine off the network. This doc states the threat model,
what is enforced today, and what full hardening still requires.

## Threat model (current)

- **Local agents, no authentication.** Any MCP client (Claude Desktop, IDE
  agents) and any local browser tab can invoke all 60+ tools and all REST
  routes. There is no per-client identity, no token, no approval queue.
- **Consequence**: a confused or prompt-injected agent can kill processes,
  rewrite ACLs, wipe temp trees, or airgap the box. The mitigations below
  raise the cost of accidents but are NOT authorization.

## Enforced today

1. **Read-only kill switch**: `SYSTEMADMIN_READ_ONLY=1` makes every mutating
   op refuse (`mutation_guard.MUTATING_OPS`). Enforced at dispatch AND inside
   each mutating implementation, so neither the portmanteau path nor direct
   `@mcp.tool` calls bypass it. Dry-run previews stay usable.
2. **Mutation audit log**: every mutating attempt appends JSONL to
   `logs/mutations.log` (`SYSTEMADMIN_AUDIT_LOG` overrides) — including
   attempts BLOCKED by read-only mode. Read it after any agent session.
3. **Confirm gates**: `airgap_enable`/`airgap_disable` require `confirm=True`
   on every call (never sticky, never implied). UI uses a two-step armed
   button with an 8s disarm. Pattern for future destructive ops.
4. **Dry-run first**: `disk_cleanup` (and similar) preview with `dry_run=True`
   by default; the function only guards+logs real deletes.
5. **Admin checks**: destructive Windows APIs refuse without elevation
   (`IsUserAnAdmin`), before doing anything.
6. **No security-downgrade ops exist**: there is deliberately NO tool that
   disables Defender, weakens firewall rules, or clears audit logs. Status
   reads only (`get_defender_status`). Adding one requires the auth roadmap
   below, not just code review.

## Airgap design

- Cut = firewall default-outbound BLOCK (all profiles) + `bthserv` stop +
  Bluetooth adapters disabled. Prior state snapshots to
  `data/airgap_state.json` (gitignored) for exact restore.
- **Loopback (127.0.0.1) bypasses Windows Firewall**: this dashboard and the
  backend keep working while every remote path (LAN, Tailscale, internet)
  dies. USB HID keyboards/mice are untouched (neither action targets USB).
- Remote tabs die by design — re-enable from the local console only.

## Full hardening roadmap (NOT done — do not claim otherwise)

1. **Per-client authN**: MCP `Authorization` (OAuth 2.1 / API tokens) +
   browser session binding; reject unauthenticated mutation calls.
2. **Approval workflow**: mutating ops return `pending_approval` with a
   one-time token; a human approves in the webapp; the agent redeems it.
   (Superset of today's `confirm` flag.)
3. **Op allowlists per client**: e.g. "reader" clients get read-only tools
   only, enforced server-side (not just hidden in UI).
4. **Audit forwarding**: ship `mutations.log` to Windows Event Log / syslog
   (WORM-ish); alert on blocked-attempt bursts (prompt-injection signal).
5. **Airgap interlock**: require physical presence proof (console session,
   not RDP) for `airgap_disable`.
