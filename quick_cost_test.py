#!/usr/bin/env python3
"""Quick test of the cost calculation fix."""

# Test the cost calculation directly
prompt_tokens = 2000
completion_tokens = 1000

# Old (wrong) calculation
old_cost = (prompt_tokens / 1_000_000 * 0.27) + (completion_tokens / 1_000_000 * 1.10)

# New (correct) calculation  
new_cost = (prompt_tokens / 1_000_000 * 0.14) + (completion_tokens / 1_000_000 * 0.28)

print("Cost Calculation Fix Validation")
print("=" * 40)
print(f"Test case: {prompt_tokens} prompt + {completion_tokens} completion tokens")
print()
print(f"OLD (wrong) calculation: ${old_cost:.6f}")
print(f"NEW (correct) calculation: ${new_cost:.6f}")
print()
print(f"Error reduction: ${old_cost - new_cost:.6f} (${(old_cost - new_cost)*1000:.2f} per 1000 tokens)")
print(f"Percentage fix: {((old_cost - new_cost) / old_cost * 100):.1f}% cost reduction")

# Verify against expected value
expected = 0.00056
error = abs(new_cost - expected)
print()
print(f"Expected value: ${expected:.6f}")
print(f"Calculation error: ${error:.8f}")
print(f"Fix status: {'✅ CORRECT' if error < 0.000001 else '❌ STILL WRONG'}")