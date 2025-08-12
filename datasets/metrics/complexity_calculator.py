#!/usr/bin/env python3
"""
Complexity Calculator for URS Documents

This module provides functions to calculate various complexity metrics for URS documents
including requirement counts, readability scores, integration complexity, and composite 
complexity scores for GAMP-5 categorization validation.

GAMP-5 Compliance: No fallback logic - all functions fail explicitly with detailed
error messages if calculations cannot be completed.
"""

import re
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class URSComplexityCalculator:
    """Calculate complexity metrics for URS documents."""
    
    def __init__(self):
        """Initialize the complexity calculator with pharmaceutical-specific weights."""
        self.complexity_weights = {
            'functional_requirements': 0.25,
            'integration_complexity': 0.20,
            'dependency_density': 0.15,
            'ambiguity_rate': 0.15,
            'readability_inverse': 0.10,
            'custom_indicators': 0.15
        }
        
        self.integration_keywords = [
            'interface', 'integration', 'api', 'connector', 'middleware',
            'synchronization', 'data exchange', 'real-time', 'protocol'
        ]
        
        self.custom_indicators = [
            'custom', 'proprietary', 'develop', 'bespoke', 'algorithm',
            'machine learning', 'artificial intelligence', 'advanced analytics'
        ]
        
        self.ambiguity_keywords = [
            'tbd', 'to be determined', 'optional', 'should', 'may',
            'enhanced', 'advanced', 'sophisticated', 'innovative'
        ]

    def extract_requirements(self, urs_content: str) -> Dict[str, List[str]]:
        """
        Extract requirements from URS markdown content.
        
        Args:
            urs_content: Raw markdown content of URS document
            
        Returns:
            Dictionary with requirement types as keys and requirement lists as values
            
        Raises:
            ValueError: If URS content is empty or malformed
            RuntimeError: If requirement extraction fails
        """
        if not urs_content or not urs_content.strip():
            raise ValueError("URS content cannot be empty")
            
        try:
            requirements = {
                'functional': [],
                'performance': [],
                'regulatory': [],
                'integration': [],
                'technical': []
            }
            
            # Extract requirements using regex patterns
            patterns = {
                'functional': r'- \*\*URS-[A-Z]+-\d+\*\*:\s*(.+?)(?=\n|$)',
                'performance': r'- \*\*URS-[A-Z]+-\d+\*\*:\s*(.+?)(?=\n|$)',
                'regulatory': r'- \*\*URS-[A-Z]+-\d+\*\*:\s*(.+?)(?=\n|$)',
                'integration': r'- \*\*URS-[A-Z]+-\d+\*\*:\s*(.+?)(?=\n|$)',
                'technical': r'- \*\*URS-[A-Z]+-\d+\*\*:\s*(.+?)(?=\n|$)'
            }
            
            # Determine section context and extract requirements
            lines = urs_content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                # Identify section headers
                if '## 2. Functional Requirements' in line:
                    current_section = 'functional'
                elif '## 3. Regulatory Requirements' in line:
                    current_section = 'regulatory'
                elif '## 4. Performance Requirements' in line:
                    current_section = 'performance'
                elif '## 5. Integration Requirements' in line:
                    current_section = 'integration'
                elif '## 6. Technical' in line:
                    current_section = 'technical'
                elif line.startswith('##'):
                    current_section = None
                
                # Extract requirement if in a known section
                if current_section and line.startswith('- **URS-'):
                    match = re.search(r'- \*\*URS-[A-Z]+-\d+\*\*:\s*(.+)', line)
                    if match:
                        requirement_text = match.group(1)
                        requirements[current_section].append(requirement_text)
            
            # Validate that we found some requirements
            total_requirements = sum(len(reqs) for reqs in requirements.values())
            if total_requirements == 0:
                raise RuntimeError("No requirements found in URS document - check format")
                
            return requirements
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract requirements from URS: {str(e)}")

    def calculate_requirement_counts(self, requirements: Dict[str, List[str]]) -> Dict[str, int]:
        """
        Calculate counts for different requirement types.
        
        Args:
            requirements: Dictionary of requirement lists by type
            
        Returns:
            Dictionary with requirement counts by type
            
        Raises:
            ValueError: If requirements dictionary is invalid
        """
        if not isinstance(requirements, dict):
            raise ValueError("Requirements must be a dictionary")
            
        try:
            counts = {}
            for req_type, req_list in requirements.items():
                if not isinstance(req_list, list):
                    raise ValueError(f"Requirements for {req_type} must be a list")
                counts[req_type] = len(req_list)
            
            counts['total'] = sum(counts.values())
            return counts
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate requirement counts: {str(e)}")

    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word using basic heuristics.
        
        Args:
            word: Word to count syllables for
            
        Returns:
            Number of syllables (minimum 1)
        """
        word = word.lower().strip()
        if not word:
            return 0
        
        # Remove punctuation and digits
        word = re.sub(r'[^a-z]', '', word)
        if not word:
            return 0
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        # Ensure at least 1 syllable per word
        return max(1, syllables)

    def _count_sentences(self, text: str) -> int:
        """
        Count sentences in text using punctuation patterns.
        
        Args:
            text: Text to count sentences for
            
        Returns:
            Number of sentences (minimum 1)
        """
        if not text.strip():
            return 0
        
        # Count sentence-ending punctuation
        sentence_endings = re.findall(r'[.!?]+', text)
        sentence_count = len(sentence_endings)
        
        # Ensure at least 1 sentence if text exists
        return max(1, sentence_count)

    def calculate_readability_score(self, text: str) -> float:
        """
        Calculate readability score using Flesch-Kincaid Grade Level.
        
        Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        
        Args:
            text: Text content to analyze
            
        Returns:
            Flesch-Kincaid Grade Level score
            
        Raises:
            ValueError: If text is empty
            RuntimeError: If readability calculation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty for readability analysis")
            
        try:
            # Clean text for readability analysis
            clean_text = re.sub(r'[*#-]', '', text)  # Remove markdown formatting
            clean_text = re.sub(r'\n+', ' ', clean_text)  # Replace newlines with spaces
            
            if len(clean_text.strip()) < 100:
                raise ValueError("Text too short for reliable readability analysis (minimum 100 characters)")
            
            # Count basic text statistics
            words = clean_text.split()
            word_count = len(words)
            sentence_count = self._count_sentences(clean_text)
            syllable_count = sum(self._count_syllables(word) for word in words)
            
            if word_count == 0 or sentence_count == 0:
                raise RuntimeError("Invalid text statistics: no words or sentences found")
            
            # Calculate Flesch-Kincaid Grade Level
            avg_sentence_length = word_count / sentence_count
            avg_syllables_per_word = syllable_count / word_count
            
            fk_grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
            
            if math.isnan(fk_grade_level) or math.isinf(fk_grade_level):
                raise RuntimeError("Readability calculation returned invalid result")
                
            return float(max(0.0, fk_grade_level))  # Ensure non-negative score
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate readability score: {str(e)}")

    def calculate_integration_complexity(self, requirements: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Calculate integration complexity based on integration-related keywords.
        
        Args:
            requirements: Dictionary of requirement lists by type
            
        Returns:
            Dictionary with integration metrics
            
        Raises:
            ValueError: If requirements dictionary is invalid
        """
        if not isinstance(requirements, dict):
            raise ValueError("Requirements must be a dictionary")
            
        try:
            all_requirements = []
            for req_list in requirements.values():
                all_requirements.extend(req_list)
            
            if not all_requirements:
                raise ValueError("No requirements found for integration analysis")
            
            integration_count = 0
            total_words = 0
            
            for req in all_requirements:
                req_lower = req.lower()
                total_words += len(req.split())
                
                for keyword in self.integration_keywords:
                    if keyword in req_lower:
                        integration_count += 1
                        break  # Count each requirement only once
            
            integration_density = integration_count / len(all_requirements) if all_requirements else 0
            integration_word_ratio = sum(req.lower().count(kw) for req in all_requirements for kw in self.integration_keywords) / total_words if total_words > 0 else 0
            
            return {
                'integration_count': integration_count,
                'integration_density': integration_density,
                'integration_word_ratio': integration_word_ratio,
                'total_requirements': len(all_requirements)
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate integration complexity: {str(e)}")

    def calculate_dependency_density(self, urs_content: str) -> float:
        """
        Calculate cross-reference density within the document.
        
        Args:
            urs_content: Raw URS document content
            
        Returns:
            Dependency density score (cross-references per requirement)
            
        Raises:
            ValueError: If content is empty
            RuntimeError: If calculation fails
        """
        if not urs_content or not urs_content.strip():
            raise ValueError("URS content cannot be empty")
            
        try:
            # Count cross-references (e.g., "see URS-XXX-001", "reference section 3.2")
            cross_ref_patterns = [
                r'URS-[A-Z]+-\d+',
                r'section\s+\d+\.\d+',
                r'see\s+\d+\.\d+',
                r'reference\s+\d+\.\d+',
                r'per\s+URS-[A-Z]+-\d+'
            ]
            
            cross_refs = 0
            for pattern in cross_ref_patterns:
                matches = re.findall(pattern, urs_content, re.IGNORECASE)
                cross_refs += len(matches)
            
            # Count total requirements
            requirement_matches = re.findall(r'- \*\*URS-[A-Z]+-\d+\*\*:', urs_content)
            total_requirements = len(requirement_matches)
            
            if total_requirements == 0:
                raise RuntimeError("No requirements found for dependency analysis")
            
            dependency_density = cross_refs / total_requirements
            return dependency_density
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate dependency density: {str(e)}")

    def calculate_ambiguity_rate(self, requirements: Dict[str, List[str]]) -> float:
        """
        Calculate ambiguity rate based on ambiguous keywords.
        
        Args:
            requirements: Dictionary of requirement lists by type
            
        Returns:
            Ambiguity rate (0.0 to 1.0)
            
        Raises:
            ValueError: If requirements dictionary is invalid
        """
        if not isinstance(requirements, dict):
            raise ValueError("Requirements must be a dictionary")
            
        try:
            all_requirements = []
            for req_list in requirements.values():
                all_requirements.extend(req_list)
            
            if not all_requirements:
                raise ValueError("No requirements found for ambiguity analysis")
            
            ambiguous_count = 0
            for req in all_requirements:
                req_lower = req.lower()
                for keyword in self.ambiguity_keywords:
                    if keyword in req_lower:
                        ambiguous_count += 1
                        break  # Count each requirement only once
            
            ambiguity_rate = ambiguous_count / len(all_requirements)
            return ambiguity_rate
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate ambiguity rate: {str(e)}")

    def calculate_custom_indicators(self, requirements: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Calculate custom development indicators.
        
        Args:
            requirements: Dictionary of requirement lists by type
            
        Returns:
            Dictionary with custom development metrics
            
        Raises:
            ValueError: If requirements dictionary is invalid
        """
        if not isinstance(requirements, dict):
            raise ValueError("Requirements must be a dictionary")
            
        try:
            all_requirements = []
            for req_list in requirements.values():
                all_requirements.extend(req_list)
            
            if not all_requirements:
                raise ValueError("No requirements found for custom indicator analysis")
            
            custom_count = 0
            for req in all_requirements:
                req_lower = req.lower()
                for keyword in self.custom_indicators:
                    if keyword in req_lower:
                        custom_count += 1
                        break  # Count each requirement only once
            
            custom_rate = custom_count / len(all_requirements)
            return {
                'custom_count': custom_count,
                'custom_rate': custom_rate,
                'total_requirements': len(all_requirements)
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate custom indicators: {str(e)}")

    def calculate_composite_complexity_score(self, metrics: Dict) -> float:
        """
        Calculate weighted composite complexity score.
        
        Args:
            metrics: Dictionary containing all calculated metrics
            
        Returns:
            Composite complexity score (0.0 to 1.0)
            
        Raises:
            ValueError: If required metrics are missing
            RuntimeError: If calculation fails
        """
        required_keys = [
            'requirement_counts', 'readability_score', 'integration_complexity',
            'dependency_density', 'ambiguity_rate', 'custom_indicators'
        ]
        
        missing_keys = [key for key in required_keys if key not in metrics]
        if missing_keys:
            raise ValueError(f"Missing required metrics: {missing_keys}")
        
        try:
            # Normalize metrics to 0-1 scale
            normalized_metrics = {}
            
            # Functional requirement count (normalize by typical pharmaceutical range 10-50)
            func_count = metrics['requirement_counts'].get('functional', 0)
            normalized_metrics['functional_requirements'] = min(func_count / 50.0, 1.0)
            
            # Integration complexity
            integration_density = metrics['integration_complexity'].get('integration_density', 0)
            normalized_metrics['integration_complexity'] = min(integration_density, 1.0)
            
            # Dependency density (normalize by typical range 0-2)
            normalized_metrics['dependency_density'] = min(metrics['dependency_density'] / 2.0, 1.0)
            
            # Ambiguity rate (already 0-1)
            normalized_metrics['ambiguity_rate'] = metrics['ambiguity_rate']
            
            # Readability (inverse - higher grade level = higher complexity, normalize by grade 20)
            readability = metrics['readability_score']
            normalized_metrics['readability_inverse'] = min(readability / 20.0, 1.0)
            
            # Custom indicators rate (already 0-1)
            normalized_metrics['custom_indicators'] = metrics['custom_indicators'].get('custom_rate', 0)
            
            # Calculate weighted composite score
            composite_score = 0.0
            for metric_name, normalized_value in normalized_metrics.items():
                weight = self.complexity_weights.get(metric_name, 0)
                composite_score += weight * normalized_value
            
            # Ensure score is between 0 and 1
            composite_score = max(0.0, min(1.0, composite_score))
            
            return composite_score
            
        except Exception as e:
            raise RuntimeError(f"Failed to calculate composite complexity score: {str(e)}")

    def analyze_urs_document(self, file_path: str) -> Dict:
        """
        Perform complete complexity analysis of a URS document.
        
        Args:
            file_path: Path to URS markdown file
            
        Returns:
            Dictionary containing all calculated metrics
            
        Raises:
            FileNotFoundError: If URS file doesn't exist
            ValueError: If file content is invalid
            RuntimeError: If analysis fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"URS file not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            # Read URS content
            with open(path, 'r', encoding='utf-8') as f:
                urs_content = f.read()
            
            if not urs_content.strip():
                raise ValueError(f"URS file is empty: {file_path}")
            
            # Extract requirements
            requirements = self.extract_requirements(urs_content)
            
            # Calculate all metrics
            metrics = {
                'document_id': path.stem,
                'file_path': str(path),
                'requirement_counts': self.calculate_requirement_counts(requirements),
                'readability_score': self.calculate_readability_score(urs_content),
                'integration_complexity': self.calculate_integration_complexity(requirements),
                'dependency_density': self.calculate_dependency_density(urs_content),
                'ambiguity_rate': self.calculate_ambiguity_rate(requirements),
                'custom_indicators': self.calculate_custom_indicators(requirements)
            }
            
            # Calculate composite score
            metrics['composite_complexity_score'] = self.calculate_composite_complexity_score(metrics)
            
            return metrics
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze URS document {file_path}: {str(e)}")


def analyze_urs_corpus(corpus_directory: str) -> List[Dict]:
    """
    Analyze all URS documents in a corpus directory.
    
    Args:
        corpus_directory: Path to directory containing URS files
        
    Returns:
        List of metric dictionaries for each URS document
        
    Raises:
        FileNotFoundError: If corpus directory doesn't exist
        RuntimeError: If analysis fails
    """
    corpus_path = Path(corpus_directory)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_directory}")
    
    calculator = URSComplexityCalculator()
    results = []
    failed_files = []
    
    # Find all URS markdown files
    urs_files = list(corpus_path.rglob("URS-*.md"))
    
    if not urs_files:
        raise RuntimeError(f"No URS files found in directory: {corpus_directory}")
    
    for urs_file in urs_files:
        try:
            metrics = calculator.analyze_urs_document(str(urs_file))
            results.append(metrics)
        except Exception as e:
            failed_files.append((str(urs_file), str(e)))
            print(f"WARNING: Failed to analyze {urs_file}: {e}")
    
    if failed_files and len(failed_files) == len(urs_files):
        raise RuntimeError(f"Failed to analyze any URS files. Errors: {failed_files}")
    
    if failed_files:
        print(f"Successfully analyzed {len(results)} files, failed to analyze {len(failed_files)} files")
    
    return results


if __name__ == "__main__":
    # Example usage
    try:
        corpus_dir = "../urs_corpus"
        results = analyze_urs_corpus(corpus_dir)
        
        print(f"Analyzed {len(results)} URS documents")
        for result in results:
            print(f"{result['document_id']}: Complexity Score = {result['composite_complexity_score']:.3f}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)