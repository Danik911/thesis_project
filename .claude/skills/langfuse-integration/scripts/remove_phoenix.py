#!/usr/bin/env python3
"""Remove Phoenix imports and references from codebase."""

import argparse
import re
from pathlib import Path


def remove_phoenix_imports(file_path: Path, dry_run: bool = False) -> bool:
    """Remove Phoenix-related imports from a file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    changed = False

    for line in lines:
        # Skip Phoenix import lines
        if re.match(r'^\s*(from phoenix|import phoenix)', line):
            if dry_run:
                print(f"  Would remove: {line.strip()}")
            changed = True
            continue

        # Skip OpenTelemetry imports related to Phoenix
        if 'phoenix.otel' in line or 'tracer_provider = register()' in line:
            if dry_run:
                print(f"  Would remove: {line.strip()}")
            changed = True
            continue

        new_lines.append(line)

    if not dry_run and changed:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)

    return changed


def main():
    parser = argparse.ArgumentParser(description='Remove Phoenix imports')
    parser.add_argument('--target', required=True, help='Directory to scan')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    args = parser.parse_args()

    target = Path(args.target)
    files = list(target.rglob('*.py'))

    modified = 0
    for file in files:
        if remove_phoenix_imports(file, args.dry_run):
            mode = "Would modify" if args.dry_run else "Modified"
            print(f"{mode}: {file}")
            modified += 1

    print(f"\nTotal: {modified} files {'would be' if args.dry_run else ''} modified")


if __name__ == '__main__':
    main()
