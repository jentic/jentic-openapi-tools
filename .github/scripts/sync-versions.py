#!/usr/bin/env python3
"""
Sync inter-package dependency versions in a monorepo.

This script updates all jentic-openapi-* package dependency versions
to match the current release version across all package pyproject.toml files.
"""

import re
import sys
from pathlib import Path


def get_current_version(root_pyproject: Path) -> str:
    """Extract the current version from root pyproject.toml."""
    content = root_pyproject.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in root pyproject.toml")
    return match.group(1)


def update_dependency_version(content: str, package_name: str, new_version: str) -> str:
    """
    Update a specific package dependency version in pyproject.toml content.

    Handles formats like:
    - "package~=0.1.0"
    - "package~=0.1.0",
    - "package @ workspace"
    """
    # Match package with version constraint
    pattern = rf'("{package_name}~=)[^"]*(")'
    replacement = rf"\g<1>{new_version}\g<2>"
    return re.sub(pattern, replacement, content)


def sync_versions(root_dir: Path, new_version: str) -> None:
    """Sync all jentic-openapi-* dependency versions to new_version."""
    packages_dir = root_dir / "packages"

    # List of all jentic-openapi packages
    jentic_packages = [
        "jentic-openapi-common",
        "jentic-openapi-datamodels",
        "jentic-openapi-parser",
        "jentic-openapi-traverse",
        "jentic-openapi-transformer",
        "jentic-openapi-transformer-redocly",
        "jentic-openapi-validator",
        "jentic-openapi-validator-redocly",
        "jentic-openapi-validator-spectral",
    ]

    # Update root pyproject.toml
    root_pyproject = root_dir / "pyproject.toml"
    content = root_pyproject.read_text()
    for package in jentic_packages:
        content = update_dependency_version(content, package, new_version)
    root_pyproject.write_text(content)
    print(f"✓ Updated {root_pyproject}")

    # Update all package pyproject.toml files
    updated_count = 0
    for package_dir in packages_dir.iterdir():
        if not package_dir.is_dir():
            continue

        pyproject = package_dir / "pyproject.toml"
        if not pyproject.exists():
            continue

        content = pyproject.read_text()
        original_content = content

        # Update all jentic-openapi-* dependencies
        for package in jentic_packages:
            content = update_dependency_version(content, package, new_version)

        # Only write if something changed
        if content != original_content:
            pyproject.write_text(content)
            print(f"✓ Updated {pyproject}")
            updated_count += 1

    print(f"\n✓ Synced versions to {new_version} in {updated_count + 1} files")


def main() -> int:
    """Main entry point."""
    root_dir = Path(__file__).parent.parent

    try:
        # Get current version from root pyproject.toml
        root_pyproject = root_dir / "pyproject.toml"
        if not root_pyproject.exists():
            print(f"Error: {root_pyproject} not found", file=sys.stderr)
            return 1

        current_version = get_current_version(root_pyproject)
        print(f"Current version: {current_version}")

        # Sync all dependency versions
        sync_versions(root_dir, current_version)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
