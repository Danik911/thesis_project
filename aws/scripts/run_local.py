#!/usr/bin/env python3
"""
Run the Pharmaceutical Test Generation stack locally using Docker Compose.

This script:
1. Checks prerequisites (Docker, Docker Compose)
2. Validates environment files (.env.local)
3. Starts all services via docker-compose.dev.yml
4. Waits for services to be healthy
5. Displays service URLs and status
6. Monitors container health

GAMP-5 Compliance: Local development environment for testing only.
All services match AWS production architecture for consistency.
"""

import subprocess
import sys
import os
import time
import signal
import platform
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_NAME = "pharma-test-gen"
COMPOSE_FILE = "docker-compose.dev.yml"

# Service health endpoints
SERVICE_ENDPOINTS = {
    "api": ("http://localhost:8080/health", 8080),
    "frontend": ("http://localhost:3000", 3000),
    "postgres": ("localhost", 5432),
    "localstack": ("http://localhost:4566", 4566),
}


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def is_wsl() -> bool:
    """Check if running in WSL."""
    return "microsoft" in platform.uname().release.lower()


def is_windows() -> bool:
    """Check if running on Windows (not WSL)."""
    return platform.system() == "Windows" and not is_wsl()


def run_command(cmd, cwd=None, check=True, capture_output=False, timeout=None):
    """Run a command and optionally capture output."""
    if isinstance(cmd, list):
        cmd_str = ' '.join(cmd)
    else:
        cmd_str = cmd

    print(f"  $ {cmd_str}")

    # If on Windows, wrap in WSL for Docker commands
    if is_windows() and isinstance(cmd, list) and cmd[0] in ["docker", "docker-compose"]:
        cmd = ["wsl", "-e", "bash", "-c", ' '.join(cmd)]
    elif is_windows() and isinstance(cmd, str) and ("docker" in cmd):
        cmd = f'wsl -e bash -c "{cmd}"'

    try:
        if capture_output:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                shell=isinstance(cmd, str), timeout=timeout
            )
            if check and result.returncode != 0:
                return None
            return result.stdout.strip()
        else:
            result = subprocess.run(
                cmd, cwd=cwd, shell=isinstance(cmd, str), timeout=timeout
            )
            if check and result.returncode != 0:
                return False
            return True
    except subprocess.TimeoutExpired:
        print(f"  Timeout after {timeout}s")
        return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


def check_prerequisites():
    """Check that all required tools are installed."""
    print("\n1. Checking prerequisites...")

    all_ok = True

    # Check Docker
    result = run_command(["docker", "--version"], capture_output=True, check=False)
    if result:
        print(f"     Docker: {result.split(',')[0]}")
    else:
        print("     Docker: NOT FOUND - Please install Docker")
        all_ok = False

    # Check Docker Compose
    result = run_command(["docker", "compose", "version"], capture_output=True, check=False)
    if result:
        version = result.strip()
        print(f"     Docker Compose: {version}")
    else:
        # Try legacy docker-compose command
        result = run_command(["docker-compose", "--version"], capture_output=True, check=False)
        if result:
            print(f"     Docker Compose: {result.split(',')[0]}")
        else:
            print("     Docker Compose: NOT FOUND - Please install Docker Compose")
            all_ok = False

    if not all_ok:
        print("\n   Please install missing tools and try again.")
        sys.exit(1)

    # Check if Docker is running
    result = run_command(["docker", "info"], capture_output=True, check=False)
    if not result:
        print("     Docker daemon is not running. Please start Docker.")
        sys.exit(1)
    print("     Docker daemon is running")


def check_env_files():
    """Check if required environment files exist."""
    print("\n2. Checking environment files...")

    project_root = get_project_root()

    required_files = [
        (".env.local", "Contains API keys and secrets"),
    ]

    optional_files = [
        (".env.development", "Development-specific overrides"),
    ]

    missing = []
    for filename, description in required_files:
        filepath = project_root / filename
        if filepath.exists():
            print(f"     {filename}: found")
        else:
            print(f"     {filename}: MISSING - {description}")
            missing.append(filename)

    for filename, description in optional_files:
        filepath = project_root / filename
        if filepath.exists():
            print(f"     {filename}: found (optional)")
        else:
            print(f"     {filename}: not found (optional)")

    if missing:
        print(f"\n   Missing required files: {', '.join(missing)}")
        print("   Please create these files with the required configuration.")
        print("\n   The .env.local should contain:")
        print("     - OPENROUTER_API_KEY (for DeepSeek LLM)")
        print("     - CLERK_SECRET_KEY (for authentication)")
        print("     - LANGFUSE_SECRET_KEY (for observability)")
        sys.exit(1)


def check_compose_file():
    """Check if Docker Compose file exists."""
    print("\n3. Checking Docker Compose configuration...")

    project_root = get_project_root()
    compose_path = project_root / COMPOSE_FILE

    if not compose_path.exists():
        print(f"     {COMPOSE_FILE}: NOT FOUND")
        print(f"     Expected location: {compose_path}")
        sys.exit(1)

    print(f"     {COMPOSE_FILE}: found")

    # Validate compose file syntax
    result = run_command(
        ["docker", "compose", "-f", str(compose_path), "config", "--quiet"],
        capture_output=True, check=False
    )
    if result is not None:
        print("     Compose file syntax: valid")
    else:
        print("     Compose file syntax: validation failed")
        print("     Running docker compose config to show errors...")
        run_command(["docker", "compose", "-f", str(compose_path), "config"])
        sys.exit(1)


