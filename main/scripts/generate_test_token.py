"""
Generate Clerk JWT token for testing.

Usage:
    python main/scripts/generate_test_token.py <user_id>
"""
import sys
import os
from clerk_backend_api import Clerk

async def generate_token(user_id: str):
    """Generate JWT token for a Clerk user."""
    clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

    # Note: Clerk SDK doesn't directly provide token generation
    # You need to use the Dashboard or create a session via frontend
    print(f"User ID: {user_id}")
    print("\nTo generate a token for this user:")
    print("1. Go to Clerk Dashboard → JWT Templates")
    print("2. Click 'Generate token for user'")
    print("3. Select the user and copy the token")
    print("\nOR sign in via a frontend app and extract the session token")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_test_token.py <user_id>")
        print(f"Example: python generate_test_token.py user_35KgiAcvIC0tdtFvJUN1vDkrNYc")
        sys.exit(1)

    import asyncio
    asyncio.run(generate_token(sys.argv[1]))
