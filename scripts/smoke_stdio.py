"""Stdio MCP handshake smoke test: spawn a server command, initialize, list tools.

Usage:  python scripts/smoke_stdio.py <command> [args...]
Exit 0 if the server answers `initialize` and `tools/list` with >= 1 tool within the timeout.
stdout of the server must carry only JSON-RPC frames; any non-JSON line on stdout fails the test.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading

TIMEOUT_S = 90


def _read_frame(proc: subprocess.Popen[str], timeout: float) -> dict:
    result: dict = {}

    def target() -> None:
        line = proc.stdout.readline()  # type: ignore[union-attr]
        if not line:
            result["error"] = "server closed stdout"
            return
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            result["error"] = f"non-JSON line on stdout (stdout must be JSON-RPC only): {line[:200]!r}"
            return
        if not isinstance(frame, dict) or frame.get("jsonrpc") != "2.0":
            result["error"] = f"non-JSON-RPC line on stdout (log leak?): {line[:200]!r}"
            return
        result["frame"] = frame

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"no frame within {timeout}s")
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["frame"]


def _send(proc: subprocess.Popen[str], msg: dict) -> None:
    proc.stdin.write(json.dumps(msg) + "\n")  # type: ignore[union-attr]
    proc.stdin.flush()  # type: ignore[union-attr]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    proc = subprocess.Popen(
        sys.argv[1:],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    stderr_buf: list[str] = []

    def _drain_stderr() -> None:
        # An undrained stderr pipe fills up and blocks the server (logs go to stderr).
        for line in proc.stderr:  # type: ignore[union-attr]
            stderr_buf.append(line)

    threading.Thread(target=_drain_stderr, daemon=True).start()
    try:
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "smoke_stdio", "version": "0"},
                },
            },
        )
        init = _read_frame(proc, TIMEOUT_S)
        server = init.get("result", {}).get("serverInfo", {})
        print(f"initialize ok: {server.get('name')} {server.get('version')}")
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = _read_frame(proc, TIMEOUT_S).get("result", {}).get("tools", [])
        print(f"tools/list ok: {len(tools)} tools")
        return 0 if tools else 1
    except Exception as exc:
        print(f"FAIL: {exc}")
        if stderr_buf:
            print("stderr tail:", "".join(stderr_buf)[-800:])
        return 1
    finally:
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
