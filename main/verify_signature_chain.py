"""
Signature Chain Verification Test for Task 22

Verifies that all Ed25519 signatures in the audit trail are properly chained
and cryptographically valid, ensuring tamper evidence and regulatory compliance.
"""

import json
import sys
from pathlib import Path

# Add main directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.core.cryptographic_audit import get_audit_crypto


def verify_audit_signature_chain():
    """Verify the signature chain in the audit trail."""
    print("Verifying Ed25519 Signature Chain for Task 22")
    print("=" * 45)
    
    crypto_audit = get_audit_crypto()
    
    # Find the latest audit log file
    audit_dir = Path("logs/comprehensive_audit")
    audit_files = list(audit_dir.glob("*.jsonl"))
    
    if not audit_files:
        print("ERROR: No audit files found!")
        return False
        
    latest_file = sorted(audit_files)[-1]
    print(f"Analyzing audit file: {latest_file.name}")
    
    # Load all audit entries
    audit_entries = []
    with open(latest_file, 'r') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                audit_entries.append(entry)
    
    print(f"Found {len(audit_entries)} audit entries")
    
    # Verify signature chain
    print("\nVerifying signature chain...")
    chain_results = crypto_audit.verify_audit_chain(audit_entries)
    
    print(f"\nCHAIN VERIFICATION RESULTS:")
    print(f"Chain Valid: {'YES' if chain_results['chain_valid'] else 'NO'}")
    print(f"Total Entries: {chain_results['total_entries']}")
    print(f"Verified Entries: {chain_results['verified_entries']}")
    print(f"Invalid Entries: {len(chain_results['invalid_entries'])}")
    print(f"Chain Breaks: {len(chain_results['chain_breaks'])}")
    
    # Verify individual signatures
    print(f"\nINDIVIDUAL SIGNATURE VERIFICATION:")
    for i, entry in enumerate(audit_entries):
        try:
            signature_valid = crypto_audit.verify_audit_event(entry)
            event_type = entry.get('event_type', 'unknown')
            signature_id = entry.get('cryptographic_metadata', {}).get('signature_id', 'none')[:8]
            print(f"Entry {i+1} ({event_type}): {'VALID' if signature_valid else 'INVALID'} [{signature_id}]")
        except Exception as e:
            print(f"Entry {i+1}: ERROR - {e}")
    
    # Extract key compliance details
    print(f"\nCOMPLIANCE VERIFICATION:")
    
    # Check signature algorithm
    signatures_ed25519 = all(
        entry.get('cryptographic_metadata', {}).get('signature_algorithm') == 'Ed25519'
        for entry in audit_entries
        if 'cryptographic_metadata' in entry
    )
    print(f"All signatures Ed25519: {'YES' if signatures_ed25519 else 'NO'}")
    
    # Check 21 CFR Part 11 metadata
    cfr_compliant = all(
        entry.get('regulatory_metadata', {}).get('compliance_standard') == '21_CFR_Part_11'
        for entry in audit_entries
        if 'regulatory_metadata' in entry
    )
    print(f"21 CFR Part 11 compliant: {'YES' if cfr_compliant else 'NO'}")
    
    # Check ALCOA+ compliance in audit data
    alcoa_compliant = all(
        entry.get('compliance_metadata', {}).get('standard') == 'GAMP-5'
        for entry in audit_entries
        if 'compliance_metadata' in entry
    )
    print(f"GAMP-5 standard metadata: {'YES' if alcoa_compliant else 'NO'}")
    
    # Check tamper evidence
    tamper_evident = all(
        entry.get('regulatory_metadata', {}).get('tamper_evidence') == 'ed25519_digital_signature'
        for entry in audit_entries
        if 'regulatory_metadata' in entry
    )
    print(f"Tamper evidence enabled: {'YES' if tamper_evident else 'NO'}")
    
    return chain_results['chain_valid'] and len(chain_results['invalid_entries']) == 0


if __name__ == "__main__":
    success = verify_audit_signature_chain()
    if success:
        print(f"\n✓ SUCCESS: All signatures verified and chain intact")
        print("  Task 22 cryptographic integrity requirement MET")
        exit(0)
    else:
        print(f"\n✗ FAILURE: Signature verification failed")
        exit(1)