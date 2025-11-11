"""
Create a Clerk session and generate JWT token for testing.

Usage:
    python main/scripts/create_clerk_session.py <user_id>
"""
import sys
import os
from pathlib import Path
import httpx
import json
from dotenv import load_dotenv

# Load environment variables from .env.local
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment variables from {env_file}")

def create_session_token(user_id: str, secret_key: str):
    """Create a session token for a Clerk user using Backend API."""

    # Clerk Backend API endpoint
    base_url = "https://api.clerk.com/v1"

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    # Create a session for the user
    print(f"Creating session for user: {user_id}")

    try:
        # Step 1: Create a session
        response = httpx.post(
            f"{base_url}/sessions",
            headers=headers,
            json={"user_id": user_id},
            timeout=30.0
        )
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data.get("id")

        print(f"\nSession created: {session_id}")

        # Step 2: Get session token
        token_response = httpx.post(
            f"{base_url}/sessions/{session_id}/tokens",
            headers=headers,
            timeout=30.0
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        jwt_token = token_data.get("jwt")

        print(f"\nJWT Token generated:")
        print(f"\n{jwt_token}")

        print(f"\n\nTest command:")
        print(f'curl -X POST http://localhost:8000/jobs ^')
        print(f'  -H "Authorization: Bearer {jwt_token}" ^')
        print(f'  -F "file=@test_urs.txt"')

        return jwt_token

    except httpx.HTTPStatusError as e:
        print(f"\nHTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_clerk_session.py <user_id>")
        print(f"\nExample:")
        print(f"  python create_clerk_session.py user_35KgiAcvIC0tdtFvJUN1vDkrNYc")
        sys.exit(1)

    user_id = sys.argv[1]
    secret_key = os.getenv("CLERK_SECRET_KEY")

    if not secret_key:
        print("Error: CLERK_SECRET_KEY environment variable not set")
        print("\nSet it with:")
        print('  $env:CLERK_SECRET_KEY="sk_test_FAVbd05h2Ec19W7GwAzHNJcOaznToLtV8f6RLXtTOF"')
        sys.exit(1)

    create_session_token(user_id, secret_key)
