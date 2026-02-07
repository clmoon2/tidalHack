"""
Distance Correction Function for ILI Data Alignment.

This module implements piecewise linear interpolation to transform anomaly
distances between coordinate systems based on matched reference points from DTW alignment.

Requirements: 2.6
"""

import numpy as np
from scipy.interpolate import interp1d
from typing import List, Union, Optional
import pandas as pd


class DistanceCorrectionFunction:
    """
    Piecewise linear interpolation function for distance correction.
    
    Uses matched reference point pairs from DTW alignment to build an
    interpolation function that transforms distances from one inspection
    run's coordinate system to another's.
    
    Algorithm:
    1. Build interpolation function: distance_run2 = f(distance_run1)
    2. Use scipy.interpolate.interp1d with linear method
    3. Handle extrapolation for anomalies outside reference point range
    
    Example:
        >>> correction_params = {
        ...     'matched_distances_run1': [100.0, 200.0, 300.0],
        ...     'matched_distances_run2': [102.0, 205.0, 297.0],
        ...     'interpolation_method': 'linear'
        ... }
        >>> corrector = DistanceCorrectionFunction(correction_params)
        >>> corrected = corrector.correct_distance(150.0)
        >>> print(corrected)  # ~153.5
    """
    
    def __init__(self, correction_function_params: dict):
        """
        Initialize distance correction function from DTW alignment results.
        
        Args:
            correction_function_params: Dictionary containing:
                - matched_distances_run1: List of distances from source run
                - matched_distances_run2: List of distances from target run
                - interpolation_method: Method for interpolation (default 'linear')
                
        Raises:
            ValueError: If parameters are invalid or insufficient data points
        """
        # Extract parameters
        self.distances_run1 = np.array(
            correction_function_params.get('matched_distances_run1', [])
        )
        self.distances_run2 = np.array(
            correction_function_params.get('matched_distances_run2', [])
        )
        self.method = correction_function_params.get('interpolation_method', 'linear')
        
        # Validate inputs
        if len(self.distances_run1) == 0 or len(self.distances_run2) == 0:
            raise ValueError("Cannot create correction function with empty distance arrays")
        
        if len(self.distances_run1) != len(self.distances_run2):
            raise ValueError(
                f"Distance arrays must have same length: "
                f"run1={len(self.distances_run1)}, run2={len(self.distances_run2)}"
            )
        
        if len(self.distances_run1) < 2:
            raise ValueError(
                f"Need at least 2 matched points for interpolation, got {len(self.distances_run1)}"
            )
        
        # Store bounds for extrapolation handling
        self.min_distance_run1 = float(np.min(self.distances_run1))
        self.max_distance_run1 = float(np.max(self.distances_run1))
        
        # Build interpolation function
        # fill_value='extrapolate' allows extrapolation beyond the data range
        # bounds_error=False prevents errors when extrapolating
        self._interpolator = interp1d(
            self.distances_run1,
            self.distances_run2,
            kind=self.method,
            fill_value='extrapolate',
            bounds_error=False,
            assume_sorted=False  # Don't assume sorted, let scipy handle it
        )
    
    def correct_distance(
        self,
        source_distance: Union[float, np.ndarray, List[float]]
    ) -> Union[float, np.ndarray]:
        """
        Transform distance from source run coordinate system to target run.
        
        Uses piecewise linear interpolation for distances within the reference
        point range, and linear extrapolation for distances outside the range.
        
        Args:
            source_distance: Distance(s) in source run coordinate system.
                Can be a single float, numpy array, or list of floats.
                
        Returns:
            Corrected distance(s) in target run coordinate system.
            Returns same type as input (float or numpy array).
            
        Examples:
            >>> corrector.correct_distance(150.0)
            153.5
            >>> corrector.correct_distance([100.0, 150.0, 200.0])
            array([102.0, 153.5, 205.0])
        """
        # Handle different input types
        is_scalar = np.isscalar(source_distance)
        
        if is_scalar:
            distances = np.array([source_distance])
        else:
            distances = np.array(source_distance)
        
        # Apply interpolation/extrapolation
        corrected = self._interpolator(distances)
        
        # Return same type as input
        if is_scalar:
            return float(corrected[0])
        else:
            return corrected
    
    def correct_anomaly_distances(
        self,
        anomalies_df: pd.DataFrame,
        distance_column: str = 'distance',
        corrected_column: str = 'corrected_distance'
    ) -> pd.DataFrame:
        """
        Apply distance correction to all anomalies in a DataFrame.
        
        Creates a new column with corrected distances while preserving
        the original distance column.
        
        Args:
            anomalies_df: DataFrame containing anomaly records
            distance_column: Name of column containing source distances
            corrected_column: Name of column to create for corrected distances
            
        Returns:
            DataFrame with added corrected_distance column
            
        Raises:
            ValueError: If distance_column doesn't exist in DataFrame
        """
        if distance_column not in anomalies_df.columns:
            raise ValueError(
                f"Distance column '{distance_column}' not found in DataFrame. "
                f"Available columns: {list(anomalies_df.columns)}"
            )
        
        # Create a copy to avoid modifying original
        result_df = anomalies_df.copy()
        
        # Handle empty DataFrame
        if len(result_df) == 0:
            result_df[corrected_column] = pd.Series(dtype=float)
            return result_df
        
        # Apply correction to all distances at once (vectorized)
        result_df[corrected_column] = self.correct_distance(
            result_df[distance_column].values
        )
        
        return result_df
    
    def get_correction_info(self) -> dict:
        """
        Get information about the correction function.
        
        Returns:
            Dictionary containing:
                - num_reference_points: Number of matched reference points
                - distance_range_run1: (min, max) distance range in source run
                - distance_range_run2: (min, max) distance range in target run
                - interpolation_method: Method used for interpolation
                - max_correction: Maximum absolute correction applied
                - mean_correction: Mean correction across reference points
        """
        corrections = self.distances_run2 - self.distances_run1
        
        return {
            'num_reference_points': len(self.distances_run1),
            'distance_range_run1': (
                float(self.min_distance_run1),
                float(self.max_distance_run1)
            ),
            'distance_range_run2': (
                float(np.min(self.distances_run2)),
                float(np.max(self.distances_run2))
            ),
            'interpolation_method': self.method,
            'max_correction': float(np.max(np.abs(corrections))),
            'mean_correction': float(np.mean(corrections)),
            'std_correction': float(np.std(corrections))
        }
    
    def is_extrapolating(self, distance: float) -> bool:
        """
        Check if a given distance requires extrapolation.
        
        Args:
            distance: Distance to check
            
        Returns:
            True if distance is outside the reference point range
        """
        return distance < self.min_distance_run1 or distance > self.max_distance_run1


def create_correction_function(
    alignment_result
) -> DistanceCorrectionFunction:
    """
    Convenience function to create correction function from AlignmentResult.
    
    Args:
        alignment_result: AlignmentResult object from DTWAligner
        
    Returns:
        DistanceCorrectionFunction ready to use
        
    Example:
        >>> from src.alignment.dtw_aligner import align_reference_points
        >>> alignment = align_reference_points(ref_points1, ref_points2, 'run1', 'run2')
        >>> corrector = create_correction_function(alignment)
        >>> corrected_df = corrector.correct_anomaly_distances(anomalies_df)
    """
    return DistanceCorrectionFunction(alignment_result.correction_function_params)
