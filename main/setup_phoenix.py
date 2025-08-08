#!/usr/bin/env python
"""
Setup Phoenix Observability for the pharmaceutical workflow system.

This script installs required Phoenix dependencies and launches Phoenix
for workflow tracing and compliance monitoring.
"""

import os
import subprocess
import sys
import time
import requests
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} failed with exception: {e}")
        return False


def check_phoenix_running() -> bool:
    """Check if Phoenix is already running."""
    try:
        response = requests.get("http://localhost:6006", timeout=5)
        if response.status_code == 200:
            print("[SUCCESS] Phoenix is already running at http://localhost:6006")
            return True
    except:
        pass
    return False


def install_phoenix_dependencies() -> bool:
    """Install all required Phoenix dependencies."""
    print("\n=== Installing Phoenix Dependencies ===")
    
    packages = [
        "arize-phoenix",
        "openinference-instrumentation-llama-index",
        "openinference-instrumentation-openai", 
        "llama-index-callbacks-arize-phoenix",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-exporter-otlp-proto-http",
        "requests"
    ]
    
    for package in packages:
        success = run_command(
            f"uv add {package}",
            f"Installing {package}"
        )
        if not success:
            print(f"[WARNING] Failed to install {package}, trying pip...")
            success = run_command(
                f"pip install {package}",
                f"Installing {package} via pip"
            )
            if not success:
                return False
    
    return True


def launch_phoenix_local() -> bool:
    """Launch Phoenix locally using Python."""
    print("\n=== Launching Phoenix Locally ===")
    
    launch_script = '''
import phoenix as px
import time
import sys

try:
    # Launch Phoenix with pharmaceutical project settings
    session = px.launch_app(
        host="localhost",
        port=6006,
        # Set project name for pharmaceutical compliance
        # project_name="pharmaceutical_test_generation",
    )
    
    print(f"Phoenix launched successfully at: {session.url}")
    print("Phoenix is now ready for pharmaceutical workflow tracing")
    print("Press Ctrl+C to stop Phoenix")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\nPhoenix shutdown requested")
        sys.exit(0)
        
except Exception as e:
    print(f"Failed to launch Phoenix: {e}")
    sys.exit(1)
'''
    
    # Write launch script
    script_path = Path("launch_phoenix.py")
    script_path.write_text(launch_script)
    
    print("[INFO] Phoenix launch script created")
    print("[INFO] You can run Phoenix in background with:")
    print("   python launch_phoenix.py &")
    print("   # or")
    print("   start python launch_phoenix.py  # Windows")
    
    return True


def launch_phoenix_docker() -> bool:
    """Launch Phoenix using Docker container."""
    print("\n=== Launching Phoenix with Docker ===")
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker availability"):
        print("[WARNING] Docker not available, cannot launch Phoenix container")
        return False
    
    # Launch Phoenix container
    docker_cmd = """
    docker run -d \\
        --name phoenix \\
        -p 6006:6006 \\
        -e PHOENIX_PROJECT_NAME=pharmaceutical_test_generation \\
        arizephoenix/phoenix:latest
    """
    
    success = run_command(docker_cmd, "Launching Phoenix Docker container")
    
    if success:
        print("[INFO] Waiting for Phoenix to start...")
        time.sleep(10)  # Give Phoenix time to start
        
        # Check if Phoenix is responding
        for i in range(10):
            if check_phoenix_running():
                return True
            time.sleep(2)
        
        print("[WARNING] Phoenix container started but not responding")
    
    return success


def populate_chromadb() -> bool:
    """Populate ChromaDB with GAMP documents."""
    print("\n=== Populating ChromaDB ===")
    
    # Check if populate script exists
    populate_script = Path("populate_chromadb.py")
    if not populate_script.exists():
        print(f"[ERROR] ChromaDB populate script not found: {populate_script}")
        return False
    
    return run_command(
        "uv run python populate_chromadb.py",
        "Populating ChromaDB with GAMP-5 documents"
    )


