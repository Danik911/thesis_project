#!/usr/bin/env python3
"""
Phoenix Trace Deep Analysis Script
Analyzes trace files (JSONL) to extract agent performance and workflow metrics
"""

import json
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime
import statistics

class TraceAnalyzer:
    def __init__(self, traces_path):
        """Initialize with path to traces directory"""
        self.traces_path = Path(traces_path)
        self.traces = []
        self.spans = []
        self.load_traces()
    
    def load_traces(self):
        """Load all trace JSONL files"""
        # Find all trace files
        trace_files = glob.glob(str(self.traces_path / "**" / "*traces.jsonl"), recursive=True)
        
        for file_path in trace_files:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        span = json.loads(line.strip())
                        span['source_file'] = Path(file_path).name
                        span['document'] = Path(file_path).stem.replace('_traces', '')
                        self.spans.append(span)
                    except json.JSONDecodeError:
                        continue
        
        print(f"Loaded {len(self.spans)} spans from {len(trace_files)} trace files")
    
    def categorize_span(self, span):
        """Categorize a span by agent or operation type"""
        name = span.get('name', '').lower()
        span_type = span.get('type', '').lower()
        
        # Agent categorization
        if 'categorization' in name or 'gamp' in name:
            return 'categorization_agent'
        elif 'context' in name or 'provider' in name:
            return 'context_provider'
        elif 'research' in name:
            return 'research_agent'
        elif 'sme' in name or 'subject' in name:
            return 'sme_agent'
        elif 'generator' in name or 'oq' in name or 'test' in name:
            return 'oq_generator'
        elif 'workflow' in name or 'orchestr' in name:
            return 'workflow'
        elif 'chromadb' in name or 'vector' in name or 'embedding' in name:
            return 'chromadb'
        elif 'llm' in name or 'completion' in name or 'chat' in name:
            return 'llm_call'
        else:
            return 'other'
    
    def analyze_agent_performance(self):
        """Analyze performance by agent type"""
        agent_metrics = defaultdict(lambda: {
            'count': 0,
            'durations': [],
            'errors': 0,
            'token_usage': {'input': [], 'output': []},
            'documents': set()
        })
        
        for span in self.spans:
            agent_type = self.categorize_span(span)
            metrics = agent_metrics[agent_type]
            
            metrics['count'] += 1
            metrics['documents'].add(span.get('document', 'unknown'))
            
            # Duration (convert to milliseconds if in nanoseconds)
            if 'duration_ns' in span:
                duration_ms = span['duration_ns'] / 1_000_000
                metrics['durations'].append(duration_ms)
            elif 'duration_ms' in span:
                metrics['durations'].append(span['duration_ms'])
            elif 'duration' in span:
                # Assume milliseconds if unit not specified
                metrics['durations'].append(span['duration'])
            
            # Error tracking
            if span.get('status') == 'error' or span.get('error', False):
                metrics['errors'] += 1
            
            # Token usage (if available)
            if 'attributes' in span:
                attrs = span['attributes']
                if 'llm.token_count.prompt' in attrs:
                    metrics['token_usage']['input'].append(attrs['llm.token_count.prompt'])
                if 'llm.token_count.completion' in attrs:
                    metrics['token_usage']['output'].append(attrs['llm.token_count.completion'])
        
        # Calculate statistics
        results = {}
        for agent_type, metrics in agent_metrics.items():
            if metrics['durations']:
                results[agent_type] = {
                    'span_count': metrics['count'],
                    'error_count': metrics['errors'],
                    'error_rate': metrics['errors'] / metrics['count'] * 100 if metrics['count'] > 0 else 0,
                    'documents_processed': len(metrics['documents']),
                    'duration_stats': {
                        'mean': statistics.mean(metrics['durations']),
                        'median': statistics.median(metrics['durations']),
                        'std': statistics.stdev(metrics['durations']) if len(metrics['durations']) > 1 else 0,
                        'min': min(metrics['durations']),
                        'max': max(metrics['durations']),
                        'p50': np.percentile(metrics['durations'], 50),
                        'p75': np.percentile(metrics['durations'], 75),
                        'p90': np.percentile(metrics['durations'], 90),
                        'p95': np.percentile(metrics['durations'], 95),
                        'p99': np.percentile(metrics['durations'], 99)
                    },
                    'token_usage': {
                        'total_input_tokens': sum(metrics['token_usage']['input']),
                        'total_output_tokens': sum(metrics['token_usage']['output']),
                        'avg_input_tokens': statistics.mean(metrics['token_usage']['input']) if metrics['token_usage']['input'] else 0,
                        'avg_output_tokens': statistics.mean(metrics['token_usage']['output']) if metrics['token_usage']['output'] else 0
                    }
                }
            else:
                results[agent_type] = {
                    'span_count': metrics['count'],
                    'error_count': metrics['errors'],
                    'error_rate': metrics['errors'] / metrics['count'] * 100 if metrics['count'] > 0 else 0,
                    'documents_processed': len(metrics['documents'])
                }
        
        return results
    
    def analyze_chromadb_operations(self):
        """Analyze ChromaDB vector database operations"""
        chromadb_spans = [s for s in self.spans if 'chromadb' in self.categorize_span(s)]
        
        if not chromadb_spans:
            return {"message": "No ChromaDB operations found"}
        
        operations = defaultdict(list)
        for span in chromadb_spans:
            op_type = span.get('operation', 'unknown')
            if 'query' in span.get('name', '').lower():
                op_type = 'query'
            elif 'add' in span.get('name', '').lower() or 'insert' in span.get('name', '').lower():
                op_type = 'insert'
            elif 'embed' in span.get('name', '').lower():
                op_type = 'embedding'
            
            duration = 0
            if 'duration_ns' in span:
                duration = span['duration_ns'] / 1_000_000
            elif 'duration_ms' in span:
                duration = span['duration_ms']
            
            operations[op_type].append({
                'duration': duration,
                'document': span.get('document', 'unknown')
            })
        
        # Calculate statistics
        results = {}
        for op_type, ops in operations.items():
            durations = [op['duration'] for op in ops if op['duration'] > 0]
            if durations:
                results[op_type] = {
                    'count': len(ops),
                    'duration_stats': {
                        'mean': statistics.mean(durations),
                        'median': statistics.median(durations),
                        'min': min(durations),
                        'max': max(durations),
                        'p90': np.percentile(durations, 90),
                        'p95': np.percentile(durations, 95)
                    }
                }
        
        results['total_operations'] = len(chromadb_spans)
        return results
    
    def analyze_workflow_patterns(self):
        """Analyze workflow execution patterns"""
        # Group spans by document
        document_spans = defaultdict(list)
        for span in self.spans:
            doc = span.get('document', 'unknown')
            document_spans[doc].append(span)
        
        workflow_metrics = {}
        for doc, spans in document_spans.items():
            # Sort spans by start time if available
            if spans and 'start_time' in spans[0]:
                spans.sort(key=lambda x: x.get('start_time', 0))
            
            # Calculate total execution time
            durations = []
            for span in spans:
                if 'duration_ns' in span:
                    durations.append(span['duration_ns'] / 1_000_000)
                elif 'duration_ms' in span:
                    durations.append(span['duration_ms'])
            
            # Identify agent sequence
            agent_sequence = [self.categorize_span(s) for s in spans]
            agent_counts = Counter(agent_sequence)
            
            workflow_metrics[doc] = {
                'total_spans': len(spans),
                'total_duration_ms': sum(durations) if durations else 0,
                'unique_agents': len(set(agent_sequence)),
                'agent_distribution': dict(agent_counts),
                'dominant_agent': agent_counts.most_common(1)[0][0] if agent_counts else 'none'
            }
        
        return workflow_metrics
    
    def identify_bottlenecks(self):
        """Identify performance bottlenecks"""
        bottlenecks = {
            'slowest_operations': [],
            'most_frequent_operations': [],
            'error_prone_operations': []
        }
        
        # Find slowest operations
        slow_spans = []
        for span in self.spans:
            duration = 0
            if 'duration_ns' in span:
                duration = span['duration_ns'] / 1_000_000
            elif 'duration_ms' in span:
                duration = span['duration_ms']
            
            if duration > 0:
                slow_spans.append({
                    'name': span.get('name', 'unknown'),
                    'type': self.categorize_span(span),
                    'duration_ms': duration,
                    'document': span.get('document', 'unknown')
                })
        
        # Sort and get top 10 slowest
        slow_spans.sort(key=lambda x: x['duration_ms'], reverse=True)
        bottlenecks['slowest_operations'] = slow_spans[:10]
        
        # Find most frequent operations
        operation_counts = Counter([self.categorize_span(s) for s in self.spans])
        bottlenecks['most_frequent_operations'] = [
            {'operation': op, 'count': count} 
            for op, count in operation_counts.most_common(5)
        ]
        
        # Find error-prone operations
        error_operations = defaultdict(int)
        total_operations = defaultdict(int)
        for span in self.spans:
            op_type = self.categorize_span(span)
            total_operations[op_type] += 1
            if span.get('status') == 'error' or span.get('error', False):
                error_operations[op_type] += 1
        
        error_rates = []
        for op_type in total_operations:
            if total_operations[op_type] > 10:  # Only consider operations with sufficient samples
                error_rate = error_operations[op_type] / total_operations[op_type] * 100
                if error_rate > 0:
                    error_rates.append({
                        'operation': op_type,
                        'error_rate': error_rate,
                        'errors': error_operations[op_type],
                        'total': total_operations[op_type]
                    })
        
        error_rates.sort(key=lambda x: x['error_rate'], reverse=True)
        bottlenecks['error_prone_operations'] = error_rates[:5]
        
        return bottlenecks
    
    def calculate_parallel_efficiency(self):
        """Calculate parallel processing efficiency"""
        # Group spans by document and time windows
        document_timelines = defaultdict(list)
        
        for span in self.spans:
            if 'start_time' in span and 'end_time' in span:
                document_timelines[span.get('document', 'unknown')].append({
                    'start': span['start_time'],
                    'end': span['end_time'],
                    'agent': self.categorize_span(span)
                })
        
        efficiency_metrics = {}
        for doc, timeline in document_timelines.items():
            if not timeline:
                continue
            
            # Sort by start time
            timeline.sort(key=lambda x: x['start'])
            
            # Calculate overlapping operations (parallel execution)
            overlaps = 0
            for i in range(len(timeline)):
                for j in range(i + 1, len(timeline)):
                    # Check if spans overlap
                    if timeline[i]['end'] > timeline[j]['start'] and timeline[i]['start'] < timeline[j]['end']:
                        overlaps += 1
            
            total_pairs = len(timeline) * (len(timeline) - 1) / 2
            parallel_ratio = overlaps / total_pairs if total_pairs > 0 else 0
            
            efficiency_metrics[doc] = {
                'total_operations': len(timeline),
                'overlapping_operations': overlaps,
                'parallel_ratio': parallel_ratio * 100  # Percentage
            }
        
        return efficiency_metrics
    
    def generate_report(self):
        """Generate comprehensive trace analysis report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_spans': len(self.spans),
                'unique_documents': len(set(s.get('document', 'unknown') for s in self.spans)),
                'span_types': dict(Counter([self.categorize_span(s) for s in self.spans]))
            },
            'agent_performance': self.analyze_agent_performance(),
            'chromadb_operations': self.analyze_chromadb_operations(),
            'workflow_patterns': self.analyze_workflow_patterns(),
            'bottlenecks': self.identify_bottlenecks(),
            'parallel_efficiency': self.calculate_parallel_efficiency()
        }
        
        return report
    
    def save_report(self, output_path):
        """Save analysis report to JSON"""
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nTrace analysis report saved to {output_path}")
        
        # Print summary
        print("\n=== Trace Analysis Summary ===")
        print(f"Total Spans: {report['summary']['total_spans']}")
        print(f"Documents Processed: {report['summary']['unique_documents']}")
        
        print("\n=== Agent Performance (Top 5) ===")
        agent_perf = report['agent_performance']
        sorted_agents = sorted(agent_perf.items(), 
                              key=lambda x: x[1]['span_count'], 
                              reverse=True)[:5]
        for agent, metrics in sorted_agents:
            print(f"{agent}:")
            print(f"  Spans: {metrics['span_count']}")
            if 'duration_stats' in metrics:
                print(f"  Avg Duration: {metrics['duration_stats']['mean']:.2f}ms")
                print(f"  P95 Duration: {metrics['duration_stats']['p95']:.2f}ms")
            print(f"  Error Rate: {metrics['error_rate']:.2f}%")
        
        print("\n=== Performance Bottlenecks ===")
        print("Slowest Operations:")
        for op in report['bottlenecks']['slowest_operations'][:3]:
            print(f"  {op['type']}: {op['duration_ms']:.2f}ms ({op['document']})")
        
        print("\nMost Frequent Operations:")
        for op in report['bottlenecks']['most_frequent_operations'][:3]:
            print(f"  {op['operation']}: {op['count']} spans")


if __name__ == "__main__":
    # Path to traces directory
    traces_path = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/main_cv_execution")
    output_path = Path("C:/Users/anteb/Desktop/Courses/Projects/thesis_project/THESIS_EVIDENCE_PACKAGE/01_TEST_EXECUTION_EVIDENCE/trace_analysis_report.json")
    
    # Run analysis
    analyzer = TraceAnalyzer(traces_path)
    analyzer.save_report(output_path)