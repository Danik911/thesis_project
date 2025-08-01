#!/usr/bin/env python3
"""
Phoenix Observability Diagnostic Tool

This diagnostic script systematically tests Phoenix infrastructure to identify
the root cause of GraphQL backend failures preventing GAMP-5 compliance monitoring.

Performs comprehensive infrastructure testing without fallbacks - fails explicitly
with complete diagnostic information per pharmaceutical compliance requirements.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


class PhoenixDiagnosticError(Exception):
    """Base exception for Phoenix diagnostic failures."""
    def __init__(self, message: str, diagnostics: dict[str, Any]):
        super().__init__(message)
        self.diagnostics = diagnostics


def setup_logging():
    """Setup comprehensive logging for diagnostics."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


class PhoenixDiagnosticTool:
    """Comprehensive Phoenix infrastructure diagnostic tool."""

    def __init__(self):
        self.logger = setup_logging()
        self.phoenix_host = os.getenv("PHOENIX_HOST", "localhost")
        self.phoenix_port = int(os.getenv("PHOENIX_PORT", "6006"))
        self.base_url = f"http://{self.phoenix_host}:{self.phoenix_port}"
        self.diagnostics = {
            "test_timestamp": time.time(),
            "phoenix_host": self.phoenix_host,
            "phoenix_port": self.phoenix_port,
            "base_url": self.base_url,
            "test_results": {}
        }

    def log_test_result(self, test_name: str, success: bool, details: dict[str, Any]):
        """Log diagnostic test result with full details."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} {test_name}")

        if not success:
            self.logger.error(f"   Error Details: {details.get('error', 'Unknown error')}")

        self.diagnostics["test_results"][test_name] = {
            "success": success,
            "details": details,
            "timestamp": time.time()
        }

    def test_basic_connectivity(self) -> bool:
        """Test basic HTTP connectivity to Phoenix endpoint."""
        test_name = "Basic HTTP Connectivity"

        try:
            self.logger.info(f"Testing connectivity to {self.base_url}...")

            response = requests.get(self.base_url, timeout=10)

            details = {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_length": len(response.content),
                "headers": dict(response.headers)
            }

            if response.status_code == 200:
                self.log_test_result(test_name, True, details)
                return True
            details["error"] = f"HTTP {response.status_code}: Server responded but with error status"
            self.log_test_result(test_name, False, details)
            return False

        except requests.exceptions.ConnectionError as e:
            details = {
                "error": f"Connection failed: {e}",
                "error_type": "ConnectionError",
                "recommendation": "Start Phoenix server or check Docker container status"
            }
            self.log_test_result(test_name, False, details)
            return False

        except requests.exceptions.Timeout as e:
            details = {
                "error": f"Connection timeout: {e}",
                "error_type": "Timeout",
                "recommendation": "Check network connectivity or increase timeout"
            }
            self.log_test_result(test_name, False, details)
            return False

        except Exception as e:
            details = {
                "error": f"Unexpected error: {e}",
                "error_type": type(e).__name__,
                "recommendation": "Check system configuration and network settings"
            }
            self.log_test_result(test_name, False, details)
            return False

    def test_graphql_endpoint(self) -> bool:
        """Test GraphQL endpoint specifically for trace access."""
        test_name = "GraphQL Endpoint Access"

        try:
            graphql_url = f"{self.base_url}/graphql"
            self.logger.info(f"Testing GraphQL endpoint: {graphql_url}")

            # Test with a simple GraphQL introspection query
            introspection_query = {
                "query": """
                query IntrospectionQuery {
                  __schema {
                    queryType {
                      name
                    }
                  }
                }
                """
            }

            response = requests.post(
                graphql_url,
                json=introspection_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            details = {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_type": response.headers.get("content-type", "unknown")
            }

            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if "data" in json_response and "__schema" in json_response["data"]:
                        details["graphql_schema_accessible"] = True
                        details["query_type"] = json_response["data"]["__schema"]["queryType"]["name"]
                        self.log_test_result(test_name, True, details)
                        return True
                    if "errors" in json_response:
                        details["error"] = f"GraphQL errors: {json_response['errors']}"
                        details["graphql_errors"] = json_response["errors"]
                        self.log_test_result(test_name, False, details)
                        return False
                    details["error"] = "GraphQL returned unexpected response format"
                    details["response_data"] = json_response
                    self.log_test_result(test_name, False, details)
                    return False

                except json.JSONDecodeError as e:
                    details["error"] = f"Invalid JSON response from GraphQL endpoint: {e}"
                    details["response_text"] = response.text[:500]
                    self.log_test_result(test_name, False, details)
                    return False
            else:
                details["error"] = f"GraphQL endpoint returned HTTP {response.status_code}"
                details["response_text"] = response.text[:500]
                self.log_test_result(test_name, False, details)
                return False

        except Exception as e:
            details = {
                "error": f"GraphQL endpoint test failed: {e}",
                "error_type": type(e).__name__,
                "recommendation": "Check Phoenix GraphQL service configuration"
            }
            self.log_test_result(test_name, False, details)
            return False

    def test_trace_data_access(self) -> bool:
        """Test ability to access trace data through GraphQL."""
        test_name = "Trace Data Access"

        try:
            graphql_url = f"{self.base_url}/graphql"
            self.logger.info("Testing trace data access...")

            # Query for projects/traces - this is what typically fails
            traces_query = {
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

            response = requests.post(
                graphql_url,
                json=traces_query,
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            details = {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }

            if response.status_code == 200:
                try:
                    json_response = response.json()

                    if "data" in json_response and "projects" in json_response["data"]:
                        projects = json_response["data"]["projects"]
                        details["projects_count"] = len(projects)
                        details["projects_accessible"] = True

                        if projects:
                            details["sample_project"] = projects[0]
                            total_traces = sum(p.get("tracesCount", 0) for p in projects)
                            details["total_traces"] = total_traces

                        self.log_test_result(test_name, True, details)
                        return True
                    if "errors" in json_response:
                        # This is where "Something went wrong" errors typically appear
                        details["error"] = "GraphQL errors accessing trace data"
                        details["graphql_errors"] = json_response["errors"]
                        details["error_messages"] = [err.get("message", "Unknown error") for err in json_response["errors"]]

                        # Check for specific error patterns
                        error_text = str(json_response["errors"]).lower()
                        if "something went wrong" in error_text:
                            details["error_pattern"] = "generic_error"
                            details["recommendation"] = "Phoenix database/storage corruption - restart Phoenix service"
                        elif "database" in error_text or "connection" in error_text:
                            details["error_pattern"] = "database_error"
                            details["recommendation"] = "Phoenix database connection issues - check Phoenix backend"
                        else:
                            details["error_pattern"] = "unknown_graphql_error"
                            details["recommendation"] = "Unknown GraphQL error - check Phoenix logs"

                        self.log_test_result(test_name, False, details)
                        return False
                    details["error"] = "Unexpected GraphQL response format for trace query"
                    details["response_data"] = json_response
                    self.log_test_result(test_name, False, details)
                    return False

                except json.JSONDecodeError as e:
                    details["error"] = f"Invalid JSON response from trace query: {e}"
                    details["response_text"] = response.text[:500]
                    self.log_test_result(test_name, False, details)
                    return False
            else:
                details["error"] = f"Trace query returned HTTP {response.status_code}"
                details["response_text"] = response.text[:500]
                self.log_test_result(test_name, False, details)
                return False

        except Exception as e:
            details = {
                "error": f"Trace data access test failed: {e}",
                "error_type": type(e).__name__,
                "recommendation": "Check Phoenix service health and restart if necessary"
            }
            self.log_test_result(test_name, False, details)
            return False

    def test_otlp_endpoint(self) -> bool:
        """Test OTLP traces endpoint for span submission."""
        test_name = "OTLP Traces Endpoint"

        try:
            otlp_url = f"{self.base_url}/v1/traces"
            self.logger.info(f"Testing OTLP endpoint: {otlp_url}")

            # Test with empty POST (should return method not allowed or similar, not connection error)
            response = requests.post(otlp_url, timeout=10)

            details = {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "headers": dict(response.headers)
            }

            # OTLP endpoint should respond (even with error) - connection success is what matters
            if response.status_code in [200, 400, 405, 415]:  # Various acceptable responses
                details["endpoint_accessible"] = True
                self.log_test_result(test_name, True, details)
                return True
            details["error"] = f"OTLP endpoint returned unexpected status: {response.status_code}"
            details["response_text"] = response.text[:200]
            self.log_test_result(test_name, False, details)
            return False

        except Exception as e:
            details = {
                "error": f"OTLP endpoint test failed: {e}",
                "error_type": type(e).__name__,
                "recommendation": "Check Phoenix OTLP traces ingestion configuration"
            }
            self.log_test_result(test_name, False, details)
            return False

    def generate_recommendations(self) -> list[str]:
        """Generate specific recommendations based on diagnostic results."""
        recommendations = []

        test_results = self.diagnostics["test_results"]

        # Check basic connectivity
        if not test_results.get("Basic HTTP Connectivity", {}).get("success", False):
            recommendations.extend([
                "🚨 CRITICAL: Phoenix server is not running or not accessible",
                "📋 ACTION: Start Phoenix server with: python -m phoenix.server.main serve",
                "🐳 OR: Start Phoenix Docker container: docker run -p 6006:6006 arizephoenix/phoenix",
                "🔧 OR: Check PHOENIX_HOST and PHOENIX_PORT environment variables"
            ])
            return recommendations

        # Check GraphQL access
        if not test_results.get("GraphQL Endpoint Access", {}).get("success", False):
            recommendations.extend([
                "🚨 CRITICAL: Phoenix GraphQL endpoint is not functional",
                "📋 ACTION: Phoenix server is running but GraphQL service is broken",
                "🔄 SOLUTION: Restart Phoenix server to reset GraphQL backend",
                "🐳 OR: Recreate Phoenix Docker container with fresh state"
            ])

        # Check trace data access - this is the core issue
        if not test_results.get("Trace Data Access", {}).get("success", False):
            trace_details = test_results.get("Trace Data Access", {}).get("details", {})
            error_pattern = trace_details.get("error_pattern", "unknown")

            if error_pattern == "generic_error":
                recommendations.extend([
                    "🚨 CRITICAL: Phoenix 'Something went wrong' error detected",
                    "📋 ROOT CAUSE: Phoenix database/storage corruption or internal service failure",
                    "🔄 IMMEDIATE ACTION: Restart Phoenix server completely",
                    "🐳 Docker users: docker stop <container> && docker rm <container> && docker run -p 6006:6006 arizephoenix/phoenix",
                    "💾 Local users: Stop Phoenix process and clear any cached data in ~/.phoenix/"
                ])
            elif error_pattern == "database_error":
                recommendations.extend([
                    "🚨 CRITICAL: Phoenix database connection issues",
                    "📋 ACTION: Check Phoenix backend database configuration",
                    "🔧 SOLUTION: Restart Phoenix with clean database state"
                ])
            else:
                recommendations.extend([
                    "🚨 CRITICAL: Unknown GraphQL error accessing trace data",
                    "📋 ACTION: Check Phoenix server logs for detailed error information",
                    "🔄 SOLUTION: Restart Phoenix server and monitor initialization"
                ])

        # OTLP endpoint issues
        if not test_results.get("OTLP Traces Endpoint", {}).get("success", False):
            recommendations.extend([
                "⚠️ WARNING: OTLP traces endpoint not accessible",
                "📋 IMPACT: New traces cannot be submitted to Phoenix",
                "🔧 ACTION: Verify Phoenix OTLP ingestion configuration"
            ])

        # All tests passed
        if all(test.get("success", False) for test in test_results.values()):
            recommendations.extend([
                "✅ SUCCESS: All Phoenix infrastructure tests passed",
                "📋 STATUS: Phoenix observability should be fully functional",
                "🔍 NOTE: If issues persist, the problem may be in application-side configuration",
                "📖 CHECK: Review Phoenix instrumentation setup in application code"
            ])

        return recommendations

    def run_full_diagnostic(self) -> dict[str, Any]:
        """Run complete Phoenix infrastructure diagnostic."""
        self.logger.info("🔍 Starting Phoenix Observability Diagnostic")
        self.logger.info("=" * 60)

        # Test sequence
        tests = [
            ("basic_connectivity", self.test_basic_connectivity),
            ("graphql_endpoint", self.test_graphql_endpoint),
            ("trace_data_access", self.test_trace_data_access),
            ("otlp_endpoint", self.test_otlp_endpoint)
        ]

        overall_success = True

        for test_key, test_func in tests:
            try:
                success = test_func()
                if not success:
                    overall_success = False

                # Add delay between tests
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"❌ CRITICAL: Test {test_key} crashed: {e}")
                overall_success = False

                self.diagnostics["test_results"][f"{test_key}_crash"] = {
                    "success": False,
                    "details": {
                        "error": f"Test crashed: {e}",
                        "error_type": type(e).__name__
                    },
                    "timestamp": time.time()
                }

        # Generate recommendations
        recommendations = self.generate_recommendations()
        self.diagnostics["recommendations"] = recommendations
        self.diagnostics["overall_success"] = overall_success

        # Display results
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🔍 PHOENIX DIAGNOSTIC RESULTS")
        self.logger.info("=" * 60)

        for recommendation in recommendations:
            self.logger.info(recommendation)

        self.logger.info("\n📊 DIAGNOSTIC SUMMARY:")
        self.logger.info(f"Overall Status: {'✅ PASS' if overall_success else '❌ FAIL'}")

        passed_tests = sum(1 for test in self.diagnostics["test_results"].values() if test.get("success", False))
        total_tests = len(self.diagnostics["test_results"])
        self.logger.info(f"Tests Passed: {passed_tests}/{total_tests}")

        return self.diagnostics


def main():
    """Main diagnostic entry point."""
    diagnostic_tool = PhoenixDiagnosticTool()

    try:
        results = diagnostic_tool.run_full_diagnostic()

        # Save detailed results to file
        results_file = Path("phoenix_diagnostic_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        diagnostic_tool.logger.info(f"\n📁 Detailed results saved to: {results_file}")

        # Exit with appropriate code
        if results["overall_success"]:
            return 0
        return 1

    except Exception as e:
        diagnostic_tool.logger.error(f"❌ CRITICAL: Diagnostic tool crashed: {e}")

        # NO FALLBACKS: Explicit failure with full diagnostic information
        raise PhoenixDiagnosticError(
            f"Phoenix diagnostic tool failed completely: {e}",
            {
                "failure_type": "diagnostic_tool_crash",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "phoenix_config": {
                    "host": diagnostic_tool.phoenix_host,
                    "port": diagnostic_tool.phoenix_port,
                    "base_url": diagnostic_tool.base_url
                },
                "timestamp": time.time(),
                "regulatory_impact": "HIGH - Cannot validate observability compliance without diagnostic information"
            }
        ) from e


if __name__ == "__main__":
    sys.exit(main())
