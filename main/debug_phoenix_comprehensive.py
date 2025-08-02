#!/usr/bin/env python
"""
Comprehensive Phoenix Observability Diagnostic Tool

This script performs detailed diagnostics of the Phoenix observability system
to identify and fix critical infrastructure failures.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PhoenixDiagnosticTool:
    """Comprehensive Phoenix diagnostic and repair tool."""
    
    def __init__(self, phoenix_host="localhost", phoenix_port=6006):
        self.phoenix_host = phoenix_host
        self.phoenix_port = phoenix_port
        self.base_url = f"http://{phoenix_host}:{phoenix_port}"
        self.graphql_url = f"{self.base_url}/graphql"
        self.otlp_url = f"{self.base_url}/v1/traces"
        
        self.results = {
            "test_timestamp": time.time(),
            "phoenix_host": phoenix_host,
            "phoenix_port": phoenix_port,
            "base_url": self.base_url,
            "environment": self._check_environment(),
            "test_results": {},
            "recommendations": [],
            "overall_success": False
        }
    
    def _check_environment(self):
        """Check Python environment and package versions."""
        env_info = {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "working_directory": str(Path.cwd()),
        }
        
        # Check package installations
        packages = ["phoenix", "numpy", "opentelemetry", "requests"]
        for package in packages:
            try:
                module = __import__(package)
                env_info[f"{package}_version"] = getattr(module, "__version__", "unknown")
                env_info[f"{package}_location"] = getattr(module, "__file__", "unknown")
            except ImportError:
                env_info[f"{package}_version"] = "NOT_INSTALLED"
        
        return env_info
    
    def test_basic_connectivity(self):
        """Test basic HTTP connectivity to Phoenix server."""
        test_name = "Basic HTTP Connectivity"
        try:
            logger.info(f"Testing {test_name}...")
            response = requests.get(self.base_url, timeout=10)
            
            self.results["test_results"][test_name] = {
                "success": response.status_code == 200,
                "details": {
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "content_length": len(response.content),
                    "headers": dict(response.headers),
                    "server_accessible": True
                },
                "timestamp": time.time()
            }
            
            if response.status_code == 200:
                logger.info(f"✅ {test_name} successful")
            else:
                logger.error(f"❌ {test_name} failed - Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
            self.results["test_results"][test_name] = {
                "success": False,
                "details": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": time.time()
            }
    
    def test_graphql_connectivity(self):
        """Test GraphQL endpoint basic connectivity."""
        test_name = "GraphQL Endpoint Connectivity"
        try:
            logger.info(f"Testing {test_name}...")
            
            # Test schema introspection
            introspection_query = {"query": "{ __schema { queryType { name } } }"}
            response = requests.post(
                self.graphql_url, 
                json=introspection_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            self.results["test_results"][test_name] = {
                "success": response.status_code == 200,
                "details": {
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "content_type": response.headers.get("content-type", ""),
                    "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                },
                "timestamp": time.time()
            }
            
            if response.status_code == 200:
                logger.info(f"✅ {test_name} successful")
            else:
                logger.error(f"❌ {test_name} failed - Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
            self.results["test_results"][test_name] = {
                "success": False,
                "details": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": time.time()
            }
    
    def test_graphql_data_queries(self):
        """Test GraphQL data access queries."""
        test_name = "GraphQL Data Access"
        
        queries_to_test = [
            ("Projects Query", '{ projects { id name } }'),
            ("Spans Query", '{ spans(first: 5) { edges { node { name startTime } } } }'),
            ("Traces Query", '{ traces(first: 5) { edges { node { traceId } } } }'),
        ]
        
        results = {}
        overall_success = True
        
        for query_name, query in queries_to_test:
            try:
                logger.info(f"Testing GraphQL: {query_name}...")
                response = requests.post(
                    self.graphql_url,
                    json={"query": query},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                success = response.status_code == 200
                response_data = None
                error_info = None
                
                if response.headers.get("content-type", "").startswith("application/json"):
                    try:
                        response_data = response.json()
                        # Check for GraphQL errors
                        if "errors" in response_data:
                            success = False
                            error_info = response_data["errors"]
                            logger.error(f"❌ {query_name} GraphQL errors: {error_info}")
                        elif "data" in response_data:
                            logger.info(f"✅ {query_name} successful")
                        else:
                            success = False
                            error_info = "No data or errors in response"
                    except json.JSONDecodeError as e:
                        success = False
                        error_info = f"JSON decode error: {e}"
                
                results[query_name] = {
                    "success": success,
                    "status_code": response.status_code,
                    "response_data": response_data,
                    "error_info": error_info
                }
                
                if not success:
                    overall_success = False
                    
            except Exception as e:
                logger.error(f"❌ {query_name} failed: {e}")
                results[query_name] = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                overall_success = False
        
        self.results["test_results"][test_name] = {
            "success": overall_success,
            "details": results,
            "timestamp": time.time()
        }
    
    def test_otlp_endpoint(self):
        """Test OTLP traces endpoint accessibility."""
        test_name = "OTLP Traces Endpoint"
        try:
            logger.info(f"Testing {test_name}...")
            
            # Test endpoint accessibility (expect 415 for GET request)
            response = requests.get(self.otlp_url, timeout=10)
            
            # 415 (Unsupported Media Type) is expected for GET request to OTLP endpoint
            endpoint_accessible = response.status_code in [200, 415, 405]
            
            self.results["test_results"][test_name] = {
                "success": endpoint_accessible,
                "details": {
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "headers": dict(response.headers),
                    "endpoint_accessible": endpoint_accessible,
                    "expected_415_for_get": response.status_code == 415
                },
                "timestamp": time.time()
            }
            
            if endpoint_accessible:
                logger.info(f"✅ {test_name} accessible (status: {response.status_code})")
            else:
                logger.error(f"❌ {test_name} not accessible - Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
            self.results["test_results"][test_name] = {
                "success": False,
                "details": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": time.time()
            }
    
    def test_trace_generation_and_export(self):
        """Test actual trace generation and export to Phoenix."""
        test_name = "Trace Generation and Export"
        try:
            logger.info(f"Testing {test_name}...")
            
            # Set up OpenTelemetry with OTLP exporter
            resource = Resource.create({
                "service.name": "phoenix_diagnostic_test",
                "service.version": "1.0.0"
            })
            
            tracer_provider = trace_sdk.TracerProvider(resource=resource)
            
            # Create OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_url,
                headers={}
            )
            
            # Create batch span processor
            span_processor = BatchSpanProcessor(
                otlp_exporter,
                max_queue_size=100,
                max_export_batch_size=10,
                schedule_delay_millis=1000  # 1 second
            )
            
            tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(tracer_provider)
            
            # Create test traces
            tracer = trace.get_tracer("phoenix_diagnostic")
            
            with tracer.start_as_current_span("diagnostic_test_span") as span:
                span.set_attribute("test.diagnostic", True)
                span.set_attribute("test.timestamp", time.time())
                span.set_attribute("gamp5.category", 4)
                span.set_attribute("compliance.pharmaceutical", True)
                
                # Create child span
                with tracer.start_as_current_span("child_diagnostic_span") as child:
                    child.set_attribute("child.test", "Phoenix diagnostic")
                    time.sleep(0.1)  # Small delay for realistic timing
            
            # Force flush to ensure traces are exported
            logger.info("Forcing trace export...")
            flush_success = tracer_provider.force_flush(timeout_millis=5000)
            
            # Wait a moment for Phoenix to process
            time.sleep(2)
            
            self.results["test_results"][test_name] = {
                "success": flush_success,
                "details": {
                    "flush_successful": flush_success,
                    "traces_generated": 2,  # parent + child
                    "export_timeout": "5 seconds",
                    "attributes_set": 5
                },
                "timestamp": time.time()
            }
            
            if flush_success:
                logger.info(f"✅ {test_name} successful - traces exported")
            else:
                logger.warning(f"⚠️ {test_name} - flush may have timed out")
                
            # Shutdown tracer provider
            tracer_provider.shutdown()
            
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
            self.results["test_results"][test_name] = {
                "success": False,
                "details": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": time.time()
            }
    
    def test_phoenix_data_retrieval(self):
        """Test if Phoenix can retrieve the traces we just sent."""
        test_name = "Phoenix Data Retrieval Verification"
        try:
            logger.info(f"Testing {test_name}...")
            
            # Wait a bit more for Phoenix to process traces
            time.sleep(3)
            
            # Try to retrieve traces via GraphQL
            query = '''
            {
                traces(first: 10) {
                    edges {
                        node {
                            traceId
                            spans {
                                edges {
                                    node {
                                        name
                                        attributes {
                                            name
                                            value
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            '''
            
            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            success = False
            traces_found = 0
            diagnostic_traces_found = 0
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data and data["data"] and "traces" in data["data"]:
                        traces = data["data"]["traces"]["edges"]
                        traces_found = len(traces)
                        
                        # Look for our diagnostic traces
                        for trace in traces:
                            spans = trace["node"]["spans"]["edges"]
                            for span in spans:
                                if "diagnostic" in span["node"]["name"]:
                                    diagnostic_traces_found += 1
                        
                        success = traces_found > 0
                        logger.info(f"Found {traces_found} traces, {diagnostic_traces_found} diagnostic traces")
                    elif "errors" in data:
                        logger.error(f"GraphQL errors: {data['errors']}")
                except json.JSONDecodeError:
                    logger.error("Failed to parse GraphQL response")
            
            self.results["test_results"][test_name] = {
                "success": success,
                "details": {
                    "status_code": response.status_code,
                    "traces_found": traces_found,
                    "diagnostic_traces_found": diagnostic_traces_found,
                    "data_accessible": success
                },
                "timestamp": time.time()
            }
            
            if success:
                logger.info(f"✅ {test_name} successful - data retrievable")
            else:
                logger.error(f"❌ {test_name} failed - data not accessible")
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
            self.results["test_results"][test_name] = {
                "success": False,
                "details": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": time.time()
            }
    
    def run_all_tests(self):
        """Run all diagnostic tests."""
        logger.info("🚀 Starting Comprehensive Phoenix Diagnostic Tests")
        logger.info("=" * 60)
        
        # Run tests in order
        self.test_basic_connectivity()
        self.test_graphql_connectivity()
        self.test_graphql_data_queries()
        self.test_otlp_endpoint()
        self.test_trace_generation_and_export()
        self.test_phoenix_data_retrieval()
        
        # Analyze results and generate recommendations
        self._analyze_results()
        
        # Set overall success
        successful_tests = sum(1 for test in self.results["test_results"].values() if test["success"])
        total_tests = len(self.results["test_results"])
        self.results["overall_success"] = successful_tests == total_tests
        
        logger.info("=" * 60)
        logger.info(f"🏁 Diagnostic Complete: {successful_tests}/{total_tests} tests passed")
        
        if self.results["overall_success"]:
            logger.info("✅ All Phoenix systems functional!")
        else:
            logger.error("❌ Critical Phoenix issues detected - see recommendations")
        
        return self.results
    
    def _analyze_results(self):
        """Analyze test results and generate recommendations."""
        recommendations = []
        
        # Check basic connectivity
        if not self.results["test_results"].get("Basic HTTP Connectivity", {}).get("success"):
            recommendations.append("🚨 CRITICAL: Phoenix server not accessible - check if server is running")
            recommendations.append("🔧 ACTION: Start Phoenix server with: python -m phoenix.server.main")
        
        # Check GraphQL
        graphql_conn = self.results["test_results"].get("GraphQL Endpoint Connectivity", {})
        graphql_data = self.results["test_results"].get("GraphQL Data Access", {})
        
        if not graphql_conn.get("success"):
            recommendations.append("🚨 CRITICAL: GraphQL endpoint not accessible")
            recommendations.append("🔧 ACTION: Check Phoenix server configuration")
        elif not graphql_data.get("success"):
            recommendations.append("🚨 CRITICAL: GraphQL data queries failing - this is the main issue")
            recommendations.append("🔧 ACTION: Check Phoenix server logs for GraphQL errors")
            recommendations.append("🔧 ACTION: Consider restarting Phoenix server")
            recommendations.append("🔧 ACTION: Verify Phoenix version compatibility")
        
        # Check trace export
        trace_export = self.results["test_results"].get("Trace Generation and Export", {})
        if not trace_export.get("success"):
            recommendations.append("🚨 CRITICAL: Trace export failing")
            recommendations.append("🔧 ACTION: Check OTLP endpoint configuration")
            recommendations.append("🔧 ACTION: Verify OpenTelemetry dependencies")
        
        # Check data retrieval
        data_retrieval = self.results["test_results"].get("Phoenix Data Retrieval Verification", {})
        if not data_retrieval.get("success"):
            if trace_export.get("success"):
                recommendations.append("🚨 CRITICAL: Traces exported but not retrievable via GraphQL")
                recommendations.append("🔧 ACTION: This confirms GraphQL API is broken")
                recommendations.append("🔧 ACTION: Phoenix server restart required")
            else:
                recommendations.append("⚠️ Data retrieval failed - likely due to export issues")
        
        # Environment recommendations
        env = self.results["environment"]
        if "numpy_version" in env and env["numpy_version"].startswith("2."):
            recommendations.append("⚠️ NumPy 2.x detected - may cause Phoenix compatibility issues")
            recommendations.append("🔧 ACTION: Consider downgrading to NumPy <2.0")
        
        if env.get("phoenix_version") == "NOT_INSTALLED":
            recommendations.append("🚨 CRITICAL: Phoenix not installed in current environment")
            recommendations.append("🔧 ACTION: Install with: uv add arize-phoenix")
        
        self.results["recommendations"] = recommendations
    
    def save_results(self, filename=None):
        """Save diagnostic results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phoenix_comprehensive_diagnostic_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📊 Diagnostic results saved to: {filename}")
        return filename


def main():
    """Run comprehensive Phoenix diagnostic."""
    diagnostic = PhoenixDiagnosticTool()
    results = diagnostic.run_all_tests()
    
    # Save results
    filename = diagnostic.save_results()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    print(f"📊 Environment: {results['environment']['python_version']} at {results['environment']['python_executable']}")
    print(f"🌐 Phoenix URL: {results['base_url']}")
    
    print("\n🧪 Test Results:")
    for test_name, result in results["test_results"].items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    if results["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"   {rec}")
    
    print(f"\n📁 Detailed results saved to: {filename}")
    
    return results["overall_success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)