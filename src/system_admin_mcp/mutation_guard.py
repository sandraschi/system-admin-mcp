"""Mutation guardrails for system-admin-mcp (safety-critical surface).

Two mechanisms, both deliberately boring:

1. READ-ONLY MODE: ``SYSTEMADMIN_READ_ONLY=1`` makes every mutating operation
   refuse with an error. For locked-down instances (shared box, untrusted
   agent session). Checked two ways so neither call path bypasses it:
   (a) portmanteau dispatch consults MUTATING_OPS, (b) each mutating
   implementation calls :func:`require_mutable` first (covers direct
   @mcp.tool calls that skip dispatch).

2. MUTATION AUDIT LOG: every mutating implementation calls
   :func:`audit_mutation` with operation + outcome. JSONL at
   ``logs/mutations.log`` (``SYSTEMADMIN_AUDIT_LOG`` overrides, used by
   tests). Tamper-evident by convention (append-only, rotated never) —
   full WORM/auditd forwarding is a later hardening step (see docs/SECURITY.md).

Full per-client authN/authZ is NOT implemented here — tracked in
docs/SECURITY.md. Until then: an agent must never invoke a mutating op
without telling the user first; confirm-gated ops (airgap) additionally
require an explicit ``confirm=True`` argument every call.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

READ_ONLY_ENV = "SYSTEMADMIN_READ_ONLY"
AUDIT_LOG_ENV = "SYSTEMADMIN_AUDIT_LOG"

# Dispatch operation names that change system state. Read-only probes,
# dry-run previews, and status queries are NOT listed (dry_run=True paths
# must stay usable for "show me what WOULD happen" flows).
MUTATING_OPS = frozenset(
    {
        # File recovery (writes recovered files)
        "recover_file",
        "batch_recover",
        # ACLs / ownership
        "set_permissions",
        "remove_permission",
        "take_ownership",
        # Disk maintenance
        # NOTE: disk_cleanup is NOT listed: its dry_run=True previews must stay
        # usable in read-only mode. The function itself guards+logs only real
        # deletes (dry_run=False). Same pattern for any future previewable op.
        "defragment_disk",
        "optimize_ssd",
        # Services / processes
        "start_service",
        "stop_service",
        "set_service_startup",
        "kill_process",
        # Startup / taskbar
        "add_startup_program",
        "remove_startup_program",
        "set_taskbar_autohide",
        "kill_taskbar_blocking_processes",
        # Filesystem watches: gated inside manage_filesystem_watch for
        # sub-operations start/stop (these names only ever come from there).
        "manage_watch_start",
        "manage_watch_stop",
        # Airgap (network + bluetooth kill switch)
        "airgap_enable",
        "airgap_disable",
    }
)


class ReadOnlyError(RuntimeError):
    """Raised when a mutating op is attempted with read-only mode on."""


def read_only_enabled() -> bool:
    return os.getenv(READ_ONLY_ENV, "").strip() == "1"


def require_mutable(operation: str) -> None:
    """Refuse mutating ops when read-only mode is on. No-op otherwise."""
    if operation in MUTATING_OPS and read_only_enabled():
        raise ReadOnlyError(f"operation '{operation}' is blocked: {READ_ONLY_ENV}=1 (read-only mode)")


def audit_log_path() -> Path:
    override = os.getenv(AUDIT_LOG_ENV, "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent.parent / "logs" / "mutations.log"


def audit_mutation(operation: str, details: dict[str, Any] | None = None) -> None:
    """Append one JSONL audit record. Never raises (audit must not break ops)."""
    record: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "operation": operation,
    }
    if details:
        record.update(details)
    try:
        path = audit_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    except Exception:
        logger.debug("mutation audit write failed", exc_info=True)
