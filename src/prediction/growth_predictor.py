"""
XGBoost-based growth prediction with SHAP explanations.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


class GrowthPredictor:
    """
    Predicts future anomaly growth using XGBoost.
    
    Features:
    - XGBoost regression model
    - Early stopping
    - SHAP explanations
    - Confidence intervals
    - Ensemble with linear baseline
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        random_state: int = 42
    ):
        """
        Initialize growth predictor.
        
        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            random_state: Random seed for reproducibility
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        
        self.model: Optional[xgb.XGBRegressor] = None
        self.explainer: Optional[shap.TreeExplainer] = None
        self.feature_names: List[str] = []
        self.metrics: Dict[str, float] = {}
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train XGBoost model with early stopping.
        
        Args:
            X: Feature matrix
            y: Target variable (growth rates)
            test_size: Fraction of data for testing
        
        Returns:
            Dictionary of evaluation metrics
        """
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )
        
        # Initialize model
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            early_stopping_rounds=10,
            eval_metric='rmse'
        )
        
        # Train with early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        # Calculate metrics
        y_pred = self.model.predict(X_test)
        self.metrics = {
            'r2': r2_score(y_test, y_pred),
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'n_train': len(X_train),
            'n_test': len(X_test)
        }
        
        # Initialize SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        return self.metrics
    
    def predict(
        self,
        X: pd.DataFrame,
        ensemble_weight: float = 0.7
    ) -> pd.DataFrame:
        """
        Predict growth rates with ensemble approach.
        
        Args:
            X: Feature matrix
            ensemble_weight: Weight for ML prediction (0.7 = 70% ML, 30% linear)
        
        Returns:
            DataFrame with predictions and confidence intervals
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # ML prediction
        ml_pred = self.model.predict(X)
        
        # Linear baseline (use historical growth rate if available)
        if 'historical_growth_rate' in X.columns:
            linear_pred = X['historical_growth_rate'].values
        else:
            linear_pred = np.zeros(len(X))
        
        # Ensemble prediction
        ensemble_pred = ensemble_weight * ml_pred + (1 - ensemble_weight) * linear_pred
        
        # Calculate confidence intervals (simple approach using prediction variance)
        pred_std = np.std(ml_pred - linear_pred)
        lower_bound = ensemble_pred - 1.96 * pred_std
        upper_bound = ensemble_pred + 1.96 * pred_std
        
        # Create results DataFrame
        results = pd.DataFrame({
            'predicted_growth_rate': ensemble_pred,
            'ml_prediction': ml_pred,
            'linear_baseline': linear_pred,
            'lower_bound_95': lower_bound,
            'upper_bound_95': upper_bound,
            'confidence_interval_width': upper_bound - lower_bound
        })
        
        return results
    
    def explain_prediction(
        self,
        X: pd.DataFrame,
        index: int = 0,
        top_n: int = 5
    ) -> Dict[str, float]:
        """
        Generate SHAP explanation for a single prediction.
        
        Args:
            X: Feature matrix
            index: Index of prediction to explain
            top_n: Number of top features to return
        
        Returns:
            Dictionary of feature -> SHAP value
        """
        if self.explainer is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # Get SHAP values for specific prediction
        shap_dict = dict(zip(self.feature_names, shap_values[index]))
        
        # Sort by absolute value and return top N
        sorted_features = sorted(
            shap_dict.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return dict(sorted_features[:top_n])
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from trained model.
        
        Returns:
            DataFrame with features and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        importance = self.model.feature_importances_
        
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return df
    
    def save_model(self, path: str):
        """Save trained model to file."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        self.model.save_model(path)
    
    def load_model(self, path: str):
        """Load trained model from file."""
        self.model = xgb.XGBRegressor()
        self.model.load_model(path)
        self.explainer = shap.TreeExplainer(self.model)

