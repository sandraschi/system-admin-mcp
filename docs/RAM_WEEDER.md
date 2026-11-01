# RAM Weeder

Finds leaked processes by **rule**, reports them, and kills only what you approve.
Added 2026-10-31 after Goliath ran at about 95% CPU / 92% RAM with three WizTree
instances (about 12 GB), 21 forgotten Godot game windows, seven orphaned headless Godot
servers and around 150 idle `cmd`/`conhost` pairs.

Size alone is the wrong signal: one WizTree at 4 GB is fine, three is the leak. So the
weeder asks *why* a process is still there.

## Rules

| Rule | Matches | Unattended sweep |
|------|---------|------------------|
| `orphan_engine` | headless Godot / headless browser engine whose launcher is gone, older than 30 min | **yes** (only this one) |
| `orphan_dev` | idle `node`/`bun`/`python`/`uv`/`pytest`/`vite`/... whose parent is gone, older than 1 h, not serving a port listed in `WEBAPP_PORTS.md` | no |
| `duplicate_app` | 3+ instances of a single-use app (WizTree, Task Manager, Process Explorer, WinDirStat, ...): all but the newest | no |
| `duplicate_game` | 2+ windowed Godot games of the same project (`--path`): all but the newest | no |
| `orphan_game` | windowed Godot game open over 2 h whose launcher is gone | no |
| `stale_headless` | any `--headless` process running over 6 h | no |
| `shell_debris` | idle `cmd`/`conhost`/`powershell` with no children and no parent, older than 1 h | no |
| `unregistered_port` | dev server listening only on ports not in `WEBAPP_PORTS.md` | no |

A process matches at most one rule (first in the table wins).

**Never candidates:** Windows system processes, the protect list (Claude, OpenCode,
Cursor, Windsurf, VS Code, Zed, Plex, Docker, Podman, WSL/vmmem, RustDesk, Tailscale,
Ollama, LM Studio, OneDrive, browsers), this server and its ancestors, and processes of
other users. Extend the protect list with `SYSTEMADMIN_WEEDER_PROTECT=name1,name2`.

## Using it

- **Dashboard:** `/weeder` (sidebar: Manage > RAM Weeder). Shows memory pressure, a chip
  per rule (click to select all of that rule), and the candidate table with reason,
  size, age, parent and command line. Only auto-eligible candidates are preselected.
  Kill asks for a second click with the total MB.
- **MCP:** `ram_weeder_tool(operation="scan")`, then
  `ram_weeder_tool(operation="kill", pids=[...], confirm=True)` with the pids the user
  approved; `ram_weeder_tool(operation="sweep", apply=True)` for orphaned engines only.
- **REST:** `GET /api/weeder/scan`, `POST /api/weeder/kill`
  (`{"targets": [{"pid", "create_time"}], "confirm": true}`), `POST /api/weeder/sweep`
  (`{"apply": false}` previews).

## Safety

- Kill re-scans first. A target is skipped if it is gone, no longer matches a rule,
  became protected, or its pid now belongs to a different process (create time differs).
- The whole process tree is terminated (5 s grace, then killed).
- Every kill and applied sweep is appended to the mutation audit log
  (`logs/mutations.log`); `SYSTEMADMIN_READ_ONLY=1` blocks kills and applied sweeps,
  scans and dry runs keep working.

## Memory pressure

Every scan and sweep reports `ok` / `warn` (>= 85% used) / `critical` (>= 93%).

## Scheduled sweep

`scripts/weeder_sweep.py` runs one sweep, appends a JSON line to `logs/weeder.log` and
exits 0 / 1 / 2 for ok / warn / critical, so a scheduler can alert on the exit code:

```powershell
uv run python scripts/weeder_sweep.py            # report only
uv run python scripts/weeder_sweep.py --apply    # kill orphaned headless engines
schtasks /Create /TN "fleet\ram-weeder-sweep" /SC MINUTE /MO 30 /TR "\"%USERPROFILE%\.local\bin\uv.exe\" run --directory D:\Dev\repos\system-admin-mcp python scripts\weeder_sweep.py --apply"
```

## Fix leaks at the source too

The weeder is a safety net. Launchers should not leak in the first place: gamecraft now
puts its viewer and MCP server in a kill-on-close Job Object and closes the previous game
on each Start (see gamecraft `AGENTS.md`, "Never leave engines running").

## Status

- 19 unit tests on synthetic snapshots (`tests/test_ram_weeder.py`), run in a Linux VM
  against the module in isolation; a live `scan()` and dry-run `sweep()` ran there too.
- Not yet run on Goliath: the full `just test` suite and a live scan. New Python
  processes on Goliath were taking minutes to start at the time (see the report in the
  session); retry when that is resolved.
