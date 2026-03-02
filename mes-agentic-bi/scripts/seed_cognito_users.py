"""Seed Cognito User Pool with test users for local BI RBAC development.

Usage:
    python scripts/seed_cognito_users.py <user_pool_id> [region]

Example:
    python scripts/seed_cognito_users.py eu-west-1_AbCdEfG eu-west-1
"""

from __future__ import annotations

import sys

import boto3


def seed_users(user_pool_id: str, region: str = "eu-west-1") -> None:
    """Create test users in Cognito for BI RBAC testing."""
    client = boto3.client("cognito-idp", region_name=region)

    users = [
        {
            "username": "admin@test.com",
            "password": "AdminPass123!@#",
            "group": "Admin",
            "attributes": [
                {"Name": "email", "Value": "admin@test.com"},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:role", "Value": "Admin"},
                {"Name": "custom:site", "Value": "ALL"},
            ],
        },
        {
            "username": "operator.planta@test.com",
            "password": "OperatorA123!@#",
            "group": "Operator",
            "attributes": [
                {"Name": "email", "Value": "operator.planta@test.com"},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:role", "Value": "Operator"},
                {"Name": "custom:site", "Value": "PlantA"},
            ],
        },
        {
            "username": "operator.plantb@test.com",
            "password": "OperatorB123!@#",
            "group": "Operator",
            "attributes": [
                {"Name": "email", "Value": "operator.plantb@test.com"},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:role", "Value": "Operator"},
                {"Name": "custom:site", "Value": "PlantB"},
            ],
        },
    ]

    for u in users:
        try:
            client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=u["username"],
                UserAttributes=u["attributes"],
                TemporaryPassword=u["password"],
                MessageAction="SUPPRESS",
            )
            # Set permanent password (skip NEW_PASSWORD_REQUIRED challenge)
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=u["username"],
                Password=u["password"],
                Permanent=True,
            )
            # Add to group
            client.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=u["username"],
                GroupName=u["group"],
            )
            print(f"Created: {u['username']} -> {u['group']}")
        except client.exceptions.UsernameExistsException:
            print(f"Exists:  {u['username']} (skipping)")
        except Exception as exc:
            print(f"ERROR:   {u['username']}: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_cognito_users.py <user_pool_id> [region]")
        print()
        print("Test users created:")
        print("  admin@test.com         -> Admin group")
        print("  operator.planta@test.com -> Operator group, site=PlantA")
        print("  operator.plantb@test.com -> Operator group, site=PlantB")
        sys.exit(1)

    pool_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "eu-west-1"

    print(f"Seeding users in pool {pool_id} (region: {region})...")
    seed_users(pool_id, region)
    print("Done.")
