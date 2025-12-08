#!/usr/bin/env python3
"""
Setup csvgeneration.com domain with Route 53
Automates domain registration, DNS configuration, and SSL certificate validation
"""

import boto3
import json
import time
import sys
from typing import Dict, List

def check_domain_availability(domain: str) -> bool:
    """Check if domain is available for registration"""
    client = boto3.client('route53domains', region_name='us-east-1')
    
    try:
        response = client.check_domain_availability(DomainName=domain)
        available = response['Availability'] == 'AVAILABLE'
        print(f"Domain {domain}: {'AVAILABLE' if available else 'NOT AVAILABLE'}")
        return available
    except Exception as e:
        print(f"Error checking domain: {e}")
        return False

def get_hosted_zone_id(domain: str) -> str:
    """Get Route 53 hosted zone ID for domain"""
    client = boto3.client('route53')
    
    try:
        response = client.list_hosted_zones_by_name(DNSName=domain)
        for zone in response['HostedZones']:
            if zone['Name'] == f"{domain}.":
                zone_id = zone['Id'].split('/')[-1]
                print(f"Found hosted zone: {zone_id}")
                return zone_id
        print(f"No hosted zone found for {domain}")
        return ""
    except Exception as e:
        print(f"Error getting hosted zone: {e}")
        return ""

def get_nameservers(zone_id: str) -> List[str]:
    """Get nameservers for hosted zone"""
    client = boto3.client('route53')
    
    try:
        response = client.get_hosted_zone(Id=zone_id)
        nameservers = response['DelegationSet']['NameServers']
        print(f"Nameservers: {', '.join(nameservers)}")
        return nameservers
    except Exception as e:
        print(f"Error getting nameservers: {e}")
        return []

def check_certificate_status(cert_arn: str) -> str:
    """Check ACM certificate validation status"""
    client = boto3.client('acm', region_name='us-east-1')
    
    try:
        response = client.describe_certificate(CertificateArn=cert_arn)
        status = response['Certificate']['Status']
        print(f"Certificate status: {status}")
        return status
    except Exception as e:
        print(f"Error checking certificate: {e}")
        return "UNKNOWN"

def wait_for_certificate_validation(cert_arn: str, timeout: int = 1800):
    """Wait for ACM certificate to be validated (max 30 minutes)"""
    print(f"Waiting for certificate validation (timeout: {timeout}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = check_certificate_status(cert_arn)
        if status == 'ISSUED':
            print("Certificate validated successfully!")
            return True
        elif status == 'FAILED':
            print("Certificate validation failed!")
            return False
        
        print(f"Status: {status}, waiting 30s...")
        time.sleep(30)
    
    print("Certificate validation timeout!")
    return False

def verify_dns_propagation(domain: str, record_type: str = 'A') -> bool:
    """Verify DNS record propagation"""
    import socket
    
    try:
        if record_type == 'A':
            result = socket.gethostbyname(domain)
            print(f"DNS resolved: {domain} -> {result}")
            return True
        return False
    except socket.gaierror:
        print(f"DNS not yet propagated for {domain}")
        return False

def main():
    domain = "csvgeneration.com"
    
    print("=" * 80)
    print("Route 53 Domain Setup for csvgeneration.com")
    print("=" * 80)
    
    # Step 1: Check domain availability
    print("\n[1/6] Checking domain availability...")
    if not check_domain_availability(domain):
        print("Domain not available. Please register manually or choose different domain.")
        sys.exit(1)
    
    # Step 2: Check if hosted zone exists (created by Terraform)
    print("\n[2/6] Checking Route 53 hosted zone...")
    zone_id = get_hosted_zone_id(domain)
    if not zone_id:
        print("Hosted zone not found. Run 'terraform apply' first.")
        sys.exit(1)
    
    # Step 3: Get nameservers
    print("\n[3/6] Getting nameservers...")
    nameservers = get_nameservers(zone_id)
    if not nameservers:
        print("Failed to get nameservers.")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("IMPORTANT: Update nameservers at your domain registrar")
    print("=" * 80)
    for i, ns in enumerate(nameservers, 1):
        print(f"Nameserver {i}: {ns}")
    print("=" * 80)
    
    # Step 4: Wait for user confirmation
    print("\n[4/6] Waiting for nameserver update...")
    input("Press Enter after updating nameservers at registrar (or skip if using Route 53)...")
    
    # Step 5: Verify DNS propagation
    print("\n[5/6] Verifying DNS propagation...")
    for attempt in range(10):
        if verify_dns_propagation(f"api.{domain}"):
            print("DNS propagated successfully!")
            break
        print(f"Attempt {attempt + 1}/10, waiting 60s...")
        time.sleep(60)
    else:
        print("DNS propagation incomplete. May take up to 48 hours.")
    
    # Step 6: Check certificate status
    print("\n[6/6] Checking SSL certificate...")
    print("Run 'terraform output acm_certificate_arn' to get certificate ARN")
    print("Then check status with:")
    print("  aws acm describe-certificate --certificate-arn <arn> --region us-east-1")
    
    print("\n" + "=" * 80)
    print("Setup complete! Next steps:")
    print("=" * 80)
    print("1. Wait for SSL certificate validation (5-30 minutes)")
    print("2. Test URLs:")
    print(f"   - https://{domain}")
    print(f"   - https://app.{domain}")
    print(f"   - https://api.{domain}/health")
    print("3. Update Clerk allowed origins")
    print("4. Update frontend CORS settings")
    print("=" * 80)

if __name__ == "__main__":
    main()
