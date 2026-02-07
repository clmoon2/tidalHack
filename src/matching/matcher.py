"""
Hungarian algorithm-based anomaly matching.

This module implements optimal anomaly matching using the Hungarian algorithm
(linear sum assignment) with similarity-based cost matrices.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Tuple, Optional
from enum import Enum

from src.data_models.models import AnomalyRecord, Match
from src.matching.similarity import SimilarityCalculator


class MatchConfidence(str, Enum):
    """Match confidence levels based on similarity scores."""
    HIGH = "HIGH"      # >= 0.8
    MEDIUM = "MEDIUM"  # >= 0.6
    LOW = "LOW"        # < 0.6


class UnmatchedClassification(str, Enum):
    """Classification for unmatched anomalies."""
    NEW = "new"                          # Anomaly in newer run, not in older run
    REPAIRED_OR_REMOVED = "repaired_or_removed"  # Anomaly in older run, not in newer run


class HungarianMatcher:
    """
    Optimal anomaly matching using Hungarian algorithm.
    
    Uses scipy's linear_sum_assignment to find optimal one-to-one matching
    between anomalies from two inspection runs. Filters low-confidence matches
    and classifies unmatched anomalies.
    """
    
    def __init__(
        self,
        similarity_calculator: Optional[SimilarityCalculator] = None,
        confidence_threshold: float = 0.6,
        use_corrected_distance: bool = True
    ):
        """
        Initialize Hungarian matcher.
        
        Args:
            similarity_calculator: Calculator for similarity scores (creates default if None)
            confidence_threshold: Minimum similarity for valid match (default 0.6)
            use_corrected_distance: Whether to use corrected distances in similarity calculation
        """
        self.similarity_calculator = similarity_calculator or SimilarityCalculator()
        self.confidence_threshold = confidence_threshold
        self.use_corrected_distance = use_corrected_distance
    
    def create_cost_matrix(
        self,
        anomalies_run1: List[AnomalyRecord],
        anomalies_run2: List[AnomalyRecord]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create cost matrix for Hungarian algorithm.
        
        Cost is defined as (1 - similarity) so that minimizing cost
        maximizes similarity. Also returns the similarity matrix for
        confidence scoring.
        
        Args:
            anomalies_run1: Anomalies from first (older) inspection run
            anomalies_run2: Anomalies from second (newer) inspection run
        
        Returns:
            Tuple of (cost_matrix, similarity_matrix) both as numpy arrays
            Shape: (len(anomalies_run1), len(anomalies_run2))
        """
        n1 = len(anomalies_run1)
        n2 = len(anomalies_run2)
        
        # Initialize matrices
        similarity_matrix = np.zeros((n1, n2))
        
        # Calculate similarity for each pair
        for i, anom1 in enumerate(anomalies_run1):
            for j, anom2 in enumerate(anomalies_run2):
                sim_result = self.similarity_calculator.calculate_similarity(
                    anom1, anom2,
                    use_corrected_distance=self.use_corrected_distance
                )
                similarity_matrix[i, j] = sim_result['overall']
        
        # Convert similarity to cost (cost = 1 - similarity)
        cost_matrix = 1.0 - similarity_matrix
        
        return cost_matrix, similarity_matrix
    
    def solve_assignment(
        self,
        cost_matrix: np.ndarray,
        similarity_matrix: np.ndarray
    ) -> Tuple[List[Tuple[int, int]], List[float]]:
        """
        Solve optimal assignment problem using Hungarian algorithm.
        
        Args:
            cost_matrix: Cost matrix (1 - similarity)
            similarity_matrix: Similarity matrix for confidence scoring
        
        Returns:
            Tuple of (assignments, confidences)
            - assignments: List of (run1_idx, run2_idx) tuples
            - confidences: List of similarity scores for each assignment
        """
        # Solve using scipy's linear_sum_assignment
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        # Extract assignments and confidences
        assignments = []
        confidences = []
        
        for i, j in zip(row_indices, col_indices):
            assignments.append((int(i), int(j)))
            confidences.append(float(similarity_matrix[i, j]))
        
        return assignments, confidences
    
    def filter_low_confidence(
        self,
        assignments: List[Tuple[int, int]],
        confidences: List[float]
    ) -> Tuple[List[Tuple[int, int]], List[float]]:
        """
        Filter out matches below confidence threshold.
        
        Args:
            assignments: List of (run1_idx, run2_idx) tuples
            confidences: List of similarity scores
        
        Returns:
            Tuple of (filtered_assignments, filtered_confidences)
        """
        filtered_assignments = []
        filtered_confidences = []
        
        for assignment, confidence in zip(assignments, confidences):
            if confidence >= self.confidence_threshold:
                filtered_assignments.append(assignment)
                filtered_confidences.append(confidence)
        
        return filtered_assignments, filtered_confidences
    
    def classify_confidence_level(self, confidence: float) -> MatchConfidence:
        """
        Classify match confidence level.
        
        Args:
            confidence: Similarity score [0, 1]
        
        Returns:
            MatchConfidence enum (HIGH, MEDIUM, or LOW)
        """
        if confidence >= 0.8:
            return MatchConfidence.HIGH
        elif confidence >= 0.6:
            return MatchConfidence.MEDIUM
        else:
            return MatchConfidence.LOW
    
    def classify_unmatched(
        self,
        anomalies_run1: List[AnomalyRecord],
        anomalies_run2: List[AnomalyRecord],
        matched_indices_run1: set,
        matched_indices_run2: set
    ) -> Dict[str, List[AnomalyRecord]]:
        """
        Classify unmatched anomalies.
        
        Args:
            anomalies_run1: Anomalies from first (older) run
            anomalies_run2: Anomalies from second (newer) run
            matched_indices_run1: Set of matched indices from run1
            matched_indices_run2: Set of matched indices from run2
        
        Returns:
            Dictionary with keys:
                - 'new': Anomalies in run2 not matched (new anomalies)
                - 'repaired_or_removed': Anomalies in run1 not matched
        """
        # Find unmatched anomalies
        unmatched_run1 = [
            anom for i, anom in enumerate(anomalies_run1)
            if i not in matched_indices_run1
        ]
        
        unmatched_run2 = [
            anom for i, anom in enumerate(anomalies_run2)
            if i not in matched_indices_run2
        ]
        
        return {
            'new': unmatched_run2,
            'repaired_or_removed': unmatched_run1
        }
    
    def match_anomalies(
        self,
        anomalies_run1: List[AnomalyRecord],
        anomalies_run2: List[AnomalyRecord],
        run1_id: str,
        run2_id: str
    ) -> Dict[str, any]:
        """
        Perform complete anomaly matching workflow.
        
        Steps:
        1. Create cost matrix from similarity scores
        2. Solve optimal assignment using Hungarian algorithm
        3. Filter matches below confidence threshold
        4. Classify confidence levels
        5. Classify unmatched anomalies
        
        Args:
            anomalies_run1: Anomalies from first (older) inspection run
            anomalies_run2: Anomalies from second (newer) inspection run
            run1_id: Identifier for first run
            run2_id: Identifier for second run
        
        Returns:
            Dictionary containing:
                - 'matches': List of Match objects
                - 'unmatched': Dict with 'new' and 'repaired_or_removed' lists
                - 'statistics': Dict with matching statistics
        """
        # Handle empty inputs
        if not anomalies_run1 or not anomalies_run2:
            return {
                'matches': [],
                'unmatched': {
                    'new': anomalies_run2 if anomalies_run2 else [],
                    'repaired_or_removed': anomalies_run1 if anomalies_run1 else []
                },
                'statistics': {
                    'total_run1': len(anomalies_run1),
                    'total_run2': len(anomalies_run2),
                    'matched': 0,
                    'unmatched_run1': len(anomalies_run1),
                    'unmatched_run2': len(anomalies_run2),
                    'match_rate': 0.0,
                    'high_confidence': 0,
                    'medium_confidence': 0,
                    'low_confidence': 0
                }
            }
        
        # Step 1: Create cost matrix
        cost_matrix, similarity_matrix = self.create_cost_matrix(
            anomalies_run1, anomalies_run2
        )
        
        # Step 2: Solve assignment
        assignments, confidences = self.solve_assignment(
            cost_matrix, similarity_matrix
        )
        
        # Step 3: Filter low confidence
        filtered_assignments, filtered_confidences = self.filter_low_confidence(
            assignments, confidences
        )
        
        # Step 4: Create Match objects with confidence levels
        matches = []
        matched_indices_run1 = set()
        matched_indices_run2 = set()
        
        confidence_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for (i, j), confidence in zip(filtered_assignments, filtered_confidences):
            anom1 = anomalies_run1[i]
            anom2 = anomalies_run2[j]
            
            # Classify confidence level
            confidence_level = self.classify_confidence_level(confidence)
            confidence_counts[confidence_level.value] += 1
            
            # Get similarity components for the match
            sim_result = self.similarity_calculator.calculate_similarity(
                anom1, anom2, use_corrected_distance=self.use_corrected_distance
            )
            
            # Create Match object
            match = Match(
                id=f"{anom1.id}_{anom2.id}",
                anomaly1_id=anom1.id,
                anomaly2_id=anom2.id,
                similarity_score=confidence,
                confidence=confidence_level.value,
                distance_similarity=sim_result['distance'],
                clock_similarity=sim_result['clock'],
                type_similarity=sim_result['type'],
                depth_similarity=sim_result['depth'],
                length_similarity=sim_result['length'],
                width_similarity=sim_result['width']
            )
            
            matches.append(match)
            matched_indices_run1.add(i)
            matched_indices_run2.add(j)
        
        # Step 5: Classify unmatched anomalies
        unmatched = self.classify_unmatched(
            anomalies_run1, anomalies_run2,
            matched_indices_run1, matched_indices_run2
        )
        
        # Calculate statistics
        total_run1 = len(anomalies_run1)
        total_run2 = len(anomalies_run2)
        matched_count = len(matches)
        
        # Match rate based on smaller set (conservative estimate)
        match_rate = matched_count / min(total_run1, total_run2) if min(total_run1, total_run2) > 0 else 0.0
        
        statistics = {
            'total_run1': total_run1,
            'total_run2': total_run2,
            'matched': matched_count,
            'unmatched_run1': len(unmatched['repaired_or_removed']),
            'unmatched_run2': len(unmatched['new']),
            'match_rate': match_rate,
            'high_confidence': confidence_counts['HIGH'],
            'medium_confidence': confidence_counts['MEDIUM'],
            'low_confidence': confidence_counts['LOW']
        }
        
        return {
            'matches': matches,
            'unmatched': unmatched,
            'statistics': statistics
        }

