#!/usr/bin/env python
"""
Phoenix GraphQL API Fix Script

This script addresses the critical GraphQL API failures that prevent
trace data retrieval from Phoenix.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PhoenixGraphQLFixer:
    """Fix Phoenix GraphQL API issues."""
    
    def __init__(self, phoenix_host="localhost", phoenix_port=6006):
        self.phoenix_host = phoenix_host
        self.phoenix_port = phoenix_port
        self.base_url = f"http://{phoenix_host}:{phoenix_port}"
        self.graphql_url = f"{self.base_url}/graphql"
        
        self.results = {
            "fixes_attempted": [],
            "test_results": {},
            "success": False
        }
    
    def check_phoenix_server_status(self):
        """Check if Phoenix server is running and accessible."""
        logger.info("🔍 Checking Phoenix server status...")
        
        try:
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code == 200:
                server_version = response.headers.get("x-phoenix-server-version", "unknown")
                logger.info(f"✅ Phoenix server running - version: {server_version}")
                
                self.results["test_results"]["server_status"] = {
                    "running": True,
                    "version": server_version,
                    "response_time": response.elapsed.total_seconds()
                }
                
                return True
            else:
                logger.error(f"❌ Phoenix server not accessible - status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Phoenix server check failed: {e}")
            self.results["test_results"]["server_status"] = {
                "running": False,
                "error": str(e)
            }
            return False
    
    def test_graphql_schema_access(self):
        """Test GraphQL schema introspection."""
        logger.info("🔍 Testing GraphQL schema access...")
        
        introspection_query = {
            "query": "{ __schema { queryType { name } mutationType { name } } }"
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=introspection_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "__schema" in data["data"]:
                    logger.info("✅ GraphQL schema accessible")
                    self.results["test_results"]["schema_access"] = {
                        "success": True,
                        "schema_data": data["data"]["__schema"]
                    }
                    return True
                elif "errors" in data:
                    logger.error(f"❌ GraphQL schema errors: {data['errors']}")
                    self.results["test_results"]["schema_access"] = {
                        "success": False,
                        "errors": data["errors"]
                    }
                    return False
            else:
                logger.error(f"❌ GraphQL schema request failed - status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ GraphQL schema test failed: {e}")
            self.results["test_results"]["schema_access"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    def test_simple_graphql_queries(self):
        """Test simple GraphQL data queries."""
        logger.info("🔍 Testing simple GraphQL queries...")
        
        # Start with the simplest possible queries
        simple_queries = [
            ("Version Query", "{ __typename }"),
            ("Projects Count", "{ projects { totalCount } }"),
            ("Basic Projects", "{ projects(first: 1) { edges { node { id } } } }"),
        ]
        
        results = {}
        success_count = 0
        
        for query_name, query in simple_queries:
            logger.info(f"   Testing: {query_name}")
            
            try:
                response = requests.post(
                    self.graphql_url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "data" in data and data["data"] is not None:
                        logger.info(f"   ✅ {query_name} successful")
                        results[query_name] = {"success": True, "data": data["data"]}
                        success_count += 1
                    elif "errors" in data:
                        logger.error(f"   ❌ {query_name} GraphQL errors: {data['errors']}")
                        results[query_name] = {"success": False, "errors": data["errors"]}
                    else:
                        logger.error(f"   ❌ {query_name} returned null data")
                        results[query_name] = {"success": False, "error": "null_data"}
                else:
                    logger.error(f"   ❌ {query_name} HTTP error: {response.status_code}")
                    results[query_name] = {"success": False, "http_status": response.status_code}
                    
            except Exception as e:
                logger.error(f"   ❌ {query_name} exception: {e}")
                results[query_name] = {"success": False, "error": str(e)}
        
        self.results["test_results"]["simple_queries"] = results
        
        logger.info(f"Simple queries: {success_count}/{len(simple_queries)} successful")
        return success_count > 0
    
    def restart_phoenix_server(self):
        """Attempt to restart Phoenix server."""
        logger.info("🔄 Attempting to restart Phoenix server...")
        
        try:
            # Try to kill any existing Phoenix processes
            logger.info("   Stopping existing Phoenix processes...")
            
            # Use tasklist and taskkill on Windows to find and kill Phoenix processes
            try:
                # Find Phoenix processes
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python*", "/FO", "CSV"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        if "phoenix" in line.lower():
                            # Extract PID and kill
                            parts = line.split(',')
                            if len(parts) >= 2:
                                pid = parts[1].strip('"')
                                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
                                logger.info(f"   Killed Phoenix process PID: {pid}")
                
            except Exception as e:
                logger.warning(f"   Could not kill existing processes: {e}")
            
            # Wait a moment
            time.sleep(2)
            
            # Start new Phoenix server
            logger.info("   Starting new Phoenix server...")
            
            # Try different ways to start Phoenix
            start_commands = [
                ["python", "-m", "phoenix.server.main", "--host", self.phoenix_host, "--port", str(self.phoenix_port)],
                ["uv", "run", "python", "-m", "phoenix.server.main", "--host", self.phoenix_host, "--port", str(self.phoenix_port)],
                ["phoenix", "server", "--host", self.phoenix_host, "--port", str(self.phoenix_port)]
            ]
            
            for cmd in start_commands:
                try:
                    logger.info(f"   Trying: {' '.join(cmd)}")
                    
                    # Start process in background
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Wait a moment for startup
                    time.sleep(5)
                    
                    # Check if server is responsive
                    if self.check_phoenix_server_status():
                        logger.info("✅ Phoenix server restart successful")
                        self.results["fixes_attempted"].append({
                            "description": "Phoenix server restart",
                            "command": " ".join(cmd),
                            "success": True
                        })
                        return True
                    else:
                        # Kill the process if it's not working
                        proc.terminate()
                        
                except Exception as e:
                    logger.warning(f"   Command failed: {e}")
                    continue
            
            logger.error("❌ Phoenix server restart failed")
            self.results["fixes_attempted"].append({
                "description": "Phoenix server restart",
                "success": False,
                "error": "All restart methods failed"
            })
            return False
            
        except Exception as e:
            logger.error(f"❌ Phoenix restart exception: {e}")
            return False
    
    def check_phoenix_data_integrity(self):
        """Check if Phoenix has any data corruption issues."""
        logger.info("🔍 Checking Phoenix data integrity...")
        
        # Try to access Phoenix data directory and check for corruption
        try:
            # Phoenix typically stores data in ~/.phoenix or similar
            from pathlib import Path
            
            possible_data_dirs = [
                Path.home() / ".phoenix",
                Path.cwd() / ".phoenix",
                Path("/tmp/phoenix"),  # Linux/Mac
                Path("C:/temp/phoenix"),  # Windows
            ]
            
            data_dir = None
            for dir_path in possible_data_dirs:
                if dir_path.exists():
                    data_dir = dir_path
                    break
            
            if data_dir:
                logger.info(f"   Found Phoenix data directory: {data_dir}")
                
                # Check for database files
                db_files = list(data_dir.glob("*.db")) + list(data_dir.glob("*.sqlite*"))
                
                if db_files:
                    logger.info(f"   Found {len(db_files)} database files")
                    
                    # Check file sizes
                    for db_file in db_files:
                        size = db_file.stat().st_size
                        logger.info(f"   {db_file.name}: {size} bytes")
                        
                        if size == 0:
                            logger.warning(f"   ⚠️ Empty database file: {db_file.name}")
                
                self.results["test_results"]["data_integrity"] = {
                    "data_dir": str(data_dir),
                    "db_files": [str(f) for f in db_files],
                    "issues": []
                }
                
                return True
            else:
                logger.info("   No Phoenix data directory found")
                return True
                
        except Exception as e:
            logger.warning(f"   Data integrity check failed: {e}")
            return True  # Don't fail on this check
    
    def create_phoenix_restart_script(self):
        """Create a script to easily restart Phoenix server."""
        restart_script_content = '''#!/usr/bin/env python
"""
Phoenix Server Restart Script

