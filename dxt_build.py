"""
DXT packaging script for System Admin MCP.

This script creates a DXT package containing the user bridge component.
The elevated service must be installed separately using the MSI installer.
"""

import os
import sys
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
PACKAGE_NAME = "system-admin-mcp"
VERSION = "1.0.0"
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
PACKAGE_DIR = BUILD_DIR / PACKAGE_NAME

# Source directories to include in the package
SOURCE_DIRS = [
    "src/system_admin_mcp/user_bridge",
    "src/system_admin_mcp/__init__.py",
]

# Additional files to include
ADDITIONAL_FILES = [
    "README.md",
    "LICENSE",
    "requirements.txt",
    "dxt_manifest.json"
]

def load_manifest() -> Dict[str, Any]:
    """Load and validate the DXT manifest."""
    try:
        with open("dxt_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        # Validate required fields
        required_fields = ["name", "version", "description", "entry_point"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field in manifest: {field}")
        
        return manifest
    except Exception as e:
        print(f"Error loading manifest: {e}", file=sys.stderr)
        sys.exit(1)

def create_build_directories() -> None:
    """Create necessary build directories."""
    # Clean and create build directories
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

def copy_source_files() -> None:
    """Copy source files to the build directory."""
    print("Copying source files...")
    
    # Copy source directories
    for src_dir in SOURCE_DIRS:
        src_path = Path(src_dir)
        if src_path.is_dir():
            dst_path = PACKAGE_DIR / src_path.name
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            dst_path = PACKAGE_DIR / src_path.name
            shutil.copy2(src_path, dst_path)
    
    # Copy additional files
    for file_path in ADDITIONAL_FILES:
        if Path(file_path).exists():
            shutil.copy2(file_path, PACKAGE_DIR / Path(file_path).name)

def create_package() -> str:
    """Create the DXT package.
    
    Returns:
        Path to the created package file
    """
    print("Creating DXT package...")
    
    # Get package name and version from manifest
    manifest = load_manifest()
    package_name = manifest["name"]
    version = manifest["version"]
    
    # Create package filename
    package_filename = f"{package_name}-{version}.dxt"
    package_path = DIST_DIR / package_filename
    
    # Create zip file
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files in the build directory
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(BUILD_DIR)
                zipf.write(file_path, arcname)
    
    print(f"Created package: {package_path}")
    return str(package_path)

def main() -> int:
    """Main entry point for the build script."""
    print(f"Building {PACKAGE_NAME} v{VERSION}")
    
    try:
        # Set up build environment
        create_build_directories()
        
        # Copy source files
        copy_source_files()
        
        # Create package
        package_path = create_package()
        
        print(f"\nBuild successful!")
        print(f"Package created at: {package_path}")
        return 0
    
    except Exception as e:
        print(f"\nBuild failed: {e}", file=sys.stderr)
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
