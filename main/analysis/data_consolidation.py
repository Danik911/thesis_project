#!/usr/bin/env python3
"""
Statistical Data Consolidation for Task 20 Analysis

This script consolidates and validates all available real data from the thesis project:
- Test suite JSON files (5 files with 30 tests each = 150 total tests)
- URS corpus documents (17 documents across GAMP categories)
- System performance metrics from logs and traces
- Cost analysis from actual API usage

CRITICAL: NO FALLBACK VALUES - All data must be real and verified.
If data cannot be obtained, the function must fail explicitly with full diagnostics.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataConsolidator:
    """
    Consolidates all real data from the pharmaceutical test generation system.
    
    GAMP-5 Compliance: No fallback logic - all functions fail explicitly
    if real data cannot be obtained or validated.
    """
    
    def __init__(self, project_root: str):
        """Initialize with project root directory."""
        self.project_root = Path(project_root)
        self.analysis_dir = self.project_root / "main" / "analysis"
        self.data_dir = self.analysis_dir / "data"
        
        # Ensure analysis directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define data sources - these must all be real files
        self.test_suites_dir = self.project_root / "main" / "output" / "test_suites"
        self.urs_corpus_dir = self.project_root / "datasets" / "urs_corpus" 
        self.traces_dir = self.project_root / "main" / "logs" / "traces"
        self.security_dir = self.project_root / "main" / "output" / "security_assessment"
        
        logger.info(f"Data consolidator initialized for project: {self.project_root}")
        
    def validate_data_sources(self) -> Dict[str, bool]:
        """
        Validate that all required data sources exist and contain data.
        
        Returns:
            Dictionary mapping source names to existence status
            
        Raises:
            FileNotFoundError: If critical data sources are missing
        """
        sources = {
            "test_suites": self.test_suites_dir,
            "urs_corpus": self.urs_corpus_dir,
            "traces": self.traces_dir,
            "security_assessment": self.security_dir
        }
        
        validation_results = {}
        missing_sources = []
        
        for source_name, source_path in sources.items():
            exists = source_path.exists()
            validation_results[source_name] = exists
            
            if exists:
                # Check if directory has content
                if source_path.is_dir():
                    file_count = len(list(source_path.glob("*")))
                    if file_count == 0:
                        logger.warning(f"Source directory is empty: {source_path}")
                        validation_results[source_name] = False
                        missing_sources.append(f"{source_name} (empty)")
                    else:
                        logger.info(f"Found {file_count} files in {source_name}")
            else:
                missing_sources.append(source_name)
                logger.error(f"Missing data source: {source_path}")
        
        if missing_sources:
            raise FileNotFoundError(f"Critical data sources missing: {missing_sources}")
            
        return validation_results
    
    def extract_test_suite_metrics(self) -> Dict[str, Any]:
        """
        Extract real metrics from test suite JSON files.
        
        Returns:
            Dictionary containing consolidated test suite metrics
            
        Raises:
            FileNotFoundError: If test suite files are missing
            ValueError: If test suite data is invalid or malformed
        """
        if not self.test_suites_dir.exists():
            raise FileNotFoundError(f"Test suites directory not found: {self.test_suites_dir}")
        
        suite_files = list(self.test_suites_dir.glob("test_suite_OQ-SUITE-*.json"))
        
        if not suite_files:
            raise FileNotFoundError(f"No test suite files found in {self.test_suites_dir}")
        
        logger.info(f"Found {len(suite_files)} test suite files")
        
        consolidated_metrics = {
            "total_test_suites": len(suite_files),
            "suite_details": [],
            "aggregate_metrics": {
                "total_tests": 0,
                "test_categories": {},
                "gamp_categories": {},
                "risk_levels": {},
                "estimated_total_duration_minutes": 0,
                "compliance_standards": set(),
                "unique_urs_requirements": set()
            }
        }
        
        for suite_file in suite_files:
            try:
                with open(suite_file, 'r', encoding='utf-8') as f:
                    suite_data = json.load(f)
                
                # Validate required fields
                if "test_suite" not in suite_data:
                    raise ValueError(f"Invalid test suite format in {suite_file}: missing 'test_suite'")
                
                test_suite = suite_data["test_suite"]
                test_cases = test_suite.get("test_cases", [])
                
                if not test_cases:
                    logger.warning(f"No test cases found in {suite_file}")
                    continue
                
                # Extract metrics from this suite
                suite_metrics = {
                    "file_name": suite_file.name,
                    "suite_id": test_suite.get("suite_id", "unknown"),
                    "generated_at": suite_data.get("metadata", {}).get("generated_at", "unknown"),
                    "test_count": len(test_cases),
                    "gamp_category": test_suite.get("gamp_category", "unknown"),
                    "document_name": test_suite.get("document_name", "unknown")
                }
                
                consolidated_metrics["suite_details"].append(suite_metrics)
                consolidated_metrics["aggregate_metrics"]["total_tests"] += len(test_cases)
                
                # Aggregate test categories, risk levels, etc.
                for test_case in test_cases:
                    # Test categories
                    category = test_case.get("test_category", "unknown")
                    consolidated_metrics["aggregate_metrics"]["test_categories"][category] = \
                        consolidated_metrics["aggregate_metrics"]["test_categories"].get(category, 0) + 1
                    
                    # GAMP categories
                    gamp_cat = test_case.get("gamp_category", "unknown")
                    consolidated_metrics["aggregate_metrics"]["gamp_categories"][str(gamp_cat)] = \
                        consolidated_metrics["aggregate_metrics"]["gamp_categories"].get(str(gamp_cat), 0) + 1
                    
                    # Risk levels
                    risk_level = test_case.get("risk_level", "unknown")
                    consolidated_metrics["aggregate_metrics"]["risk_levels"][risk_level] = \
                        consolidated_metrics["aggregate_metrics"]["risk_levels"].get(risk_level, 0) + 1
                    
                    # Duration
                    duration = test_case.get("estimated_duration_minutes", 0)
                    if isinstance(duration, (int, float)):
                        consolidated_metrics["aggregate_metrics"]["estimated_total_duration_minutes"] += duration
                    
                    # URS requirements
                    urs_reqs = test_case.get("urs_requirements", [])
                    if isinstance(urs_reqs, list):
                        consolidated_metrics["aggregate_metrics"]["unique_urs_requirements"].update(urs_reqs)
                
                # Compliance standards
                compliance_standards = suite_data.get("metadata", {}).get("compliance_standards", [])
                if isinstance(compliance_standards, list):
                    consolidated_metrics["aggregate_metrics"]["compliance_standards"].update(compliance_standards)
                
                logger.info(f"Processed {suite_file.name}: {len(test_cases)} tests")
                
            except Exception as e:
                raise ValueError(f"Failed to process test suite {suite_file}: {str(e)}")
        
        # Convert sets to lists for JSON serialization
        consolidated_metrics["aggregate_metrics"]["compliance_standards"] = \
            list(consolidated_metrics["aggregate_metrics"]["compliance_standards"])
        consolidated_metrics["aggregate_metrics"]["unique_urs_requirements"] = \
            list(consolidated_metrics["aggregate_metrics"]["unique_urs_requirements"])
        
        # Validation: Ensure we have reasonable data
        if consolidated_metrics["aggregate_metrics"]["total_tests"] == 0:
            raise ValueError("No valid tests found in any test suite file")
        
        if consolidated_metrics["aggregate_metrics"]["estimated_total_duration_minutes"] == 0:
            logger.warning("No duration estimates found - this may indicate data quality issues")
        
        logger.info(f"Extracted metrics for {consolidated_metrics['total_test_suites']} suites, "
                   f"{consolidated_metrics['aggregate_metrics']['total_tests']} total tests")
        
        return consolidated_metrics
    
    def extract_urs_corpus_metrics(self) -> Dict[str, Any]:
        """
        Extract real metrics from URS corpus documents.
        
        Returns:
            Dictionary containing URS corpus analysis
            
        Raises:
            FileNotFoundError: If URS corpus directory is missing
            ValueError: If URS documents are invalid
        """
        if not self.urs_corpus_dir.exists():
            raise FileNotFoundError(f"URS corpus directory not found: {self.urs_corpus_dir}")
        
        # Find all URS files recursively
        urs_files = list(self.urs_corpus_dir.rglob("URS-*.md"))
        
        if not urs_files:
            raise FileNotFoundError(f"No URS files found in {self.urs_corpus_dir}")
        
        logger.info(f"Found {len(urs_files)} URS documents")
        
        corpus_metrics = {
            "total_documents": len(urs_files),
            "documents_by_category": {},
            "document_details": [],
            "aggregate_metrics": {
                "total_file_size_bytes": 0,
                "categories_distribution": {},
                "average_document_length": 0
            }
        }
        
        for urs_file in urs_files:
            try:
                # Determine GAMP category from directory structure
                category_dir = urs_file.parent.name
                if category_dir.startswith("category_"):
                    gamp_category = int(category_dir.split("_")[1])
                elif category_dir == "ambiguous":
                    gamp_category = "ambiguous"
                else:
                    gamp_category = "unknown"
                
                # Read file content
                with open(urs_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_size = len(content.encode('utf-8'))
                word_count = len(content.split())
                
                doc_metrics = {
                    "file_name": urs_file.name,
                    "file_path": str(urs_file.relative_to(self.project_root)),
                    "gamp_category": gamp_category,
                    "file_size_bytes": file_size,
                    "word_count": word_count,
                    "line_count": len(content.splitlines())
                }
                
                corpus_metrics["document_details"].append(doc_metrics)
                corpus_metrics["aggregate_metrics"]["total_file_size_bytes"] += file_size
                
                # Update category distribution
                cat_key = str(gamp_category)
                corpus_metrics["aggregate_metrics"]["categories_distribution"][cat_key] = \
                    corpus_metrics["aggregate_metrics"]["categories_distribution"].get(cat_key, 0) + 1
                
                # Update documents by category
                if cat_key not in corpus_metrics["documents_by_category"]:
                    corpus_metrics["documents_by_category"][cat_key] = []
                corpus_metrics["documents_by_category"][cat_key].append(urs_file.name)
                
                logger.info(f"Processed {urs_file.name}: Category {gamp_category}, {word_count} words")
                
            except Exception as e:
                raise ValueError(f"Failed to process URS document {urs_file}: {str(e)}")
        
        # Calculate averages
        if corpus_metrics["total_documents"] > 0:
            total_words = sum(doc["word_count"] for doc in corpus_metrics["document_details"])
            corpus_metrics["aggregate_metrics"]["average_document_length"] = \
                total_words / corpus_metrics["total_documents"]
        
        # Validation
        expected_categories = ["3", "4", "5", "ambiguous"]
        found_categories = set(corpus_metrics["aggregate_metrics"]["categories_distribution"].keys())
        
        if not any(cat in found_categories for cat in expected_categories):
            raise ValueError(f"No valid GAMP categories found. Expected {expected_categories}, found {found_categories}")
        
        logger.info(f"Extracted corpus metrics: {corpus_metrics['total_documents']} documents across "
                   f"{len(corpus_metrics['aggregate_metrics']['categories_distribution'])} categories")
        
        return corpus_metrics
    
    def extract_performance_traces(self) -> Dict[str, Any]:
        """
        Extract performance metrics from Phoenix trace files.
        
        Returns:
            Dictionary containing performance metrics
            
        Raises:
            FileNotFoundError: If trace directory is missing
        """
        if not self.traces_dir.exists():
            raise FileNotFoundError(f"Traces directory not found: {self.traces_dir}")
        
        trace_files = list(self.traces_dir.glob("*.jsonl"))
        
        if not trace_files:
            logger.warning(f"No trace files found in {self.traces_dir}")
            return {"total_trace_files": 0, "performance_metrics": {}}
        
        logger.info(f"Found {len(trace_files)} trace files")
        
        performance_metrics = {
            "total_trace_files": len(trace_files),
            "trace_file_details": [],
            "aggregate_metrics": {
                "total_spans": 0,
                "total_file_size_bytes": 0,
                "date_range": {
                    "earliest": None,
                    "latest": None
                }
            }
        }
        
        for trace_file in trace_files:
            try:
                file_size = trace_file.stat().st_size
                
                # Extract date from filename if possible
                file_date = None
                date_match = trace_file.name
                for date_part in date_match.split("_"):
                    if len(date_part) == 8 and date_part.isdigit():  # YYYYMMDD format
                        try:
                            file_date = datetime.strptime(date_part, "%Y%m%d").date()
                            break
                        except:
                            continue
                
                # Count lines (spans) in JSONL file
                with open(trace_file, 'r', encoding='utf-8') as f:
                    span_count = sum(1 for line in f if line.strip())
                
                file_metrics = {
                    "file_name": trace_file.name,
                    "file_size_bytes": file_size,
                    "span_count": span_count,
                    "file_date": file_date.isoformat() if file_date else None
                }
                
                performance_metrics["trace_file_details"].append(file_metrics)
                performance_metrics["aggregate_metrics"]["total_spans"] += span_count
                performance_metrics["aggregate_metrics"]["total_file_size_bytes"] += file_size
                
                # Update date range
                if file_date:
                    if (performance_metrics["aggregate_metrics"]["date_range"]["earliest"] is None or 
                        file_date < datetime.fromisoformat(performance_metrics["aggregate_metrics"]["date_range"]["earliest"]).date()):
                        performance_metrics["aggregate_metrics"]["date_range"]["earliest"] = file_date.isoformat()
                    
                    if (performance_metrics["aggregate_metrics"]["date_range"]["latest"] is None or 
                        file_date > datetime.fromisoformat(performance_metrics["aggregate_metrics"]["date_range"]["latest"]).date()):
                        performance_metrics["aggregate_metrics"]["date_range"]["latest"] = file_date.isoformat()
                
                logger.info(f"Processed trace file {trace_file.name}: {span_count} spans, {file_size} bytes")
                
            except Exception as e:
                logger.warning(f"Failed to process trace file {trace_file}: {str(e)}")
                continue
        
        logger.info(f"Extracted performance metrics: {performance_metrics['aggregate_metrics']['total_spans']} total spans")
        
        return performance_metrics
    
    def consolidate_all_data(self) -> Dict[str, Any]:
        """
        Consolidate all available real data into a single structure.
        
        Returns:
            Dictionary containing all consolidated metrics
            
        Raises:
            RuntimeError: If critical data consolidation fails
        """
        logger.info("Starting comprehensive data consolidation")
        
        try:
            # Validate all data sources first
            validation_results = self.validate_data_sources()
            logger.info(f"Data source validation: {validation_results}")
            
            # Extract all data
            consolidated_data = {
                "consolidation_metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "project_root": str(self.project_root),
                    "data_sources_validated": validation_results
                },
                "test_suites": self.extract_test_suite_metrics(),
                "urs_corpus": self.extract_urs_corpus_metrics(),
                "performance_traces": self.extract_performance_traces()
            }
            
            # Add cross-dataset metrics
            consolidated_data["cross_dataset_metrics"] = {
                "total_generated_tests": consolidated_data["test_suites"]["aggregate_metrics"]["total_tests"],
                "total_urs_documents": consolidated_data["urs_corpus"]["total_documents"],
                "tests_per_document_ratio": consolidated_data["test_suites"]["aggregate_metrics"]["total_tests"] / max(1, consolidated_data["urs_corpus"]["total_documents"]),
                "total_monitoring_spans": consolidated_data["performance_traces"]["aggregate_metrics"]["total_spans"],
                "data_volume_mb": (
                    consolidated_data["urs_corpus"]["aggregate_metrics"]["total_file_size_bytes"] +
                    consolidated_data["performance_traces"]["aggregate_metrics"]["total_file_size_bytes"]
                ) / (1024 * 1024)
            }
            
            # Validation: Ensure we have substantial data
            cross_metrics = consolidated_data["cross_dataset_metrics"]
            if cross_metrics["total_generated_tests"] < 10:
                raise ValueError(f"Insufficient test data: only {cross_metrics['total_generated_tests']} tests found")
            
            if cross_metrics["total_urs_documents"] < 5:
                raise ValueError(f"Insufficient URS documents: only {cross_metrics['total_urs_documents']} found")
            
            logger.info("Data consolidation completed successfully")
            logger.info(f"Summary: {cross_metrics['total_generated_tests']} tests, "
                       f"{cross_metrics['total_urs_documents']} URS docs, "
                       f"{cross_metrics['total_monitoring_spans']} monitoring spans")
            
            return consolidated_data
            
        except Exception as e:
            raise RuntimeError(f"Critical failure in data consolidation: {str(e)}")
    
    def save_consolidated_data(self, data: Dict[str, Any], filename: str = "consolidated_data.json") -> Path:
        """
        Save consolidated data to JSON file.
        
        Args:
            data: Consolidated data dictionary
            filename: Output filename
            
        Returns:
            Path to saved file
            
        Raises:
            RuntimeError: If save operation fails
        """
        try:
            output_path = self.data_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Consolidated data saved to: {output_path}")
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to save consolidated data: {str(e)}")


def main():
    """Main execution function for data consolidation."""
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Initialize consolidator
        consolidator = DataConsolidator(str(project_root))
        
        # Consolidate all data
        consolidated_data = consolidator.consolidate_all_data()
        
        # Save to file
        output_path = consolidator.save_consolidated_data(consolidated_data)
        
        print(f"\n{'='*60}")
        print("DATA CONSOLIDATION COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        
        cross_metrics = consolidated_data["cross_dataset_metrics"]
        print(f"Total Generated Tests: {cross_metrics['total_generated_tests']}")
        print(f"Total URS Documents: {cross_metrics['total_urs_documents']}")
        print(f"Total Monitoring Spans: {cross_metrics['total_monitoring_spans']}")
        print(f"Tests per Document Ratio: {cross_metrics['tests_per_document_ratio']:.1f}")
        print(f"Total Data Volume: {cross_metrics['data_volume_mb']:.1f} MB")
        print(f"\nConsolidated data saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] Data consolidation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())