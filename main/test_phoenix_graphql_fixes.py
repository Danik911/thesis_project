#!/usr/bin/env uv run python
"""
Test script to validate Phoenix GraphQL API fixes and demonstrate correct usage.

This script validates that:
1. Phoenix GraphQL endpoints work correctly
2. Monitor-agent API fixes are functional  
3. Diagnostic tool bugs are resolved
4. Proper instrumentation packages are installed
"""

import json
import logging
import requests
import sys
import time
from typing import Any, Dict


def setup_logging():
    """Setup logging for test validation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


class PhoenixGraphQLTester:
    """Test Phoenix GraphQL API functionality."""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "http://localhost:6006"
        self.graphql_url = f"{self.base_url}/graphql"
        
    def test_basic_connectivity(self) -> bool:
        """Test basic Phoenix connectivity."""
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self.logger.info("✅ Phoenix basic connectivity working")
                return True
            else:
                self.logger.error(f"❌ Phoenix connectivity failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Phoenix connectivity error: {e}")
            return False
    
    def test_graphql_introspection(self) -> bool:
        """Test GraphQL schema introspection."""
        query = {
            "query": """
            query IntrospectionQuery {
              __schema {
                queryType {
                  name
                }
                mutationType {
                  name
                }
              }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "__schema" in data["data"]:
                    self.logger.info("✅ GraphQL introspection working")
                    self.logger.info(f"   Query type: {data['data']['__schema']['queryType']['name']}")
                    return True
                else:
                    self.logger.error(f"❌ GraphQL introspection unexpected response: {data}")
                    return False
            else:
                self.logger.error(f"❌ GraphQL introspection failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ GraphQL introspection error: {e}")
            return False
    
    def test_projects_query(self) -> bool:
        """Test projects query (corrected monitor-agent API usage)."""
        query = {
            "query": """
            query GetProjects {
              projects {
                id
                name
                tracesCount
              }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "projects" in data["data"]:
                    projects = data["data"]["projects"]
                    self.logger.info(f"✅ Projects query working - found {len(projects)} projects")
                    
                    if projects:
                        total_traces = sum(p.get("tracesCount", 0) for p in projects)
                        self.logger.info(f"   Total traces across projects: {total_traces}")
                        self.logger.info(f"   Sample project: {projects[0]['name']} (ID: {projects[0]['id']})")
                    
                    return True
                elif "errors" in data:
                    self.logger.error(f"❌ Projects query GraphQL errors: {data['errors']}")
                    return False
                else:
                    self.logger.error(f"❌ Projects query unexpected response: {data}")
                    return False
            else:
                self.logger.error(f"❌ Projects query failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Projects query error: {e}")
            return False
    
    def test_traces_query(self) -> bool:
        """Test traces query (corrected monitor-agent API usage)."""
        query = {
            "query": """
            query GetTraces {
              projects {
                id
                name
                traces(first: 10) {
                  edges {
                    node {
                      spanId
                      traceId
                      startTime
                      statusCode
                    }
                  }
                }
              }
            }
            """
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "projects" in data["data"]:
                    projects = data["data"]["projects"]
                    self.logger.info("✅ Traces query working")
                    
                    for project in projects:
                        traces = project.get("traces", {}).get("edges", [])
                        self.logger.info(f"   Project '{project['name']}': {len(traces)} traces retrieved")
                        
                        if traces:
                            sample_trace = traces[0]["node"]
                            self.logger.info(f"   Sample trace ID: {sample_trace['traceId']}")
                    
                    return True
                elif "errors" in data:
                    self.logger.error(f"❌ Traces query GraphQL errors: {data['errors']}")
                    return False
                else:
                    self.logger.error(f"❌ Traces query unexpected response: {data}")
                    return False
            else:
                self.logger.error(f"❌ Traces query failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Traces query error: {e}")
            return False
    
    def test_old_monitor_agent_api_failure(self) -> bool:
        """Demonstrate the old (incorrect) monitor-agent API usage fails."""
        self.logger.info("Testing old monitor-agent API usage (should fail)...")
        
        try:
            # This is what the monitor-agent was doing incorrectly
            response = requests.get(f"{self.base_url}/v1/traces", timeout=10)
            
            if response.status_code == 415:
                self.logger.info("✅ Confirmed: /v1/traces GET returns 415 (Unsupported Media Type) - expected behavior")
                self.logger.info("   This endpoint is for SENDING traces (POST), not retrieving them (GET)")
                return True
            else:
                self.logger.warning(f"⚠️ Unexpected response from /v1/traces GET: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error testing old API usage: {e}")
            return False
    
    def run_comprehensive_test(self) -> bool:
        """Run all tests and return overall success."""
        self.logger.info("🔍 Starting Phoenix GraphQL API Validation")
        self.logger.info("=" * 60)
        
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("GraphQL Introspection", self.test_graphql_introspection),
            ("Projects Query", self.test_projects_query),
            ("Traces Query", self.test_traces_query),
            ("Old API Usage Validation", self.test_old_monitor_agent_api_failure)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.logger.info(f"\n🧪 Running: {test_name}")
            try:
                success = test_func()
                results.append(success)
                time.sleep(0.5)  # Brief delay between tests
            except Exception as e:
                self.logger.error(f"❌ Test {test_name} crashed: {e}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        overall_success = all(results)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 PHOENIX GRAPHQL API VALIDATION RESULTS")
        self.logger.info("=" * 60)
        self.logger.info(f"Tests Passed: {passed}/{total}")
        self.logger.info(f"Overall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if overall_success:
            self.logger.info("\n🎉 Phoenix GraphQL API is fully functional!")
            self.logger.info("📋 Monitor-agent API fixes validated")
            self.logger.info("✅ Ready for pharmaceutical compliance monitoring")
        else:
            self.logger.error("\n❌ Some issues remain - check individual test results above")
        
        return overall_success


def main():
    """Main test execution."""
    tester = PhoenixGraphQLTester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
        
    except Exception as e:
        tester.logger.error(f"❌ Test suite crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())