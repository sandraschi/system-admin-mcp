#!/usr/bin/env python3
"""
MCPB packaging script for System Admin MCP Server.

Builds a v0.2 MCPB bundle from mcpb/ directory for Claude Desktop distribution.
Run: uv run python mcpb_build.py
"""

import json
import zipfile
from pathlib import Path


def create_mcpb_package():
    root = Path(__file__).parent
    mcpb_dir = root / "mcpb"
    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = mcpb_dir / "manifest.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    name = manifest.get("name", "system-admin-mcp")
    version = manifest.get("version", "0.4.0")
    output_file = dist_dir / f"{name}-v{version}.mcpb"

    inclusions = [
        "manifest.json",
        "server/__main__.py",
        "assets/prompts/system.md",
        "assets/prompts/file_recovery.md",
        "assets/prompts/security_management.md",
        "assets/prompts/system_diagnostics.md",
        "assets/prompts/troubleshooting.md",
        "assets/prompts/volume_maintenance.md",
        "assets/prompts/user.md",
        "assets/prompts/examples.json",
    ]

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for rel_path in inclusions:
            abs_path = mcpb_dir / rel_path
            if abs_path.exists():
                zipf.write(str(abs_path), rel_path)
                print(f"  + {rel_path}")
            else:
                print(f"  - SKIPPED (not found): {rel_path}")

    print(f"\nPackage: {output_file} ({output_file.stat().st_size / 1024:.1f} KB)")
    print("Contents:")
    with zipfile.ZipFile(output_file, "r") as zipf:
        for f in zipf.namelist():
            print(f"  - {f}")
    return True


def main():
    print("=== Building MCPB Package (SOTA v2.0) ===\n")
    if create_mcpb_package():
        print("\nSUCCESS: MCPB package created.")
    else:
        print("\nERROR: Failed to create MCPB package.")
        exit(1)


if __name__ == "__main__":
    main()
