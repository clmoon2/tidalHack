"""
DTW (Dynamic Time Warping) Alignment Engine for ILI Reference Points.

This module implements the DTW algorithm to align reference point sequences
across inspection runs, accounting for odometer drift up to ±10%.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

import numpy as np
from typing import List, Tuple, Optional
import pandas as pd
from dataclasses import dataclass

from src.data_models.models import ReferencePoint, AlignmentResult


@dataclass
class MatchedPair:
    """A matched pair of reference points from two runs"""
    ref_point1_id: str
    ref_point2_id: str
    distance1: float
    distance2: float
    distance_diff: float


class DTWAligner:
    """
    Dynamic Time Warping aligner for reference point sequences.
    
    Implements DTW with a 10% drift constraint to align reference points
    (girth welds, valves, tees) across inspection runs despite odometer drift.
    
    Algorithm:
    1. Extract odometer sequences from both runs
    2. Compute DTW distance matrix with 10% drift constraint
    3. Find optimal warping path using dynamic programming
    4. Calculate alignment metrics (match_rate, RMSE)
    """
    
    def __init__(self, drift_constraint: float = 0.10):
        """
        Initialize DTW aligner.
        
        Args:
            drift_constraint: Maximum allowed drift as fraction (default 0.10 = 10%)
        """
        self.drift_constraint = drift_constraint
    
    def align_sequences(
        self,
        ref_points1: List[ReferencePoint],
        ref_points2: List[ReferencePoint],
        run1_id: str,
        run2_id: str
    ) -> AlignmentResult:
        """
        Align two reference point sequences using DTW.
        
        Args:
            ref_points1: Reference points from first inspection run
            ref_points2: Reference points from second inspection run
            run1_id: Identifier for first run
            run2_id: Identifier for second run
            
        Returns:
            AlignmentResult with matched points, metrics, and correction parameters
            
        Raises:
            ValueError: If sequences are empty or alignment quality is insufficient
        """
        if not ref_points1 or not ref_points2:
            raise ValueError("Cannot align empty reference point sequences")
        
        # Extract distance sequences
        seq1 = np.array([rp.distance for rp in ref_points1])
        seq2 = np.array([rp.distance for rp in ref_points2])
        
        # Calculate distance matrix with drift constraint
        distance_matrix = self.calculate_distance_matrix(seq1, seq2)
        
        # Find optimal warping path
        path = self.find_optimal_path(distance_matrix, seq1, seq2)
        
        # Build matched pairs
        matched_pairs: List[Tuple[str, str]] = []
        matched_pair_objects: List[MatchedPair] = []
        
        for i, j in path:
            if i < len(ref_points1) and j < len(ref_points2):
                rp1 = ref_points1[i]
                rp2 = ref_points2[j]
                matched_pairs.append((rp1.id, rp2.id))
                matched_pair_objects.append(MatchedPair(
                    ref_point1_id=rp1.id,
                    ref_point2_id=rp2.id,
                    distance1=rp1.distance,
                    distance2=rp2.distance,
                    distance_diff=abs(rp1.distance - rp2.distance)
                ))
        
        # Calculate alignment metrics
        match_rate = self._calculate_match_rate(len(matched_pairs), len(ref_points1), len(ref_points2))
        rmse = self._calculate_rmse(matched_pair_objects)
        
        # Store correction function parameters (for DistanceCorrectionFunction)
        correction_params = {
            'matched_distances_run1': [mp.distance1 for mp in matched_pair_objects],
            'matched_distances_run2': [mp.distance2 for mp in matched_pair_objects],
            'interpolation_method': 'linear'
        }
        
        return AlignmentResult(
            run1_id=run1_id,
            run2_id=run2_id,
            matched_points=matched_pairs,
            match_rate=match_rate,
            rmse=rmse,
            correction_function_params=correction_params
        )
    
    def calculate_distance_matrix(
        self,
        seq1: np.ndarray,
        seq2: np.ndarray
    ) -> np.ndarray:
        """
        Calculate DTW distance matrix with 10% drift constraint.
        
        For each pair (i, j), calculates |distance1[i] - distance2[j]|
        but only if the difference is within the drift constraint window.
        Pairs outside the constraint are set to infinity.
        
        Args:
            seq1: Odometer readings from first run (sorted)
            seq2: Odometer readings from second run (sorted)
            
        Returns:
            Distance matrix of shape (len(seq1), len(seq2))
        """
        n = len(seq1)
        m = len(seq2)
        
        # Initialize distance matrix with infinity
        distance_matrix = np.full((n, m), np.inf)
        
        # Calculate pairwise distances with drift constraint
        for i in range(n):
            for j in range(m):
                # Calculate absolute distance difference
                dist_diff = abs(seq1[i] - seq2[j])
                
                # Check if within drift constraint (10% of the reference distance)
                # Use the average of both distances as reference
                avg_distance = (seq1[i] + seq2[j]) / 2.0
                max_allowed_drift = avg_distance * self.drift_constraint
                
                if dist_diff <= max_allowed_drift:
                    distance_matrix[i, j] = dist_diff
        
        return distance_matrix
    
    def find_optimal_path(
        self,
        distance_matrix: np.ndarray,
        seq1: np.ndarray,
        seq2: np.ndarray
    ) -> List[Tuple[int, int]]:
        """
        Find optimal warping path using dynamic programming.
        
        Uses DTW algorithm with backtracking to find the path that
        minimizes cumulative distance while respecting the drift constraint.
        
        Args:
            distance_matrix: Pairwise distance matrix from calculate_distance_matrix
            seq1: First sequence (for validation)
            seq2: Second sequence (for validation)
            
        Returns:
            List of (i, j) index pairs representing the optimal alignment path
        """
        n, m = distance_matrix.shape
        
        # Initialize cost matrix
        cost = np.full((n + 1, m + 1), np.inf)
        cost[0, 0] = 0.0
        
        # Fill cost matrix using dynamic programming
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                # Get distance for this cell (i-1, j-1 in distance_matrix)
                dist = distance_matrix[i - 1, j - 1]
                
                # Only proceed if this pair is within drift constraint
                if not np.isinf(dist):
                    # Find minimum cost from three possible predecessors
                    min_cost = min(
                        cost[i - 1, j],      # insertion (skip point in seq1)
                        cost[i, j - 1],      # deletion (skip point in seq2)
                        cost[i - 1, j - 1]   # match
                    )
                    cost[i, j] = dist + min_cost
        
        # Backtrack to find optimal path
        path = self._backtrack_path(cost, distance_matrix)
        
        return path
    
    def _backtrack_path(
        self,
        cost: np.ndarray,
        distance_matrix: np.ndarray
    ) -> List[Tuple[int, int]]:
        """
        Backtrack through cost matrix to find optimal alignment path.
        
        Args:
            cost: Filled cost matrix from dynamic programming
            distance_matrix: Original distance matrix
            
        Returns:
            List of (i, j) index pairs in forward order
        """
        path = []
        i = cost.shape[0] - 1
        j = cost.shape[1] - 1
        
        # Start from bottom-right and work backwards
        while i > 0 and j > 0:
            # Add current position to path (convert from cost indices to distance_matrix indices)
            path.append((i - 1, j - 1))
            
            # Find which predecessor had minimum cost
            candidates = [
                (i - 1, j - 1, cost[i - 1, j - 1]),  # match
                (i - 1, j, cost[i - 1, j]),          # insertion
                (i, j - 1, cost[i, j - 1])           # deletion
            ]
            
            # Choose the predecessor with minimum cost
            min_candidate = min(candidates, key=lambda x: x[2])
            i, j = min_candidate[0], min_candidate[1]
        
        # Reverse path to get forward order
        path.reverse()
        
        return path
    
    def _calculate_match_rate(
        self,
        num_matched: int,
        len_seq1: int,
        len_seq2: int
    ) -> float:
        """
        Calculate match rate as percentage of reference points matched.
        
        Match rate = (matched points / max(seq1, seq2)) * 100
        This ensures the match rate never exceeds 100%.
        
        Args:
            num_matched: Number of matched pairs
            len_seq1: Length of first sequence
            len_seq2: Length of second sequence
            
        Returns:
            Match rate as percentage (0-100)
        """
        max_length = max(len_seq1, len_seq2)
        if max_length == 0:
            return 0.0
        
        match_rate = (num_matched / max_length) * 100.0
        return min(match_rate, 100.0)  # Cap at 100%
    
    def _calculate_rmse(self, matched_pairs: List[MatchedPair]) -> float:
        """
        Calculate Root Mean Square Error for matched reference points.
        
        RMSE = sqrt(mean((distance1 - distance2)²))
        
        Args:
            matched_pairs: List of matched reference point pairs
            
        Returns:
            RMSE in feet
        """
        if not matched_pairs:
            return 0.0
        
        squared_errors = [mp.distance_diff ** 2 for mp in matched_pairs]
        mean_squared_error = np.mean(squared_errors)
        rmse = np.sqrt(mean_squared_error)
        
        return float(rmse)


def align_reference_points(
    ref_points1: List[ReferencePoint],
    ref_points2: List[ReferencePoint],
    run1_id: str,
    run2_id: str,
    drift_constraint: float = 0.10
) -> AlignmentResult:
    """
    Convenience function to align reference points using DTW.
    
    Args:
        ref_points1: Reference points from first inspection run
        ref_points2: Reference points from second inspection run
        run1_id: Identifier for first run
        run2_id: Identifier for second run
        drift_constraint: Maximum allowed drift as fraction (default 0.10)
        
    Returns:
        AlignmentResult with matched points and metrics
    """
    aligner = DTWAligner(drift_constraint=drift_constraint)
    return aligner.align_sequences(ref_points1, ref_points2, run1_id, run2_id)
