"""
Test Clerk authentication with real JWT token.

Usage:
    python test_clerk_auth.py <jwt_token> <urs_file>
"""
import sys
import httpx

def test_authentication(jwt_token: str, urs_file: str):
    """Test FastAPI authentication with Clerk JWT token."""

    url = "http://localhost:8000/jobs"

    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    try:
        with open(urs_file, 'rb') as f:
            files = {"file": (urs_file, f, "text/plain")}

            print(f"Testing authentication with Clerk JWT...")
            print(f"Endpoint: {url}")
            print(f"File: {urs_file}")
            print(f"Token (first 50 chars): {jwt_token[:50]}...")
            print()

            response = httpx.post(url, headers=headers, files=files, timeout=30.0)

            print(f"Status Code: {response.status_code}")
            print(f"Response:")
            print(response.text)
            print()

            if response.status_code == 200 or response.status_code == 201:
                print("SUCCESS! Clerk authentication working!")
                return True
            else:
                print(f"FAILED! Status: {response.status_code}")
                return False

    except FileNotFoundError:
        print(f"Error: File not found: {urs_file}")
        return False
    except httpx.ConnectError:
        print("Error: Could not connect to FastAPI server.")
        print("Make sure the server is running: uvicorn main.api.app:app --reload")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_clerk_auth.py <jwt_token> <urs_file>")
        print("\nExample:")
        print('  python test_clerk_auth.py "eyJhbGci..." test_urs.txt')
        sys.exit(1)

    jwt_token = sys.argv[1]
    urs_file = sys.argv[2]

    success = test_authentication(jwt_token, urs_file)
    sys.exit(0 if success else 1)
