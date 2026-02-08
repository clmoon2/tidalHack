"""
Example: ML-based growth prediction using XGBoost.

This script demonstrates:
1. Feature engineering from anomaly data
2. Training XGBoost model
3. Making predictions with confidence intervals
4. SHAP explanations for interpretability
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from src.ingestion.loader import ILIDataLoader
from src.prediction.feature_engineer import FeatureEngineer
from src.prediction.growth_predictor import GrowthPredictor
from src.growth.analyzer import GrowthAnalyzer
from src.matching.matcher import HungarianMatcher
from src.matching.similarity import SimilarityCalculator

print("=" * 80)
print("ML GROWTH PREDICTION EXAMPLE")
print("=" * 80)
print()

# Step 1: Load data
print("Step 1: Loading inspection data...")
loader = ILIDataLoader()

data_dir = project_root / "data"
run_2015 = loader.load_csv(str(data_dir / "ILIDataV2_2015.csv"), "RUN_2015")
run_2022 = loader.load_csv(str(data_dir / "ILIDataV2_2022.csv"), "RUN_2022")

anomalies_2015 = run_2015['anomalies']
anomalies_2022 = run_2022['anomalies']
ref_points_2015 = run_2015['reference_points']

print(f"  2015: {len(anomalies_2015)} anomalies")
print(f"  2022: {len(anomalies_2022)} anomalies")
print()

# Step 2: Match anomalies to get historical growth rates
print("Step 2: Matching anomalies to calculate historical growth...")
similarity_calc = SimilarityCalculator()
matcher = HungarianMatcher(confidence_threshold=0.6)

match_result = matcher.match_anomalies(
    anomalies_2015,
    anomalies_2022,
    "RUN_2015",
    "RUN_2022",
    similarity_calc
)

# Calculate growth rates
analyzer = GrowthAnalyzer(rapid_growth_threshold=5.0)
growth_analysis = analyzer.analyze_matches(
    match_result['matches'],
    anomalies_2015,
    anomalies_2022,
    time_interval_years=7.0
)

# Create growth rate lookup
growth_rates = {}
for metric in growth_analysis['growth_metrics']:
    # Extract 2022 anomaly ID from match_id
    match_id = metric.match_id
    parts = match_id.split('_')
    if len(parts) >= 6:
        anomaly_2022_id = f"{parts[3]}_{parts[4]}_{parts[5]}"
        growth_rates[anomaly_2022_id] = metric.depth_growth_rate

print(f"  Matched: {len(match_result['matches'])} pairs")
print(f"  Growth rates calculated: {len(growth_rates)}")
print()

# Step 3: Engineer features
print("Step 3: Engineering features for ML...")
engineer = FeatureEngineer()

# Use subset of 2022 anomalies for training (those with historical growth)
training_anomalies = [
    a for a in anomalies_2022 
    if a.id in growth_rates
]

features_df = engineer.extract_features(
    training_anomalies,
    ref_points_2015,
    growth_rates
)

print(f"  Features extracted: {len(engineer.get_feature_names())} features")
print(f"  Training samples: {len(features_df)}")
print(f"  Feature names: {', '.join(engineer.get_feature_names()[:5])}...")
print()

# Step 4: Train XGBoost model
print("Step 4: Training XGBoost model...")
predictor = GrowthPredictor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1
)

# Prepare training data
X = features_df[engineer.get_feature_names()]
y = features_df['anomaly_id'].map(growth_rates)

# Remove any NaN values
valid_idx = ~y.isna()
X = X[valid_idx]
y = y[valid_idx]

if len(X) < 10:
    print("  ⚠️  Not enough training data (need at least 10 samples)")
    print("  Skipping model training...")
else:
    metrics = predictor.train(X, y, test_size=0.2)
    
    print(f"  Model trained successfully!")
    print(f"  Training samples: {metrics['n_train']}")
    print(f"  Test samples: {metrics['n_test']}")
    print(f"  R² score: {metrics['r2']:.3f}")
    print(f"  MAE: {metrics['mae']:.3f} pp/year")
    print(f"  RMSE: {metrics['rmse']:.3f} pp/year")
    print()
    
    # Step 5: Feature importance
    print("Step 5: Feature importance...")
    importance_df = predictor.get_feature_importance()
    print("  Top 5 most important features:")
    for idx, row in importance_df.head(5).iterrows():
        print(f"    {row['feature']}: {row['importance']:.3f}")
    print()
    
    # Step 6: Make predictions
    print("Step 6: Making predictions for new anomalies...")
    
    # Predict for all 2022 anomalies
    all_features = engineer.extract_features(
        anomalies_2022[:100],  # Limit to first 100 for demo
        ref_points_2015,
        growth_rates
    )
    
    X_pred = all_features[engineer.get_feature_names()]
    predictions = predictor.predict(X_pred, ensemble_weight=0.7)
    
    print(f"  Predictions made: {len(predictions)}")
    print(f"  Mean predicted growth: {predictions['predicted_growth_rate'].mean():.3f} pp/year")
    print(f"  Max predicted growth: {predictions['predicted_growth_rate'].max():.3f} pp/year")
    print()
    
    # Step 7: SHAP explanations
    print("Step 7: SHAP explanations for top predictions...")
    
    # Find anomalies with highest predicted growth
    top_indices = predictions['predicted_growth_rate'].nlargest(3).index
    
    for i, idx in enumerate(top_indices, 1):
        anomaly_id = all_features.iloc[idx]['anomaly_id']
        pred_growth = predictions.iloc[idx]['predicted_growth_rate']
        
        print(f"\n  Anomaly #{i}: {anomaly_id}")
        print(f"  Predicted growth: {pred_growth:.3f} pp/year")
        print(f"  Confidence interval: [{predictions.iloc[idx]['lower_bound_95']:.3f}, {predictions.iloc[idx]['upper_bound_95']:.3f}]")
        
        # Get SHAP explanation
        shap_values = predictor.explain_prediction(X_pred, index=idx, top_n=5)
        print(f"  Top contributing features:")
        for feature, value in shap_values.items():
            print(f"    {feature}: {value:+.3f}")
    
    print()
    
    # Step 8: Save model
    print("Step 8: Saving model...")
    model_path = project_root / "models" / "growth_predictor.json"
    model_path.parent.mkdir(exist_ok=True)
    predictor.save_model(str(model_path))
    print(f"  Model saved to: {model_path}")
    print()

print("=" * 80)
print("✅ ML PREDICTION EXAMPLE COMPLETE!")
print("=" * 80)
print()
print("Key Takeaways:")
print("  • XGBoost can predict future growth rates from current anomaly features")
print("  • SHAP explanations provide interpretability for predictions")
print("  • Ensemble approach (70% ML + 30% linear) provides robust predictions")
print("  • Confidence intervals quantify prediction uncertainty")
print()
