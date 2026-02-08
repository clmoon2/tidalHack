"""
Feature engineering for ML growth prediction.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from src.data_models.models import AnomalyRecord, ReferencePoint


class FeatureEngineer:
    """
    Extracts and engineers features for ML growth prediction.
    
    Features include:
    - Current dimensions (depth, length, width)
    - Historical growth rates
    - Distance from reference points
    - Clock position
    - Feature type (one-hot encoded)
    - Derived ratios (length/width, depth/length)
    """
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_columns: List[str] = []
        self.categorical_mappings: Dict[str, Dict[str, int]] = {}
    
    def extract_features(
        self,
        anomalies: List[AnomalyRecord],
        reference_points: List[ReferencePoint],
        growth_rates: Dict[str, float] = None
    ) -> pd.DataFrame:
        """
        Extract features from anomalies.
        
        Args:
            anomalies: List of anomaly records
            reference_points: List of reference points for distance calculation
            growth_rates: Optional dict of anomaly_id -> growth_rate
        
        Returns:
            DataFrame with engineered features
        """
        features = []
        
        for anomaly in anomalies:
            feature_dict = self._extract_anomaly_features(
                anomaly, reference_points, growth_rates
            )
            features.append(feature_dict)
        
        df = pd.DataFrame(features)
        
        # One-hot encode categorical features
        df = self._encode_categorical(df)
        
        # Store feature columns for later use
        self.feature_columns = [col for col in df.columns if col != 'anomaly_id']
        
        return df
    
    def _extract_anomaly_features(
        self,
        anomaly: AnomalyRecord,
        reference_points: List[ReferencePoint],
        growth_rates: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Extract features for a single anomaly."""
        features = {
            'anomaly_id': anomaly.id,
            
            # Current dimensions
            'depth_pct': anomaly.depth_pct,
            'length_in': anomaly.length_in,
            'width_in': anomaly.width_in,
            
            # Clock position
            'clock_position': anomaly.clock_position,
            
            # Feature type
            'feature_type': anomaly.feature_type,
            
            # Distance from nearest reference point
            'dist_to_nearest_ref': self._calculate_nearest_ref_distance(
                anomaly, reference_points
            ),
            
            # Derived ratios
            'length_width_ratio': (
                anomaly.length_in / anomaly.width_in 
                if anomaly.width_in > 0 else 0
            ),
            'depth_length_ratio': (
                anomaly.depth_pct / anomaly.length_in 
                if anomaly.length_in > 0 else 0
            ),
        }
        
        # Add historical growth rate if available
        if growth_rates and anomaly.id in growth_rates:
            features['historical_growth_rate'] = growth_rates[anomaly.id]
        else:
            features['historical_growth_rate'] = 0.0
        
        return features
    
    def _calculate_nearest_ref_distance(
        self,
        anomaly: AnomalyRecord,
        reference_points: List[ReferencePoint]
    ) -> float:
        """Calculate distance to nearest reference point."""
        if not reference_points:
            return 999.0  # Large default value
        
        distances = [
            abs(anomaly.corrected_distance - ref.corrected_distance)
            for ref in reference_points
        ]
        
        return min(distances)
    
    def _encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """One-hot encode categorical features."""
        # Feature type encoding
        if 'feature_type' in df.columns:
            feature_type_dummies = pd.get_dummies(
                df['feature_type'], 
                prefix='feature_type'
            )
            df = pd.concat([df, feature_type_dummies], axis=1)
            df = df.drop('feature_type', axis=1)
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature column names."""
        return self.feature_columns

