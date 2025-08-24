#!/usr/bin/env python3
"""
Manual debugging of categorization logic
"""

# Test document content
content = """# Standard Off-the-Shelf Temperature Monitoring System

## System Description
This is a standard commercial off-the-shelf (COTS) temperature monitoring system for pharmaceutical storage areas. The system uses vendor-supplied software without any customization or configuration beyond standard installation parameters.

## Key Features
- Standard temperature sensors with pre-configured ranges
- Vendor-supplied monitoring software used as-is
- Pre-built reporting templates from vendor
- Standard alert thresholds (no custom business logic)
- Out-of-the-box compliance features

## Requirements
1. Monitor temperature in cold storage units
2. Record readings every 5 minutes
3. Generate standard compliance reports
4. Send email alerts for out-of-range conditions
5. Maintain electronic records per 21 CFR Part 11

## GAMP Category Justification
This system clearly falls under GAMP Category 3 as it is:
- Commercial off-the-shelf software
- No customization or custom code
- Standard configuration only
- Uses vendor's standard functionality
- No bespoke interfaces or modifications"""

print("=== MANUAL CATEGORIZATION DEBUG ===")

# Normalize content like the tool does
normalized_content = content.lower()
normalized_content = " ".join(normalized_content.split())

print(f"Normalized content length: {len(normalized_content)} chars")
print(f"First 200 chars: {normalized_content[:200]}...")

# Category 3 indicators from the code
category_3_indicators = {
    "strong_indicators": [
        "commercial software", "standard package", "off-the-shelf",
        "cots", "vendor standard", "default configuration",
        "standard installation", "unmodified", "as supplied",
        "vendor-supplied software without modification", "vendor's built-in functionality",
        "vendor's standard database", "as supplied by vendor", "vendor's archival feature",
        "vendor's standard reporting", "standard reports provided by vendor"
    ],
    "exclusions": [
        "configuration", "customization", "modification", "user-defined",
        "workflow", "setup", "parameters", "custom"
    ]
}

print("\n=== CATEGORY 3 INDICATOR MATCHING ===")

strong_matches = []
exclusions = []

for indicator in category_3_indicators["strong_indicators"]:
    if indicator in normalized_content:
        strong_matches.append(indicator)
        print(f"✓ Found strong indicator: '{indicator}'")

for exclusion in category_3_indicators["exclusions"]:
    if exclusion in normalized_content:
        exclusions.append(exclusion)
        print(f"⚠️  Found exclusion: '{exclusion}'")

print(f"\nTotal strong matches: {len(strong_matches)}")
print(f"Total exclusions: {len(exclusions)}")

# Calculate score like the tool does
strong_score = len(strong_matches) * 3  # Strong indicators worth 3 points
exclusion_penalty = len(exclusions) * -2  # Exclusions subtract 2 points
base_score = strong_score + exclusion_penalty

print("\nSCORE CALCULATION:")
print(f"Strong score (count * 3): {len(strong_matches)} * 3 = {strong_score}")
print(f"Exclusion penalty (count * -2): {len(exclusions)} * -2 = {exclusion_penalty}")
print(f"Base score: {base_score}")

# Category 3 bonus (from lines 274-276 in agent.py)
if len(strong_matches) >= 1 and len(exclusions) == 0:
    category_3_bonus = 3
    print(f"Category 3 bonus (strong >= 1, exclusions == 0): +{category_3_bonus}")
    final_score = base_score + category_3_bonus
else:
    category_3_bonus = 0
    print(f"No Category 3 bonus (strong: {len(strong_matches)}, exclusions: {len(exclusions)})")
    final_score = base_score

print(f"Final Category 3 score: {max(0, final_score)}")

# Basic confidence calculation
if final_score > base_score:  # Got bonus
    raw_confidence = 0.4 * len(strong_matches) + (-0.3) * len(exclusions)
    print("\nCONFIDENCE CALCULATION:")
    print(f"Base confidence: 0.4 * {len(strong_matches)} + (-0.3) * {len(exclusions)} = {raw_confidence}")

    # Category 3 adjustment (from lines 359-360)
    if len(strong_matches) >= 1:
        category_adjustment = 0.05
        print(f"Category 3 adjustment: +{category_adjustment}")
        raw_confidence += category_adjustment

    final_confidence = max(0.0, min(1.0, raw_confidence))
    print(f"Final confidence: {final_confidence} ({final_confidence * 100:.1f}%)")
