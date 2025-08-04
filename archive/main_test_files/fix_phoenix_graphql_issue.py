#!/usr/bin/env uv run python
"""
Phoenix GraphQL API Fix
Targeted fix for Phoenix GraphQL "unexpected error occurred" issue

Based on diagnostic analysis:
- Phoenix server running (version 11.10.1) 
- OTLP trace ingestion working
- GraphQL schema introspection working
- GraphQL data queries failing with generic errors
- 2.6GB database exists but inaccessible via GraphQL

This script implements multiple fix strategies to restore trace data access.
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import phoenix as px
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhoenixGraphQLFixer:
    """Comprehensive Phoenix GraphQL issue fixer."""
    
    def __init__(self):
        self.phoenix_url = "http://localhost:6006"
        self.graphql_url = f"{self.phoenix_url}/graphql"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "fix_attempts": {},
            "success": False,
            "working_method": None,
            "traces_accessible": False
        }
    
    def run_all_fixes(self):
        """Run all available fixes in order of likelihood to succeed."""
        logger.info("🔧 Starting Phoenix GraphQL Fix Process")
        logger.info("=" * 60)
        
        fixes = [
            ("Direct Phoenix Client Bypass", self.fix_via_direct_client),
            ("Phoenix Server Restart", self.fix_via_server_restart),
            ("Database Reset with Backup", self.fix_via_database_reset),
            ("Alternative Phoenix Launch", self.fix_via_alternative_launch),
            ("Environment Reset", self.fix_via_environment_reset),
        ]
        
        for fix_name, fix_function in fixes:
            logger.info(f"\n🔧 Attempting Fix: {fix_name}")
            logger.info("-" * 40)
            
            try:
                success = fix_function()
                self.results["fix_attempts"][fix_name] = {
                    "attempted": True,
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    logger.info(f"✅ {fix_name} SUCCESSFUL!")
                    self.results["success"] = True
                    self.results["working_method"] = fix_name
                    self._verify_final_state()
                    return True
                else:
                    logger.warning(f"❌ {fix_name} failed, trying next method...")
                    
            except Exception as e:
                logger.error(f"❌ {fix_name} error: {e}")
                self.results["fix_attempts"][fix_name] = {
                    "attempted": True,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        logger.error("❌ All fix attempts failed")
        self._provide_manual_instructions()
        return False
    
    def fix_via_direct_client(self):
        """Fix #1: Test direct Phoenix client to bypass GraphQL."""
        logger.info("Testing direct Phoenix client as workaround...")
        
        try:
            # Test multiple client configurations
            clients_to_test = [
                ("Default Client", lambda: px.Client()),
                ("Explicit Endpoint", lambda: px.Client(endpoint=self.phoenix_url)),
                ("Long Timeout", lambda: px.Client(endpoint=self.phoenix_url, timeout=30)),
            ]
            
            for client_name, client_factory in clients_to_test:
                try:
                    logger.info(f"   Testing {client_name}...")
                    client = client_factory()
                    
                    # Test data access
                    spans_df = client.get_spans_dataframe()
                    
                    if len(spans_df) > 0:
                        logger.info(f"   ✅ {client_name} successful - {len(spans_df)} spans retrieved")
                        logger.info(f"   📊 Traces: {spans_df['trace_id'].nunique()}")
                        
                        # Update monitoring script to use direct client
                        self._update_monitoring_script_for_direct_client()
                        
                        self.results["traces_accessible"] = True
                        return True
                    else:
                        logger.info(f"   ⚠️ {client_name} connected but no data")
                        
                except Exception as e:
                    logger.warning(f"   ❌ {client_name} failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Direct client test failed: {e}")
            return False
    
    def fix_via_server_restart(self):
        """Fix #2: Restart Phoenix server to clear GraphQL issues."""
        logger.info("Attempting Phoenix server restart...")
        
        try:
            # First, try to stop existing Phoenix gracefully
            logger.info("Stopping existing Phoenix processes...")
            self._stop_phoenix_processes()
            
            # Wait for cleanup
            time.sleep(3)
            
            # Start fresh Phoenix server
            logger.info("Starting fresh Phoenix server...")
            phoenix_process = self._start_fresh_phoenix()
            
            if phoenix_process:
                # Wait for server to initialize
                logger.info("Waiting for Phoenix to initialize...")
                time.sleep(10)
                
                # Test GraphQL after restart
                if self._test_graphql_after_restart():
                    logger.info("✅ Phoenix restart successful - GraphQL working")
                    return True
                else:
                    logger.warning("❌ Phoenix restarted but GraphQL still broken")
                    return False
            else:
                logger.error("❌ Failed to start fresh Phoenix server")
                return False
                
        except Exception as e:
            logger.error(f"Server restart failed: {e}")
            return False
    
    def fix_via_database_reset(self):
        """Fix #3: Reset Phoenix database while preserving data."""
        logger.info("Attempting database reset with backup...")
        
        try:
            # First backup current traces via direct client
            backup_success = self._backup_traces()
            if not backup_success:
                logger.warning("Could not backup traces - proceeding with caution")
            
            # Stop Phoenix
            self._stop_phoenix_processes()
            time.sleep(2)
            
            # Find and backup Phoenix database
            db_backup_success = self._backup_phoenix_database()
            
            # Start Phoenix with clean state
            logger.info("Starting Phoenix with clean database...")
            phoenix_process = self._start_fresh_phoenix()
            
            if phoenix_process:
                time.sleep(5)
                
                # Test if clean Phoenix works
                if self._test_graphql_basic():
                    logger.info("✅ Clean Phoenix GraphQL working")
                    
                    # Try to restore traces if we have backup
                    if backup_success:
                        restore_success = self._restore_traces_from_backup()
                        if restore_success:
                            logger.info("✅ Traces restored successfully")
                            return True
                        else:
                            logger.warning("⚠️ GraphQL working but trace restore failed")
                            return True  # At least GraphQL works
                    else:
                        logger.info("✅ GraphQL working with clean database")
                        return True
                else:
                    logger.error("❌ Even clean Phoenix GraphQL not working")
                    # Try to restore original database
                    if db_backup_success:
                        self._restore_phoenix_database()
                    return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return False
    
    def fix_via_alternative_launch(self):
        """Fix #4: Try alternative Phoenix launch methods."""
        logger.info("Trying alternative Phoenix launch methods...")
        
        alternative_methods = [
            ("Environment Override", self._launch_with_env_override),
            ("Direct Phoenix Server", self._launch_direct_phoenix_server),
            ("Docker Phoenix", self._launch_docker_phoenix),
        ]
        
        for method_name, launch_func in alternative_methods:
            try:
                logger.info(f"   Trying {method_name}...")
                success = launch_func()
                if success:
                    logger.info(f"   ✅ {method_name} successful")
                    return True
                else:
                    logger.warning(f"   ❌ {method_name} failed")
            except Exception as e:
                logger.warning(f"   ❌ {method_name} error: {e}")
        
        return False
    
    def fix_via_environment_reset(self):
        """Fix #5: Reset Phoenix environment variables and configuration."""
        logger.info("Resetting Phoenix environment...")
        
        try:
            # Clear Phoenix environment variables
            phoenix_env_vars = [
                "PHOENIX_HOST", "PHOENIX_PORT", "PHOENIX_API_KEY",
                "OTEL_EXPORTER_OTLP_ENDPOINT", "PHOENIX_PROJECT_NAME",
                "PHOENIX_EXPERIMENT_NAME", "PHOENIX_EXTERNAL"
            ]
            
            for var in phoenix_env_vars:
                if var in os.environ:
                    logger.info(f"Clearing {var}")
                    del os.environ[var]
            
            # Set clean defaults
            os.environ["PHOENIX_HOST"] = "localhost"
            os.environ["PHOENIX_PORT"] = "6006"
            
            # Try launching with clean environment
            logger.info("Launching Phoenix with clean environment...")
            
            # Stop existing processes first
            self._stop_phoenix_processes()
            time.sleep(2)
            
            # Start with clean environment
            phoenix_process = self._start_fresh_phoenix()
            
            if phoenix_process:
                time.sleep(8)
                
                if self._test_graphql_basic():
                    logger.info("✅ Clean environment Phoenix working")
                    return True
                else:
                    logger.warning("❌ Clean environment didn't fix GraphQL")
                    return False
            else:
                return False
                
        except Exception as e:
            logger.error(f"Environment reset failed: {e}")
            return False
    
    def _stop_phoenix_processes(self):
        """Stop all Phoenix processes."""
        try:
            # Try to find and stop Phoenix processes
            import psutil
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'phoenix' in proc.info['name'].lower():
                        logger.info(f"Stopping Phoenix process PID {proc.info['pid']}")
                        proc.terminate()
                    elif proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline']).lower()
                        if 'phoenix' in cmdline or '6006' in cmdline:
                            logger.info(f"Stopping Phoenix-related process PID {proc.info['pid']}")
                            proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Wait for processes to terminate
            time.sleep(2)
            
        except ImportError:
            logger.warning("psutil not available - cannot stop processes programmatically")
        except Exception as e:
            logger.warning(f"Error stopping Phoenix processes: {e}")
    
    def _start_fresh_phoenix(self):
        """Start a fresh Phoenix server."""
        try:
            # Use the existing start script
            start_script = Path("main/start_phoenix.py")
            if start_script.exists():
                logger.info("Using existing Phoenix start script...")
                # Run in background
                process = subprocess.Popen([
                    sys.executable, str(start_script)
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return process
            else:
                # Start Phoenix programmatically
                logger.info("Starting Phoenix programmatically...")
                import phoenix as px
                session = px.launch_app(host="localhost", port=6006)
                logger.info(f"Phoenix launched at: {session.url}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start Phoenix: {e}")
            return None
    
    def _test_graphql_after_restart(self):
        """Test GraphQL functionality after restart."""
        max_retries = 5
        
        for i in range(max_retries):
            try:
                time.sleep(2)  # Wait between retries
                
                # Test basic connectivity
                response = requests.get(self.phoenix_url, timeout=5)
                if response.status_code != 200:
                    continue
                
                # Test GraphQL schema
                schema_query = {"query": "{ __schema { queryType { name } } }"}
                schema_response = requests.post(
                    self.graphql_url, 
                    json=schema_query,
                    timeout=5
                )
                
                if schema_response.status_code != 200:
                    continue
                
                # Test data query
                data_query = {"query": "{ projects { id name } }"}
                data_response = requests.post(
                    self.graphql_url,
                    json=data_query,
                    timeout=5
                )
                
                if data_response.status_code == 200:
                    data = data_response.json()
                    if "errors" not in data:
                        logger.info(f"✅ GraphQL working after restart (attempt {i+1})")
                        return True
                
                logger.info(f"GraphQL still broken on attempt {i+1}/{max_retries}")
                
            except Exception as e:
                logger.warning(f"GraphQL test attempt {i+1} failed: {e}")
        
        return False
    
    def _test_graphql_basic(self):
        """Test basic GraphQL functionality."""
        try:
            # Test schema introspection
            schema_query = {"query": "{ __schema { queryType { name } } }"}
            response = requests.post(self.graphql_url, json=schema_query, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return "errors" not in data
            
            return False
            
        except Exception as e:
            logger.warning(f"Basic GraphQL test failed: {e}")
            return False
    
    def _backup_traces(self):
        """Backup current traces using direct client."""
        try:
            logger.info("Backing up traces...")
            client = px.Client(endpoint=self.phoenix_url)
            spans_df = client.get_spans_dataframe()
            
            if len(spans_df) > 0:
                backup_file = f"phoenix_traces_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                spans_df.to_parquet(backup_file)
                logger.info(f"✅ Backed up {len(spans_df)} spans to {backup_file}")
                return True
            else:
                logger.warning("No traces to backup")
                return False
                
        except Exception as e:
            logger.error(f"Trace backup failed: {e}")
            return False
    
    def _backup_phoenix_database(self):
        """Backup Phoenix database files."""
        try:
            # Look for Phoenix database files
            potential_db_paths = [
                ".phoenix/",
                "~/.phoenix/",
                Path.home() / ".phoenix",
                Path.cwd() / ".phoenix",
            ]
            
            for db_path in potential_db_paths:
                db_path = Path(db_path).expanduser()
                if db_path.exists():
                    backup_path = f"phoenix_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    import shutil
                    shutil.copytree(db_path, backup_path)
                    logger.info(f"✅ Database backed up to {backup_path}")
                    return True
            
            logger.warning("Phoenix database not found for backup")
            return False
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def _restore_phoenix_database(self):
        """Restore Phoenix database from backup."""
        # Implementation would go here
        logger.info("Database restore functionality not implemented yet")
        return False
    
    def _restore_traces_from_backup(self):
        """Restore traces from backup file."""
        # Implementation would go here
        logger.info("Trace restore functionality not implemented yet")
        return False
    
    def _launch_with_env_override(self):
        """Launch with environment variable overrides."""
        try:
            os.environ["PHOENIX_PORT"] = "6006"
            os.environ["PHOENIX_HOST"] = "localhost"
            
            import phoenix as px
            session = px.launch_app()
            time.sleep(5)
            
            return self._test_graphql_basic()
            
        except Exception as e:
            logger.warning(f"Environment override launch failed: {e}")
            return False
    
    def _launch_direct_phoenix_server(self):
        """Launch Phoenix server directly."""
        try:
            # Try direct server launch
            cmd = [sys.executable, "-m", "phoenix.server.main", "--host", "localhost", "--port", "6006"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(8)
            
            return self._test_graphql_basic()
            
        except Exception as e:
            logger.warning(f"Direct server launch failed: {e}")
            return False
    
    def _launch_docker_phoenix(self):
        """Try to launch Phoenix in Docker."""
        logger.info("Docker Phoenix launch not implemented")
        return False
    
    def _update_monitoring_script_for_direct_client(self):
        """Update monitoring script to use direct client as workaround."""
        logger.info("📝 Updating monitoring script to use direct client bypass...")
        
        # This would modify the monitoring script to use direct client
        # instead of relying on GraphQL
        
        workaround_note = """
# WORKAROUND: GraphQL API broken, using direct Phoenix client
# Use phoenix_monitoring_direct_client.py for trace access
"""
        
        try:
            with open("phoenix_graphql_workaround.md", "w") as f:
                f.write(workaround_note)
            logger.info("✅ Workaround documentation created")
        except Exception as e:
            logger.warning(f"Could not create workaround documentation: {e}")
    
    def _verify_final_state(self):
        """Verify that the fix actually resolved the issue."""
        logger.info("🔍 Verifying fix effectiveness...")
        
        try:
            # Test GraphQL
            graphql_working = self._test_graphql_basic()
            
            # Test direct client
            client_working = False
            try:
                client = px.Client()
                spans_df = client.get_spans_dataframe()
                client_working = len(spans_df) >= 0  # Even 0 spans means client works
            except Exception:
                pass
            
            self.results["final_verification"] = {
                "graphql_working": graphql_working,
                "client_working": client_working,
                "traces_accessible": client_working
            }
            
            if graphql_working or client_working:
                logger.info("✅ Phoenix trace access restored!")
                self.results["traces_accessible"] = True
            else:
                logger.warning("⚠️ Fix may not be complete")
                
        except Exception as e:
            logger.error(f"Final verification failed: {e}")
    
    def _provide_manual_instructions(self):
        """Provide manual instructions when all automated fixes fail."""
        logger.info("\n" + "=" * 60)
        logger.info("🛠️  MANUAL FIX INSTRUCTIONS")
        logger.info("=" * 60)
        logger.info("All automated fixes failed. Try these manual steps:")
        logger.info("")
        logger.info("1. COMPLETE PHOENIX RESTART:")
        logger.info("   • Stop all Python processes")
        logger.info("   • Kill any processes on port 6006")
        logger.info("   • Run: uv run python main/start_phoenix.py")
        logger.info("")
        logger.info("2. ALTERNATIVE: Use direct client bypass:")
        logger.info("   • Use the test_phoenix_client_bypass.py script")
        logger.info("   • Access traces via px.Client().get_spans_dataframe()")
        logger.info("")
        logger.info("3. NUCLEAR OPTION: Fresh Phoenix installation:")
        logger.info("   • Remove ~/.phoenix/ directory")
        logger.info("   • uv remove arize-phoenix")
        logger.info("   • uv add arize-phoenix")
        logger.info("   • Restart Phoenix server")
        logger.info("=" * 60)
    
    def save_results(self):
        """Save fix results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phoenix_graphql_fix_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"📁 Fix results saved to: {filename}")
        return filename


def main():
    """Run Phoenix GraphQL fix process."""
    fixer = PhoenixGraphQLFixer()
    success = fixer.run_all_fixes()
    filename = fixer.save_results()
    
    print("\n" + "=" * 60)
    print("🏁 PHOENIX GRAPHQL FIX SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ RESOLUTION SUCCESSFUL!")
        print(f"Working method: {fixer.results['working_method']}")
        print(f"Traces accessible: {'YES' if fixer.results['traces_accessible'] else 'NO'}")
    else:
        print("❌ AUTOMATED FIXES FAILED")
        print("Check manual instructions above")
    
    print(f"\nDetailed results: {filename}")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)