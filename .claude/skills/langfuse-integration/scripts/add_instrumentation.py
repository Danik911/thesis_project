#!/usr/bin/env python3
"""
Add Langfuse @observe decorators to Python functions.

Usage:
    python add_instrumentation.py --target <file_or_directory> [--dry-run]
"""

import argparse
import re
from pathlib import Path


def add_observe_decorator(file_path: Path, dry_run: bool = False) -> int:
    """Add @observe decorators to async/sync functions."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern: async def or def without existing @observe
    pattern = r'(\n)(    |\t)(async )?(def \w+\([^)]*\).*?:)'

    changes = 0
    lines = content.split('\n')
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if line is function definition
        if re.match(r'^\s*(async )?(def \w+)', line):
            # Check previous line for @observe
            if i > 0 and '@observe' not in lines[i-1]:
                # Add decorator
                indent = len(line) - len(line.lstrip())
                decorator = ' ' * indent + '@observe()'

                if not dry_run:
                    new_lines.append(decorator)
                else:
                    print(f"  Would add: {decorator}")

                changes += 1

        new_lines.append(line)
        i += 1

    if not dry_run and changes > 0:
        with open(file_path, 'w') as f:
            f.write('\n'.join(new_lines))

        # Add import if not present
        if 'from langfuse import observe' not in content:
            with open(file_path, 'r') as f:
                content = f.read()

            import_line = 'from langfuse import observe\n'
            with open(file_path, 'w') as f:
                f.write(import_line + content)

    return changes


def main():
    parser = argparse.ArgumentParser(description='Add @observe decorators')
    parser.add_argument('--target', required=True, help='File or directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    args = parser.parse_args()

    target = Path(args.target)

    if target.is_file():
        files = [target]
    else:
        files = list(target.rglob('*.py'))

    total_changes = 0
    for file in files:
        changes = add_observe_decorator(file, args.dry_run)
        if changes > 0:
            mode = "Would modify" if args.dry_run else "Modified"
            print(f"{mode}: {file} ({changes} decorators)")
            total_changes += changes

    print(f"\nTotal: {total_changes} decorators {'would be' if args.dry_run else ''} added")


if __name__ == '__main__':
    main()
