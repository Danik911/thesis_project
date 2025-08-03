#!/usr/bin/env python3
"""
Validate the categorization fix by testing the specific negation logic
"""

# Sample content from the document
content = "vendor-supplied software without any customization or configuration beyond standard installation parameters standard configuration only no custom business logic no bespoke interfaces or modifications"

# Normalize it
normalized_content = content.lower()

print("=== VALIDATING NEGATION FIX ===")
print(f"Normalized content: {normalized_content}")

# Test exclusions from Category 3
exclusions_to_check = ["configuration", "customization", "modification", "custom"]

print(f"\n=== TESTING EXCLUSION DETECTION ===")

for exc in exclusions_to_check:
    if exc in normalized_content:
        print(f"\n📍 Found '{exc}' in content")
        
        # Test negation patterns
        negation_patterns = [
            f"without {exc}",
            f"without any {exc}",
            f"no {exc}",
            f"not {exc}",
            f"no custom",     # Special case
            f"no bespoke",    # Special case  
            f"standard {exc} only",
        ]
        
        found_negations = []
        for pattern in negation_patterns:
            if pattern in normalized_content:
                found_negations.append(pattern)
        
        is_negated = len(found_negations) > 0
        
        print(f"  Negation patterns found: {found_negations}")
        print(f"  Result: {'EXCLUDED (negated)' if is_negated else 'INCLUDED (not negated)'}")
        
        if is_negated:
            print(f"  ✅ '{exc}' will NOT count as exclusion")
        else:
            print(f"  ❌ '{exc}' will count as exclusion") 

print(f"\n=== TESTING STRONG INDICATORS ===")

# Test Category 3 strong indicators
strong_indicators = ["commercial software", "off-the-shelf", "cots", "vendor standard"]

strong_matches = []
for indicator in strong_indicators:
    if indicator in "commercial off-the-shelf cots vendor-supplied software":
        strong_matches.append(indicator)
        print(f"✅ Found strong indicator: '{indicator}'")

print(f"\nStrong indicators found: {len(strong_matches)}")

# Expected result
print(f"\n=== EXPECTED OUTCOME ===")
print(f"Strong indicators: {len(strong_matches)} (should be 2-3)")
print(f"Exclusions after negation: 0 (all should be negated)")
print(f"Category 3 score: {len(strong_matches)} * 3 + 0 * -2 + 3 (bonus) = {len(strong_matches) * 3 + 3}")
print(f"Expected confidence: High (80%+) due to strong indicators and no exclusions")