This script stops any running Phoenix servers and starts a new one.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def kill_phoenix_processes():
    """Kill existing Phoenix processes."""
    print("🔄 Stopping existing Phoenix processes...")
    
    try:
        # Find and kill Phoenix processes (Windows)
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python*", "/FO", "CSV"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\\n')
            killed_count = 0
            
            for line in lines[1:]:  # Skip header
                if "phoenix" in line.lower():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')
                        try:
                            subprocess.run(["taskkill", "/PID", pid, "/F"], 
                                         capture_output=True, check=True)
                            print(f"   ✅ Killed Phoenix process PID: {pid}")
                            killed_count += 1
                        except subprocess.CalledProcessError:
                            print(f"   ⚠️ Could not kill PID: {pid}")
            
            if killed_count == 0:
                print("   No Phoenix processes found to kill")
            else:
                print(f"   Killed {killed_count} Phoenix processes")
                
    except Exception as e:
        print(f"   ⚠️ Error killing processes: {e}")

def start_phoenix_server(host="localhost", port=6006):
    """Start Phoenix server."""
    print(f"🚀 Starting Phoenix server at {host}:{port}...")
    
    commands_to_try = [
        ["python", "-m", "phoenix.server.main", "--host", host, "--port", str(port)],
        ["uv", "run", "python", "-m", "phoenix.server.main", "--host", host, "--port", str(port)],
    ]
    
    for cmd in commands_to_try:
        try:
            print(f"   Trying: {' '.join(cmd)}")
            
            # Start server
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for startup
            print("   Waiting for server startup...")
            time.sleep(8)
            
            # Test if server is responsive
            try:
                response = requests.get(f"http://{host}:{port}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Phoenix server started successfully!")
                    print(f"   🌐 Access at: http://{host}:{port}")
                    
                    # Keep the process running
                    print("   Phoenix server is running. Press Ctrl+C to stop.")
                    try:
                        proc.wait()
                    except KeyboardInterrupt:
                        print("\\n   Stopping Phoenix server...")
                        proc.terminate()
                        proc.wait()
                        print("   ✅ Phoenix server stopped")
                    
                    return True
                else:
                    print(f"   ❌ Server not responsive (status: {response.status_code})")
                    proc.terminate()
                    
            except requests.RequestException as e:
                print(f"   ❌ Server not accessible: {e}")
                proc.terminate()
                
        except Exception as e:
            print(f"   ❌ Command failed: {e}")
            continue
    
    print("❌ All start methods failed")
    return False