def start_services():
    """Start Docker Compose services."""
    print("\n4. Starting services with Docker Compose...")

    project_root = get_project_root()
    compose_path = project_root / COMPOSE_FILE

    print("     Building images (this may take a few minutes on first run)...")
    print("")
    print("     Services to start:")
    print("       - postgres    (PostgreSQL 15 with pgvector)")
    print("       - localstack  (AWS SQS mock)")
    print("       - api         (FastAPI on port 8080)")
    print("       - worker      (Background job processor)")
    print("       - frontend    (Next.js on port 3000)")
    print("")

    # Build and start services
    result = run_command(
        ["docker", "compose", "-f", str(compose_path), "up", "-d", "--build"],
        cwd=str(project_root),
        timeout=600  # 10 minutes for build
    )

    if not result:
        print("     Failed to start services")
        print("     Check Docker logs for details:")
        print(f"       docker compose -f {COMPOSE_FILE} logs")
        sys.exit(1)

    print("     Services started")


def wait_for_services():
    """Wait for all services to be healthy."""
    print("\n5. Waiting for services to be healthy...")

    project_root = get_project_root()
    compose_path = project_root / COMPOSE_FILE

    services = ["postgres", "api", "frontend"]
    max_wait = 180  # 3 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
        all_healthy = True

        for service in services:
            # Get container health status
            result = run_command(
                ["docker", "compose", "-f", str(compose_path), "ps", "-a", "--format", "json"],
                cwd=str(project_root),
                capture_output=True, check=False
            )

            if result:
                # Check if container is running
                status_cmd = f"docker compose -f {compose_path} ps {service} --format '{{{{.Status}}}}'"
                status = run_command(status_cmd, cwd=str(project_root), capture_output=True, check=False)

                if status and ("Up" in status or "running" in status.lower()):
                    if "healthy" in status.lower():
                        print(f"     {service}: healthy")
                    elif "starting" in status.lower():
                        print(f"     {service}: starting...")
                        all_healthy = False
                    else:
                        print(f"     {service}: running")
                else:
                    print(f"     {service}: not running")
                    all_healthy = False
            else:
                all_healthy = False

        if all_healthy:
            break

        elapsed = int(time.time() - start_time)
        print(f"     Waiting... ({elapsed}s / {max_wait}s)")
        time.sleep(10)

    # Final status check
    print("\n     Final service status:")
    run_command(
        ["docker", "compose", "-f", str(compose_path), "ps"],
        cwd=str(project_root)
    )


def display_service_info():
    """Display service information and URLs."""
    print("\n" + "=" * 70)
    print("   LOCAL DEVELOPMENT STACK RUNNING")
    print("=" * 70)

    print(f"""
   Frontend:      http://localhost:3000
   API:           http://localhost:8080
   API Docs:      http://localhost:8080/docs
   API Health:    http://localhost:8080/health

   PostgreSQL:    localhost:5432
     Database:    testgen
     User:        postgres
     Password:    devpassword

   LocalStack:    http://localhost:4566
     SQS Queue:   testgen-jobs
     DLQ:         testgen-jobs-dlq
    """)

    print("=" * 70)
    print("   USEFUL COMMANDS")
    print("=" * 70)
    print(f"""
   View logs:
     docker compose -f {COMPOSE_FILE} logs -f

   View specific service logs:
     docker compose -f {COMPOSE_FILE} logs -f api
     docker compose -f {COMPOSE_FILE} logs -f worker

   Stop services:
     docker compose -f {COMPOSE_FILE} down

   Reset all data (including database):
     docker compose -f {COMPOSE_FILE} down --volumes

   Rebuild after code changes:
     docker compose -f {COMPOSE_FILE} up -d --build
    """)


def stop_services():
    """Stop all Docker Compose services."""
    print("\n   Stopping services...")

    project_root = get_project_root()
    compose_path = project_root / COMPOSE_FILE

    run_command(
        ["docker", "compose", "-f", str(compose_path), "down"],
        cwd=str(project_root),
        check=False
    )

    print("   Services stopped")


def handle_signal(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n\n   Received interrupt signal...")
    stop_services()
    sys.exit(0)


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("   PHARMACEUTICAL TEST GENERATION - LOCAL DEVELOPMENT")
    print("   Docker Compose Development Stack")
    print("=" * 70)
    print(f"\n   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Compose: {COMPOSE_FILE}")

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, handle_signal)

    # Check prerequisites
    check_prerequisites()

    # Check environment files
    check_env_files()

    # Check compose file
    check_compose_file()

    # Start services
    start_services()

    # Wait for healthy services
    wait_for_services()

    # Display info
    display_service_info()

    print(f"\n   Ready: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 70)
    print("   Press Ctrl+C to stop all services")
    print("=" * 70 + "\n")

    # Keep running until interrupted
    try:
        while True:
            time.sleep(60)
            # Periodic health check
            project_root = get_project_root()
            compose_path = project_root / COMPOSE_FILE
            result = run_command(
                f"docker compose -f {compose_path} ps --format '{{{{.Status}}}}'",
                cwd=str(project_root),
                capture_output=True,
                check=False
            )
            if result and "exited" in result.lower():
                print("\n   Warning: One or more services have stopped unexpectedly")
                print(f"   Check logs: docker compose -f {COMPOSE_FILE} logs")
    except KeyboardInterrupt:
        handle_signal(None, None)


if __name__ == "__main__":
    main()
