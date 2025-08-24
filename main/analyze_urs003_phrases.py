#!/usr/bin/env python3
"""Analyze URS-003 to identify all Category 5 phrases"""

import re

URS003_CONTENT = """
## URS-003: Manufacturing Execution System (MES)
**Target Category**: 5 (Clear)
**System Type**: Custom Batch Record Management System

### 1. Introduction
This URS defines requirements for a custom MES to manage electronic batch records for sterile injectable products.

### 2. Functional Requirements
- **URS-MES-001**: System shall be custom-developed to integrate with proprietary equipment.
- **URS-MES-002**: Custom algorithms required for:
  - Dynamic in-process control limits based on multivariate analysis
  - Real-time batch genealogy tracking across multiple unit operations
  - Proprietary yield optimization calculations
- **URS-MES-003**: Develop custom interfaces for:
  - 12 different equipment types with proprietary protocols
  - Integration with custom warehouse management system
  - Real-time data exchange with proprietary PAT systems
- **URS-MES-004**: Custom workflow engine to handle:
  - Parallel processing paths unique to our manufacturing process
  - Complex exception handling for deviations
  - Site-specific business rules not supported by commercial packages
- **URS-MES-005**: Develop proprietary data structures for:
  - Multi-level bill of materials with conditional components
  - Process parameters with complex interdependencies
- **URS-MES-006**: Custom mobile application for shop floor data entry.
- **URS-MES-007**: Bespoke analytics module for real-time process monitoring.

### 3. Regulatory Requirements
- **URS-MES-008**: Custom audit trail implementation with enhanced metadata.
- **URS-MES-009**: Develop proprietary electronic signature workflow.
- **URS-MES-010**: Custom data integrity checks beyond standard validations.
"""

def analyze_category5_phrases():
    """Analyze URS-003 for Category 5 indicators"""

    # Normalize content like the GAMP tool does
    normalized = URS003_CONTENT.lower()
    normalized = " ".join(normalized.split())

    print("URS-003 Category 5 Phrase Analysis")
    print("=" * 50)

    # Look for custom/bespoke/proprietary phrases
    custom_patterns = [
        r"custom[\s-]\w+",
        r"bespoke[\s-]\w+",
        r"proprietary[\s-]\w+",
        r"develop\s+custom",
        r"custom\s+\w+",
        r"site-specific\s+\w+"
    ]

    all_matches = set()

    for pattern in custom_patterns:
        matches = re.findall(pattern, normalized)
        for match in matches:
            all_matches.add(match.strip())

    print("Custom/Bespoke/Proprietary phrases found:")
    for match in sorted(all_matches):
        print(f"  - '{match}'")

    # Current strong indicators (after our fix)
    current_strong = [
        "custom development", "custom-developed", "bespoke solution", "bespoke analytics",
        "proprietary algorithm", "custom algorithms", "custom calculations",
        "tailored functionality", "purpose-built", "custom integration",
        "unique business logic", "custom code", "develop custom", "custom workflow",
        "proprietary data structures", "custom mobile application", "custom audit trail",
        "proprietary electronic signature", "custom data integrity"
    ]

    # Check which phrases are covered
    print("\nCoverage Analysis:")
    covered = 0
    total = len(all_matches)

    for phrase in sorted(all_matches):
        found = False
        for indicator in current_strong:
            if phrase in indicator or indicator in phrase:
                found = True
                break

        if found:
            print(f"  ✅ '{phrase}' - Covered by current indicators")
            covered += 1
        else:
            print(f"  ❌ '{phrase}' - NOT covered by current indicators")

    print(f"\nCoverage: {covered}/{total} ({covered/total*100:.1f}%)")

    # Suggest additional indicators
    uncovered = []
    for phrase in all_matches:
        found = False
        for indicator in current_strong:
            if phrase in indicator or indicator in phrase:
                found = True
                break
        if not found:
            uncovered.append(phrase)

    if uncovered:
        print("\nSuggested additional indicators:")
        for phrase in sorted(uncovered):
            print(f"  '{phrase}'")


if __name__ == "__main__":
    analyze_category5_phrases()
