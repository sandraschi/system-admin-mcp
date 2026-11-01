"""Unattended RAM weeder pass, meant for Windows Task Scheduler.

Kills only `orphan_engine` candidates (headless Godot/browser engines whose launcher
is gone, older than 30 min) when run with --apply; otherwise just reports. Logs every
run as one JSON line to logs/weeder.log and exits with:

  0  memory ok
  1  memory warn (>= 85% used)
  2  memory critical (>= 93% used)

so a scheduler or monitoring hook can alert on the exit code.

  uv run python scripts/weeder_sweep.py            # dry run
  uv run python scripts/weeder_sweep.py --apply    # kill orphaned headless engines

Schedule every 30 minutes (run once from an elevated or normal shell):

  schtasks /Create /TN "fleet\\ram-weeder-sweep" /SC MINUTE /MO 30 ^
    /TR "\"%USERPROFILE%\\.local\\bin\\uv.exe\" run --directory D:\\Dev\\repos\\system-admin-mcp python scripts\\weeder_sweep.py --apply"
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from system_admin_mcp.tools import ram_weeder


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="kill orphaned headless engines (default: report only)")
    args = ap.parse_args()
    result = ram_weeder.sweep(apply=args.apply)
    level = result["pressure"]["level"]
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "applied": args.apply,
        "pressure": result["pressure"],
        "eligible": [{"pid": c["pid"], "name": c["name"], "rss_mb": c["rss_mb"]} for c in result["eligible"]],
        "killed": [k["pid"] for k in (result.get("kill") or {}).get("killed", [])],
    }
    log = REPO / "logs" / "weeder.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    sys.stdout.write(json.dumps(record, indent=2) + "\n")
    return {"ok": 0, "warn": 1, "critical": 2}[level]


if __name__ == "__main__":
    sys.exit(main())
