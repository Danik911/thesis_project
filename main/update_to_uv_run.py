#!/usr/bin/env python3
"""
Update all Python execution scripts to use 'uv run python' instead of 'python'.
This ensures proper Phoenix instrumentation is active.
"""

import re
from pathlib import Path


def update_file(file_path, dry_run=False):
    """Update a single file to use uv run python."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Skip binary files
        return False, "Binary file"

    original_content = content
    changes_made = []

    # Pattern to match python execution commands
    patterns = [
        # Match 'python3 script.py' or 'python script.py'
        (r"\bpython3?\s+([^\s]+\.py)", r"uv run python \1"),
        # Match 'python3 -m module' or 'python -m module'
        (r"\bpython3?\s+-m\s+", r"uv run python -m "),
        # Match shebang lines with python
        (r"^#!/usr/bin/env python3?$", r"#!/usr/bin/env uv run python"),
        # Match direct python calls in shell scripts
        (r"^\s*python3?\s+", r"uv run python "),
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, content, re.MULTILINE):
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                changes_made.append(f"Updated pattern: {pattern}")
                content = new_content

    if content != original_content:
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        return True, changes_made

    return False, "No changes needed"


def main():
    """Update all relevant files in the project."""
    project_root = Path(__file__).parent.parent

    # File patterns to check
    file_patterns = [
        "**/*.sh",
        "**/*.bat",
        "**/*.cmd",
        "**/*.py",  # For shebangs and subprocess calls
        "**/*.yml",
        "**/*.yaml",
        "**/Makefile",
        "**/makefile",
    ]

    # Directories to exclude
    exclude_dirs = {
        ".venv", "venv", "__pycache__", ".git", "node_modules",
        "build", "dist", ".tox", ".pytest_cache", ".mypy_cache"
    }

    print("Scanning for files to update...")
    files_to_update = []

    for pattern in file_patterns:
        for file_path in project_root.rglob(pattern):
            # Skip excluded directories
            if any(part in exclude_dirs for part in file_path.parts):
                continue

            # Skip this script itself
            if file_path.name == "update_to_uv_run.py":
                continue

            files_to_update.append(file_path)

    print(f"\nFound {len(files_to_update)} files to check")

    # First pass: dry run to show what would be changed
    print("\n--- DRY RUN ---")
    files_with_changes = []

    for file_path in files_to_update:
        changed, info = update_file(file_path, dry_run=True)
        if changed:
            files_with_changes.append((file_path, info))
            print(f"Would update: {file_path.relative_to(project_root)}")
            for change in info:
                print(f"  - {change}")

    if not files_with_changes:
        print("\nNo files need updating!")
        return

    # Auto-proceed with updates
    print(f"\n{len(files_with_changes)} files will be updated.")
    print("Auto-proceeding with updates...")

    # Second pass: actual updates
    print("\n--- UPDATING FILES ---")
    success_count = 0

    for file_path, _ in files_with_changes:
        changed, info = update_file(file_path, dry_run=False)
        if changed:
            success_count += 1
            print(f"Updated: {file_path.relative_to(project_root)}")

    print(f"\nSuccessfully updated {success_count} files.")

    # Special instructions for specific files
    print("\n--- ADDITIONAL NOTES ---")
    print("1. The main.py file should be run with: uv run python main/main.py")
    print("2. Test scripts should use: uv run pytest")
    print("3. Any Makefile or CI/CD scripts may need manual review")
    print("4. Update any documentation that shows Python commands")


if __name__ == "__main__":
    main()
