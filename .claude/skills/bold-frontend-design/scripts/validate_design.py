#!/usr/bin/env python3
"""
Bold Frontend Design Validation Script

Detects generic/convergent design patterns that lead to "AI slop" aesthetics.
Returns warnings for any detected anti-patterns.

Usage:
    python validate_design.py /path/to/frontend/

Exit codes:
    0 - No warnings (all checks passed)
    1 - Warnings detected (generic patterns found)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Generic patterns to detect
GENERIC_FONTS = [
    'Inter',
    'Roboto',
    'Arial',
    'Helvetica',
    'system-ui',
    '-apple-system',
    'BlinkMacSystemFont',
]

GENERIC_COLORS = [
    '#6366f1',  # Indigo 500
    '#8b5cf6',  # Violet 500
    '#a78bfa',  # Violet 400
    '#818cf8',  # Indigo 400
]

GENERIC_LAYOUTS = [
    r'grid\s+grid-cols-2\s+gap-[48]',  # Standard two-column
    r'grid\s+grid-cols-3\s+gap-[48]',  # Standard three-column
]

GENERIC_ANIMATIONS = [
    r'initial=\{\{\s*opacity:\s*0\s*\}\}\s+animate=\{\{\s*opacity:\s*1\s*\}\}',
]


class DesignValidator:
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.warnings: List[Tuple[str, str, str]] = []
        self.files_scanned = 0

    def scan_directory(self):
        """Scan directory for design files"""
        extensions = ['.tsx', '.ts', '.jsx', '.js', '.css', '.scss']

        for ext in extensions:
            for file_path in self.directory.rglob(f'*{ext}'):
                # Skip node_modules and build directories
                if 'node_modules' in str(file_path) or '.next' in str(file_path):
                    continue

                self.scan_file(file_path)
                self.files_scanned += 1

    def scan_file(self, file_path: Path):
        """Scan individual file for anti-patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for generic fonts
            for font in GENERIC_FONTS:
                if re.search(rf'font-family.*{font}', content, re.IGNORECASE):
                    self.add_warning(
                        file_path,
                        'Generic Font',
                        f"Detected '{font}' font (convergent pattern)"
                    )

            # Check for generic colors
            for color in GENERIC_COLORS:
                if color.lower() in content.lower():
                    self.add_warning(
                        file_path,
                        'Generic Color',
                        f"Detected purple gradient color '{color}' (AI default)"
                    )

            # Check for generic layouts
            for pattern in GENERIC_LAYOUTS:
                if re.search(pattern, content):
                    self.add_warning(
                        file_path,
                        'Generic Layout',
                        f"Detected predictable grid pattern: {pattern}"
                    )

            # Check for simple animations
            for pattern in GENERIC_ANIMATIONS:
                if re.search(pattern, content):
                    self.add_warning(
                        file_path,
                        'Generic Animation',
                        "Detected simple fade-in without choreography"
                    )

        except Exception as e:
            print(f"{YELLOW}Warning: Could not scan {file_path}: {e}{RESET}")

    def add_warning(self, file_path: Path, category: str, message: str):
        """Add a warning to the list"""
        relative_path = file_path.relative_to(self.directory)
        self.warnings.append((str(relative_path), category, message))

    def print_report(self):
        """Print validation report"""
        print(f"\n{BLUE}{'=' * 60}{RESET}")
        print(f"{BLUE}Bold Frontend Design Validation Report{RESET}")
        print(f"{BLUE}{'=' * 60}{RESET}\n")

        print(f"Files scanned: {self.files_scanned}")

        if not self.warnings:
            print(f"\n{GREEN}✓ No generic fonts detected{RESET}")
            print(f"{GREEN}✓ No generic purple gradients{RESET}")
            print(f"{GREEN}✓ No predictable layouts{RESET}")
            print(f"{GREEN}✓ No simple fade-in animations{RESET}")
            print(f"\n{GREEN}{'=' * 60}{RESET}")
            print(f"{GREEN}Design validation PASSED{RESET}")
            print(f"{GREEN}{'=' * 60}{RESET}\n")
            return 0
        else:
            print(f"\n{RED}Warnings: {len(self.warnings)}{RESET}\n")

            # Group warnings by category
            categories = {}
            for file_path, category, message in self.warnings:
                if category not in categories:
                    categories[category] = []
                categories[category].append((file_path, message))

            # Print warnings by category
            for category, items in categories.items():
                print(f"{YELLOW}> {category} ({len(items)} issue(s)){RESET}")
                for file_path, message in items:
                    print(f"  {RED}x{RESET} {file_path}")
                    print(f"    {message}")
                print()

            print(f"{RED}{'=' * 60}{RESET}")
            print(f"{RED}Design validation FAILED{RESET}")
            print(f"{RED}{'=' * 60}{RESET}\n")

            print(f"{YELLOW}Recommendations:{RESET}")
            if 'Generic Font' in categories:
                print(f"  • Replace Inter/Roboto with: Space Grotesk, Clash Display, Instrument Sans")
            if 'Generic Color' in categories:
                print(f"  • Replace purple gradients with context-specific palette")
            if 'Generic Layout' in categories:
                print(f"  • Add asymmetry, overlap, or grid-breaking elements")
            if 'Generic Animation' in categories:
                print(f"  • Implement orchestrated entrance with staggered delays")
            print()

            return 1


def main():
    if len(sys.argv) < 2:
        print(f"{RED}Usage: python validate_design.py /path/to/frontend/{RESET}")
        sys.exit(1)

    directory = sys.argv[1]

    if not os.path.isdir(directory):
        print(f"{RED}Error: '{directory}' is not a valid directory{RESET}")
        sys.exit(1)

    print(f"{BLUE}Validating design in: {directory}{RESET}")

    validator = DesignValidator(directory)
    validator.scan_directory()
    exit_code = validator.print_report()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