def install_missing_packages() -> bool:
    """Install other missing packages like pdfplumber."""
    print("\n=== Installing Missing Packages ===")
    
    packages = ["pdfplumber"]
    
    for package in packages:
        success = run_command(
            f"uv add {package}",
            f"Installing {package}"
        )
        if not success:
            success = run_command(
                f"pip install {package}",
                f"Installing {package} via pip"
            )
            if not success:
                return False
    
    return True


def validate_setup() -> bool:
    """Validate that all components are working."""
    print("\n=== Validating Setup ===")
    
    success = True
    
    # Check Phoenix
    if check_phoenix_running():
        print("[OK] Phoenix: Running at http://localhost:6006")
    else:
        print("[X] Phoenix: Not running")
        success = False
    
    # Check packages
    try:
        import phoenix
        print("[OK] Phoenix package: Available")
    except ImportError:
        print("[X] Phoenix package: Not available")
        success = False
    
    try:
        import pdfplumber
        print("[OK] PDFPlumber package: Available")
    except ImportError:
        print("[X] PDFPlumber package: Not available") 
        success = False
    
    # Check ChromaDB
    try:
        from main.src.agents.parallel.context_provider import create_context_provider_agent
        context_provider = create_context_provider_agent()
        
        # Try to get collection counts
        total_docs = 0
        for collection_name in ["gamp5", "regulatory", "sops", "best_practices"]:
            try:
                collection = context_provider.collections[collection_name]
                count = collection.count()
                total_docs += count
            except:
                pass
        
        if total_docs > 0:
            print(f"[OK] ChromaDB: {total_docs} documents available")
        else:
            print("[X] ChromaDB: No documents found")
            success = False
            
    except Exception as e:
        print(f"[X] ChromaDB: Error checking - {e}")
        success = False
    
    return success


def main():
    """Main setup function."""
    print("=== Phoenix Observability Setup for Pharmaceutical Workflow ===")
    print("This script will:")
    print("1. Install required Phoenix dependencies")
    print("2. Launch Phoenix observability server") 
    print("3. Populate ChromaDB with GAMP-5 documents")
    print("4. Install missing packages (pdfplumber, etc.)")
    print("5. Validate the complete setup")
    print()
    
    # Check if Phoenix is already running
    if check_phoenix_running():
        print("Phoenix is already running, skipping launch step")
        phoenix_running = True
    else:
        phoenix_running = False
    
    # Install Phoenix dependencies
    if not install_phoenix_dependencies():
        print("❌ Failed to install Phoenix dependencies")
        return False
    
    # Launch Phoenix if not running
    if not phoenix_running:
        # Use command line argument or default to local launch
        import sys
        if "--docker" in sys.argv:
            print("\n[INFO] Launching Phoenix using Docker...")
            if not launch_phoenix_docker():
                print("❌ Failed to launch Phoenix Docker container")
                return False
        elif "--skip-phoenix" in sys.argv:
            print("[INFO] Skipping Phoenix launch - you'll need to start it manually")
        else:
            print("\n[INFO] Setting up Phoenix local launch script...")
            if not launch_phoenix_local():
                print("❌ Failed to setup local Phoenix launch")
                return False
    
    # Install missing packages
    if not install_missing_packages():
        print("❌ Failed to install missing packages")
        return False
    
    # Populate ChromaDB
    if not populate_chromadb():
        print("❌ Failed to populate ChromaDB")
        print("[INFO] You can run this manually with: uv run python populate_chromadb.py")
    
    # Validate setup
    print("\n" + "="*60)
    if validate_setup():
        print("\n[SUCCESS] Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start Phoenix if not already running:")
        print("   python launch_phoenix.py")
        print("2. Test the OSS model workflow:")
        print("   LLM_PROVIDER=openrouter uv run python main.py tests/test_data/gamp5_test_data/testing_data.md --verbose")
        print("3. Access Phoenix UI at: http://localhost:6006")
    else:
        print("\n[WARNING] Setup completed with some issues")
        print("Check the validation errors above and resolve them manually")
    
    return True


if __name__ == "__main__":
    main()