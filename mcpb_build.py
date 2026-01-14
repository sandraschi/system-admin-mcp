#!/usr/bin/env python3
"""
MCPB packaging script for System Admin MCP Server.

This script creates a minimal MCPB package with NO dependencies.
IMPORTANT: MCPB packages contain NO dependencies - handled by MCPB runtime.
"""

import json
import zipfile
from pathlib import Path


def create_mcpb_package():
    """Create a minimal MCPB package - NO dependencies included."""
    project_root = Path(__file__).parent
    mcpb_dir = project_root / "mcpb"
    dist_dir = project_root / "dist"

    # Ensure dist directory exists
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Read manifest
    manifest_path = mcpb_dir / "manifest.json"
    if not manifest_path.exists():
        print("[ERROR] MCPB manifest not found")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    package_name = manifest.get('name', 'system-admin-mcp')
    version = manifest.get('version', '0.1.0')
    output_file = dist_dir / f"{package_name}-{version}.mcpb"

    # Create minimal MCPB package
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Write the manifest
        zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Add the main server file ONLY (NO dependencies!)
        server_path = mcpb_dir / "server" / "__main__.py"
        if server_path.exists():
            zipf.write(str(server_path), "server/__main__.py")
        else:
            print("[WARNING] Main server file not found")

    print("[SUCCESS] MCPB package created successfully!")
    print(f"Package: {output_file}")
    print(f"[WARNING] IMPORTANT: This MCPB package contains NO dependencies!")
    print(f"   The MCPB runtime handles all Python package dependencies.")

    # List contents
    print("\nPackage contents:")
    with zipfile.ZipFile(output_file, 'r') as zipf:
        for file in zipf.namelist():
            print(f"- {file}")

    return True


def main():
    """Main entry point."""
    print("\n=== Building MCPB Package (NO dependencies) ===\n")

    success = create_mcpb_package()

    if success:
        print("\n[SUCCESS] MCPB package created!")
    else:
        print("\n[ERROR] Failed to create MCPB package")
        exit(1)


if __name__ == "__main__":
    main()
