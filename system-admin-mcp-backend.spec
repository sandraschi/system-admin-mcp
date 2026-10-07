import sys, os
site_pkgs = os.path.abspath('.venv/Lib/site-packages')
if site_pkgs not in sys.path:
    sys.path.insert(0, site_pkgs)

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

import glob as _glob

datas = [("src/system_admin_mcp", "system_admin_mcp")]
for pkg in ("fastmcp", "fastapi", "uvicorn", "pydantic", "starlette", "httpx", "psutil", "docket", "burner_redis", "mcp", "opentelemetry"):
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

# Include burner_redis native extension (.pyd) so docket can import it
_burner_pyds = _glob.glob(os.path.join(site_pkgs, "burner_redis", "*.pyd"))
_burner_bins = [(_pyd, "burner_redis") for _pyd in _burner_pyds]

a = Analysis(
    ['run_server.py'],
    pathex=["src", site_pkgs],
    binaries=_burner_bins,
    datas=datas,
    hiddenimports=[
        "_datetime",
        "mcp.types",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "system_admin_mcp.main",
        "system_admin_mcp.server",
        "_strptime",
        "joserfc",
        "joserfc.jwk",
        "joserfc.jwt",
        "cachetools",
        "burner_redis",
        "burner_redis.lock",
        "burner_redis.pipeline",
        "burner_redis.pubsub",
        "docket",
        "docket.docket",
        "docket._redis",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="system-admin-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
