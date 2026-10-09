import logging
import os
import sys

# Frozen (PyInstaller onefile, console=False): sys.stderr/stdout can be None,
# which crashes logging/uvicorn at import. Point them at devnull first.
# (Tauri checklist §J + isatty pitfall.)
# A persistent boot log is ALSO opened (LOCALAPPDATA) so frozen failures are
# diagnosable; main.py attaches it as a FileHandler via SYSTEMADMIN_LOG_FILE.
if getattr(sys, "frozen", False):
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    try:
        import time as _time
        from pathlib import Path as _Path

        _base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or os.path.expandvars("%TEMP%")
        _logdir = _Path(_base) / "ai.fleet.system-admin-mcp" / "logs"
        _logdir.mkdir(parents=True, exist_ok=True)
        _logpath = _logdir / "backend.log"
        os.environ.setdefault("SYSTEMADMIN_LOG_FILE", str(_logpath))
        with open(_logpath, "a", encoding="utf-8") as _fh:
            _fh.write(f"\n=== boot {_time.strftime('%Y-%m-%dT%H:%M:%S')} frozen={sys.executable} ===\n")
    except Exception:
        # Boot-logging is best-effort (frozen profile may be read-only);
        # never let telemetry break startup, but don't swallow silently.
        logging.getLogger("system_admin_mcp.boot").debug("Frozen boot log unavailable", exc_info=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Eager stdlib C extensions: PyInstaller misses lazy imports (_strptime pitfall).
import _datetime  # noqa: F401
import _strptime  # noqa: F401

# Freeze the mcp bootstrap before fastmcp touches it (frozen Image crash pitfall).
import mcp.types  # noqa: F401

from system_admin_mcp.main import main

if __name__ == "__main__":
    main()
