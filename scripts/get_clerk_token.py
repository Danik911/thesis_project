"""Utility to mint Clerk session and JWT tokens for local testing.

This script avoids the deprecated `clerk` CLI by calling the Clerk Backend
API directly. It reads the Clerk secret from the environment or an `.env`
file, creates a short-lived session for the supplied `user_id`, and then
exchanges that session for a JWT generated from the requested template.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

CLERK_API_BASE = "https://api.clerk.com/v1"
USER_AGENT = "thesis-project-clerk-helper/1.0 (+https://github.com/Danik911/thesis_project)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Clerk JWT using the Backend API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--user-id",
        help="Clerk user_id to impersonate (e.g. user_123). Required unless --list-templates is used.",
    )
    parser.add_argument(
        "--template",
        default="server-token",
        help="JWT template slug to use when minting the token.",
    )
    parser.add_argument(
        "--env-file",
        default=".env.local",
        help="Path to .env file that contains CLERK_SECRET_KEY if not already exported.",
    )
    parser.add_argument(
        "--print-session",
        action="store_true",
        help="Also print the intermediate session ID (useful for debugging).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file to write the JWT to (contents will be overwritten).",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available Clerk JWT templates instead of generating a token.",
    )
    args = parser.parse_args()

    if not args.list_templates and not args.user_id:
        parser.error("--user-id is required unless --list-templates is specified")

    return args


def load_secret_key(env_file: str) -> str | None:
    secret = os.environ.get("CLERK_SECRET_KEY")
    if secret:
        return secret

    path = Path(env_file)
    if not path.exists():
        return None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith("CLERK_SECRET_KEY"):
            continue
        _, value = line.split("=", 1)
        return value.strip().strip('"')
    return None


def call_clerk(
    endpoint: str,
    *,
    secret_key: str,
    payload: dict | None = None,
    method: str = "POST",
) -> dict:
    url = f"{CLERK_API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {secret_key}")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", USER_AGENT)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        message = textwrap.dedent(
            f"""
            Clerk API request failed.
              endpoint: {endpoint}
              status:   {exc.code}
              body:     {detail or '<empty>'}
            """
        ).strip()
        raise RuntimeError(message) from exc


def list_jwt_templates(secret_key: str) -> list[dict]:
    response = call_clerk(
        "jwt_templates",
        secret_key=secret_key,
        payload=None,
        method="GET",
    )
    data = response.get("data") if isinstance(response, dict) else None
    if isinstance(data, list):
        return data
    if isinstance(response, list):
        return response
    return []


def main() -> int:
    args = parse_args()
    secret_key = load_secret_key(args.env_file)

    if not secret_key:
        print(
            "ERROR: CLERK_SECRET_KEY is not set in the environment or .env file.",
            file=sys.stderr,
        )
        return 1

    if args.list_templates:
        templates = list_jwt_templates(secret_key)
        if not templates:
            print("No JWT templates found for this Clerk instance.", file=sys.stderr)
            return 1
        for tpl in templates:
            name = tpl.get("name") or tpl.get("slug") or tpl.get("id")
            tpl_id = tpl.get("id", "?")
            print(f"{name} (id={tpl_id})")
        return 0

    session = call_clerk(
        "sessions",
        secret_key=secret_key,
        payload={"user_id": args.user_id},
    )
    session_id = session["id"]

    try:
        token = call_clerk(
            f"sessions/{session_id}/tokens/{args.template}",
            secret_key=secret_key,
            payload={},
        )
    except RuntimeError as exc:
        message = str(exc)
        if "JWT template not found" in message or "resource_not_found" in message:
            templates = list_jwt_templates(secret_key)
            options = ", ".join(
                tpl.get("name") or tpl.get("slug") or tpl.get("id") or "<unknown>"
                for tpl in templates
            )
            hint = options or "<no templates configured>"
            print(
                textwrap.dedent(
                    f"""
                    ERROR: Clerk JWT template '{args.template}' does not exist.
                    Available templates: {hint}
                    Tip: rerun with --list-templates to view the latest list.
                    """
                ).strip(),
                file=sys.stderr,
            )
            return 1
        raise

    jwt = token.get("jwt")
    if not jwt:
        print("ERROR: Clerk response did not include a JWT.", file=sys.stderr)
        return 1

    if args.print_session:
        print(f"session_id={session_id}")
    print(jwt)

    if args.output:
        args.output.write_text(jwt, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