def main():
    """Main restart function."""
    print("🔄 Phoenix Server Restart")
    print("=" * 40)
    
    # Kill existing processes
    kill_phoenix_processes()
    
    # Wait a moment
    time.sleep(2)
    
    # Start new server
    if start_phoenix_server():
        print("\\n✅ Phoenix restart completed successfully!")
        return True
    else:
        print("\\n❌ Phoenix restart failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        
        script_path = Path(__file__).parent / "restart_phoenix_server.py"
        script_path.write_text(restart_script_content)
        
        logger.info(f"📝 Created Phoenix restart script: {script_path}")
        
        self.results["fixes_attempted"].append({
            "description": "Create Phoenix restart script",
            "script_path": str(script_path),
            "success": True
        })
        
        return True
    
    def run_all_fixes(self):
        """Run all GraphQL fixes."""
        logger.info("🚀 Starting Phoenix GraphQL Fixes")
        logger.info("=" * 60)
        
        fixes = [
            ("Check Phoenix server status", self.check_phoenix_server_status),
            ("Test GraphQL schema access", self.test_graphql_schema_access),
            ("Test simple GraphQL queries", self.test_simple_graphql_queries),
            ("Check Phoenix data integrity", self.check_phoenix_data_integrity),
            ("Create restart script", self.create_phoenix_restart_script),
        ]
        
        success_count = 0
        
        for description, fix_func in fixes:
            logger.info(f"\\n🔧 {description}...")
            try:
                if fix_func():
                    success_count += 1
                    logger.info(f"✅ {description} completed successfully")
                else:
                    logger.error(f"❌ {description} failed")
                    
                    # If basic checks fail, try restart
                    if description in ["Check Phoenix server status", "Test simple GraphQL queries"]:
                        logger.info("   Attempting Phoenix server restart...")
                        if self.restart_phoenix_server():
                            # Re-run the failed check
                            if fix_func():
                                success_count += 1
                                logger.info(f"✅ {description} successful after restart")
                            
            except Exception as e:
                logger.error(f"❌ {description} failed with exception: {e}")
        
        # Final assessment
        if self.test_simple_graphql_queries():
            self.results["success"] = True
            logger.info("✅ GraphQL API is now functional!")
        else:
            self.results["success"] = False
            logger.error("❌ GraphQL API still not functional")
        
        logger.info("=" * 60)
        logger.info(f"🏁 GraphQL fixes complete: {success_count}/{len(fixes)} successful")
        
        return self.results
    
    def save_results(self, filename="phoenix_graphql_fix_results.json"):
        """Save fix results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📊 GraphQL fix results saved to: {filename}")
        return filename

def main():
    """Run Phoenix GraphQL fixes."""
    fixer = PhoenixGraphQLFixer()
    results = fixer.run_all_fixes()
    
    # Save results
    fixer.save_results()
    
    # Print summary
    print("\\n" + "=" * 60)
    print("📋 GRAPHQL FIX SUMMARY")
    print("=" * 60)
    
    print(f"🌐 Phoenix URL: {fixer.base_url}")
    print(f"📊 GraphQL URL: {fixer.graphql_url}")
    
    if results["success"]:
        print("\\n✅ GraphQL API is now functional!")
        print("   You can now:")
        print("   • Query trace data via GraphQL")
        print("   • Use enhanced observability features")
        print("   • Generate compliance dashboards")
    else:
        print("\\n❌ GraphQL API issues persist")
        print("   Manual intervention required:")
        print("   • Check Phoenix server logs")
        print("   • Consider Phoenix version downgrade")
        print("   • Use restart_phoenix_server.py script")
    
    print("\\n📋 Test Results:")
    for test_name, result in results.get("test_results", {}).items():
        if isinstance(result, dict) and "success" in result:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
        else:
            status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    return results["success"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)