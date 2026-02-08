"""
Alignment Validation Module
============================

Validates DTW alignment quality against requirements:
- Match rate >= 95%
- RMSE <= 10 feet
- Flags unmatched reference points with diagnostics

Author: ILI Data Alignment System
Date: 2024
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np


class AlignmentValidator:
    """
    Validates alignment quality and flags issues.
    
    Requirements:
    - Match rate >= 95% (Requirement 2.3)
    - RMSE <= 10 feet (Requirement 2.4)
    - Flag unmatched reference points (Requirement 2.5)
    """
    
    def __init__(
        self,
        min_match_rate: float = 0.95,
        max_rmse: float = 10.0
    ):
        """
        Initialize validator with thresholds.
        
        Args:
            min_match_rate: Minimum acceptable match rate (default: 0.95)
            max_rmse: Maximum acceptable RMSE in feet (default: 10.0)
        """
        self.min_match_rate = min_match_rate
        self.max_rmse = max_rmse
    
    def validate_alignment(
        self,
        alignment_result: Dict[str, Any],
        ref_points_run1: pd.DataFrame,
        ref_points_run2: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Validate alignment quality against requirements.
        
        Args:
            alignment_result: Result from DTWAligner.align()
            ref_points_run1: Reference points from first run
            ref_points_run2: Reference points from second run
        
        Returns:
            Dictionary with validation results:
            {
                'is_valid': bool,
                'match_rate': float,
                'match_rate_passed': bool,
                'rmse': float,
                'rmse_passed': bool,
                'unmatched_run1': List[Dict],
                'unmatched_run2': List[Dict],
                'warnings': List[str],
                'diagnostics': Dict
            }
        """
        # Extract metrics
        match_rate = alignment_result.get('match_rate', 0.0)
        rmse = alignment_result.get('rmse', float('inf'))
        aligned_pairs = alignment_result.get('aligned_pairs', [])
        
        # Check thresholds
        match_rate_passed = match_rate >= self.min_match_rate
        rmse_passed = rmse <= self.max_rmse
        is_valid = match_rate_passed and rmse_passed
        
        # Find unmatched reference points
        unmatched_run1 = self._find_unmatched_points(
            ref_points_run1, aligned_pairs, run_index=0
        )
        unmatched_run2 = self._find_unmatched_points(
            ref_points_run2, aligned_pairs, run_index=1
        )
        
        # Generate warnings
        warnings = []
        if not match_rate_passed:
            warnings.append(
                f"Match rate {match_rate:.1%} is below threshold {self.min_match_rate:.1%}"
            )
        if not rmse_passed:
            warnings.append(
                f"RMSE {rmse:.2f} ft exceeds threshold {self.max_rmse:.2f} ft"
            )
        if unmatched_run1:
            warnings.append(
                f"{len(unmatched_run1)} reference points unmatched in Run 1"
            )
        if unmatched_run2:
            warnings.append(
                f"{len(unmatched_run2)} reference points unmatched in Run 2"
            )
        
        # Generate diagnostics
        diagnostics = self._generate_diagnostics(
            alignment_result, unmatched_run1, unmatched_run2
        )
        
        return {
            'is_valid': is_valid,
            'match_rate': match_rate,
            'match_rate_passed': match_rate_passed,
            'match_rate_threshold': self.min_match_rate,
            'rmse': rmse,
            'rmse_passed': rmse_passed,
            'rmse_threshold': self.max_rmse,
            'unmatched_run1': unmatched_run1,
            'unmatched_run2': unmatched_run2,
            'warnings': warnings,
            'diagnostics': diagnostics
        }
    
    def _find_unmatched_points(
        self,
        ref_points: pd.DataFrame,
        aligned_pairs: List[tuple],
        run_index: int
    ) -> List[Dict[str, Any]]:
        """
        Find reference points that were not matched.
        
        Args:
            ref_points: Reference points DataFrame
            aligned_pairs: List of (idx1, idx2) tuples
            run_index: 0 for run1, 1 for run2
        
        Returns:
            List of unmatched points with diagnostics
        """
        if len(ref_points) == 0:
            return []
        
        # Get matched indices
        matched_indices = set()
        for pair in aligned_pairs:
            matched_indices.add(pair[run_index])
        
        # Find unmatched
        unmatched = []
        for idx, row in ref_points.iterrows():
            if idx not in matched_indices:
                unmatched.append({
                    'index': idx,
                    'distance_ft': float(row['distance_ft']),
                    'feature_type': row.get('feature_type', 'reference'),
                    'reason': self._diagnose_unmatch(idx, ref_points, aligned_pairs, run_index)
                })
        
        return unmatched
    
    def _diagnose_unmatch(
        self,
        idx: int,
        ref_points: pd.DataFrame,
        aligned_pairs: List[tuple],
        run_index: int
    ) -> str:
        """
        Diagnose why a reference point was not matched.
        
        Args:
            idx: Index of unmatched point
            ref_points: Reference points DataFrame
            aligned_pairs: List of aligned pairs
            run_index: 0 for run1, 1 for run2
        
        Returns:
            Diagnostic message
        """
        if len(aligned_pairs) == 0:
            return "No alignment pairs found"
        
        point_dist = ref_points.loc[idx, 'distance_ft']
        
        # Check if at beginning or end
        if idx == 0:
            return "Point at beginning of run - may be outside alignment window"
        if idx == len(ref_points) - 1:
            return "Point at end of run - may be outside alignment window"
        
        # Check if isolated (far from other points)
        distances = ref_points['distance_ft'].values
        if idx > 0 and idx < len(distances) - 1:
            gap_before = abs(distances[idx] - distances[idx - 1])
            gap_after = abs(distances[idx + 1] - distances[idx])
            if gap_before > 100 or gap_after > 100:
                return f"Isolated point (gaps: {gap_before:.1f}ft before, {gap_after:.1f}ft after)"
        
        # Check if near matched points
        nearest_matched_dist = float('inf')
        for pair in aligned_pairs:
            matched_idx = pair[run_index]
            if matched_idx in ref_points.index:
                matched_dist = ref_points.loc[matched_idx, 'distance_ft']
                dist_diff = abs(point_dist - matched_dist)
                nearest_matched_dist = min(nearest_matched_dist, dist_diff)
        
        if nearest_matched_dist < 20:
            return f"Close to matched point ({nearest_matched_dist:.1f}ft) but not selected by DTW"
        
        return "Could not be aligned - possible data quality issue"
    
    def _generate_diagnostics(
        self,
        alignment_result: Dict[str, Any],
        unmatched_run1: List[Dict],
        unmatched_run2: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate detailed diagnostics for alignment.
        
        Args:
            alignment_result: Alignment result dictionary
            unmatched_run1: Unmatched points from run 1
            unmatched_run2: Unmatched points from run 2
        
        Returns:
            Diagnostics dictionary
        """
        aligned_pairs = alignment_result.get('aligned_pairs', [])
        
        # Calculate alignment statistics
        if len(aligned_pairs) > 0:
            distances = [pair[2] for pair in aligned_pairs if len(pair) > 2]
            if distances:
                avg_distance_error = np.mean(distances)
                max_distance_error = np.max(distances)
                std_distance_error = np.std(distances)
            else:
                avg_distance_error = 0.0
                max_distance_error = 0.0
                std_distance_error = 0.0
        else:
            avg_distance_error = 0.0
            max_distance_error = 0.0
            std_distance_error = 0.0
        
        # Categorize unmatched points
        unmatched_categories = {
            'boundary_points': 0,
            'isolated_points': 0,
            'data_quality_issues': 0,
            'other': 0
        }
        
        for point in unmatched_run1 + unmatched_run2:
            reason = point['reason']
            if 'beginning' in reason or 'end' in reason:
                unmatched_categories['boundary_points'] += 1
            elif 'Isolated' in reason:
                unmatched_categories['isolated_points'] += 1
            elif 'data quality' in reason:
                unmatched_categories['data_quality_issues'] += 1
            else:
                unmatched_categories['other'] += 1
        
        return {
            'total_aligned_pairs': len(aligned_pairs),
            'avg_distance_error': float(avg_distance_error),
            'max_distance_error': float(max_distance_error),
            'std_distance_error': float(std_distance_error),
            'total_unmatched': len(unmatched_run1) + len(unmatched_run2),
            'unmatched_run1_count': len(unmatched_run1),
            'unmatched_run2_count': len(unmatched_run2),
            'unmatched_categories': unmatched_categories,
            'dtw_distance': alignment_result.get('dtw_distance', 0.0)
        }
    
    def generate_report(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate human-readable validation report.
        
        Args:
            validation_result: Result from validate_alignment()
        
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ALIGNMENT VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall status
        status = "✅ PASSED" if validation_result['is_valid'] else "❌ FAILED"
        lines.append(f"Overall Status: {status}")
        lines.append("")
        
        # Match rate
        match_rate = validation_result['match_rate']
        match_rate_threshold = validation_result['match_rate_threshold']
        match_status = "✅" if validation_result['match_rate_passed'] else "❌"
        lines.append(f"Match Rate: {match_status} {match_rate:.1%} (threshold: {match_rate_threshold:.1%})")
        
        # RMSE
        rmse = validation_result['rmse']
        rmse_threshold = validation_result['rmse_threshold']
        rmse_status = "✅" if validation_result['rmse_passed'] else "❌"
        lines.append(f"RMSE: {rmse_status} {rmse:.2f} ft (threshold: {rmse_threshold:.2f} ft)")
        lines.append("")
        
        # Diagnostics
        diag = validation_result['diagnostics']
        lines.append("Alignment Statistics:")
        lines.append(f"  Total aligned pairs: {diag['total_aligned_pairs']}")
        lines.append(f"  Average distance error: {diag['avg_distance_error']:.2f} ft")
        lines.append(f"  Max distance error: {diag['max_distance_error']:.2f} ft")
        lines.append(f"  Std dev distance error: {diag['std_distance_error']:.2f} ft")
        lines.append(f"  DTW distance: {diag['dtw_distance']:.2f}")
        lines.append("")
        
        # Unmatched points
        if diag['total_unmatched'] > 0:
            lines.append(f"Unmatched Reference Points: {diag['total_unmatched']}")
            lines.append(f"  Run 1: {diag['unmatched_run1_count']}")
            lines.append(f"  Run 2: {diag['unmatched_run2_count']}")
            lines.append("")
            
            lines.append("Unmatched Categories:")
            for category, count in diag['unmatched_categories'].items():
                if count > 0:
                    lines.append(f"  {category.replace('_', ' ').title()}: {count}")
            lines.append("")
        
        # Warnings
        if validation_result['warnings']:
            lines.append("⚠️  Warnings:")
            for warning in validation_result['warnings']:
                lines.append(f"  - {warning}")
            lines.append("")
        
        # Unmatched point details
        if validation_result['unmatched_run1']:
            lines.append("Unmatched Points in Run 1:")
            for point in validation_result['unmatched_run1'][:5]:  # Show first 5
                lines.append(f"  Distance {point['distance_ft']:.1f} ft: {point['reason']}")
            if len(validation_result['unmatched_run1']) > 5:
                lines.append(f"  ... and {len(validation_result['unmatched_run1']) - 5} more")
            lines.append("")
        
        if validation_result['unmatched_run2']:
            lines.append("Unmatched Points in Run 2:")
            for point in validation_result['unmatched_run2'][:5]:  # Show first 5
                lines.append(f"  Distance {point['distance_ft']:.1f} ft: {point['reason']}")
            if len(validation_result['unmatched_run2']) > 5:
                lines.append(f"  ... and {len(validation_result['unmatched_run2']) - 5} more")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
