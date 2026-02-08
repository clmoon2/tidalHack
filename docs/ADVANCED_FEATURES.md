# Advanced Features Guide

This guide covers the advanced ML and LLM features of the ILI Data Alignment System.

## Table of Contents

1. [DBSCAN Clustering (ASME B31G Interaction Zones)](#dbscan-clustering-asme-b31g-interaction-zones)
2. [ML Growth Prediction](#ml-growth-prediction)
3. [Natural Language Queries](#natural-language-queries)
4. [Setup and Configuration](#setup-and-configuration)
5. [API Reference](#api-reference)

---

## DBSCAN Clustering (ASME B31G Interaction Zones)

### Overview

The clustering module automatically identifies groups of spatially proximate anomalies within a single inspection run that form **ASME B31G interaction zones**. It uses scikit-learn's DBSCAN algorithm — a density-based clustering method that is ideal for this use case because it:

- **Requires no pre-specified cluster count** — the number of zones emerges from the data
- **Naturally classifies isolated anomalies as noise** — only groups that meet the density threshold become clusters
- **Works directly with physical proximity thresholds** — axial separation (ft) and circumferential separation (clock hours)

### How It Works

1. **Feature extraction** — For each anomaly, the `(distance, clock_position)` pair is extracted.
2. **Circular clock handling** — Clock positions (1–12) are converted to `(cos θ, sin θ)` coordinates so that 12 o'clock and 1 o'clock are treated as neighbours.
3. **Feature scaling** — Axial distances are divided by `axial_threshold_ft` and circumferential coordinates are scaled by the chord length at `clock_threshold` so that `eps = 1.0` respects both thresholds equally.
4. **DBSCAN** — `DBSCAN(eps=1.0, min_samples=min_cluster_size, metric='euclidean')` is run on the 3-column feature matrix `[scaled_dist, scaled_cx, scaled_cy]`.
5. **Zone construction** — Each cluster label is packaged into an `InteractionZone` object containing centroid position, span, maximum depth, combined length, and member anomaly IDs.

### Quick Start

```python
from src.analysis.cluster_detector import ClusterDetector

detector = ClusterDetector(
    axial_threshold_ft=1.0,   # max axial separation (ft) for neighbours
    clock_threshold=1.5,      # max circumferential separation (clock hours)
    min_cluster_size=2,       # DBSCAN min_samples
)

# Run on a single inspection run
updated_anomalies, zones = detector.detect_clusters(anomalies, "RUN_2022")

print(f"Interaction zones: {len(zones)}")
for zone in zones:
    print(f"  {zone.zone_id}: {zone.anomaly_count} anomalies, "
          f"centroid {zone.centroid_distance:.0f} ft @ {zone.centroid_clock} o'clock, "
          f"max depth {zone.max_depth_pct:.1f}%, "
          f"combined length {zone.combined_length_in:.1f} in")

# Clustered anomalies now carry a cluster_id
clustered = [a for a in updated_anomalies if a.cluster_id]
print(f"Clustered: {len(clustered)} / {len(updated_anomalies)} "
      f"({len(clustered)/len(updated_anomalies)*100:.1f}%)")
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `axial_threshold_ft` | 1.0 | Maximum axial separation in feet for two anomalies to be neighbours (~6× wall thickness) |
| `clock_threshold` | 1.5 | Maximum circumferential separation in clock hours |
| `min_cluster_size` | 2 | Minimum number of anomalies to form a cluster (DBSCAN `min_samples`) |
| `wall_thickness_in` | 0.25 | Nominal wall thickness in inches (informational) |

### InteractionZone Data Model

Each detected cluster is represented as an `InteractionZone`:

```python
class InteractionZone(BaseModel):
    zone_id: str              # e.g. "ZONE_RUN_2022_0001"
    run_id: str               # Inspection run this zone belongs to
    anomaly_ids: List[str]    # IDs of member anomalies
    anomaly_count: int        # Number of anomalies (>= 2)
    centroid_distance: float  # Mean axial position (ft)
    centroid_clock: float     # Circular mean clock position (1–12)
    span_distance_ft: float   # Max − min distance within zone (ft)
    span_clock: float         # Smallest arc containing all clock positions
    max_depth_pct: float      # Worst-case depth in the group (%)
    combined_length_in: float # Sum of individual lengths (conservative per B31G)
```

### REST API

```bash
# Detect interaction zones for a specific run
GET /api/clusters/{run_id}?axial_threshold_ft=1.0&clock_threshold=1.5&min_cluster_size=2

# Example
GET /api/clusters/RUN_2022
```

**Response** includes `zones`, `total_zones`, `clustered_anomaly_count`, `total_anomaly_count`, and `clustered_pct`.

### Pipeline Integration

Clustering runs as **Step 2 of 11** in the three-way analysis pipeline (`ThreeWayAnalyzer.run_full_analysis`). It executes immediately after data loading and before DTW alignment:

```
1. Load datasets → 2. DBSCAN clustering → 3. Extract ref points → 4–5. DTW align → …
```

The resulting `InteractionZone` lists are stored in `ThreeWayAnalysisResult.interaction_zones_2007/2015/2022`, along with aggregate `total_clusters` and `clustered_anomaly_pct` fields.

---

## ML Growth Prediction

### Overview

The ML growth prediction module uses XGBoost to predict future anomaly growth rates based on current features and historical patterns.

### Features

- **XGBoost Regression**: Gradient boosting for accurate predictions
- **Feature Engineering**: Automatic extraction of relevant features
- **SHAP Explanations**: Interpretable AI with feature importance
- **Confidence Intervals**: Quantify prediction uncertainty
- **Ensemble Approach**: Combines ML (70%) with linear baseline (30%)

### Quick Start

```python
from src.prediction.feature_engineer import FeatureEngineer
from src.prediction.growth_predictor import GrowthPredictor

# 1. Engineer features
engineer = FeatureEngineer()
features = engineer.extract_features(
    anomalies,
    reference_points,
    historical_growth_rates
)

# 2. Train model
predictor = GrowthPredictor(n_estimators=100, max_depth=6)
X = features[engineer.get_feature_names()]
y = features['anomaly_id'].map(growth_rates)
metrics = predictor.train(X, y)

# 3. Make predictions
predictions = predictor.predict(X_new)

# 4. Explain predictions
shap_values = predictor.explain_prediction(X_new, index=0)
```

### Feature Engineering

The system automatically extracts these features:

**Current Dimensions:**
- `depth_pct`: Current depth percentage
- `length_in`: Length in inches
- `width_in`: Width in inches

**Spatial Features:**
- `clock_position`: Clock position (1-12)
- `dist_to_nearest_ref`: Distance to nearest reference point

**Derived Features:**
- `length_width_ratio`: Length/width ratio
- `depth_length_ratio`: Depth/length ratio

**Historical:**
- `historical_growth_rate`: Past growth rate (if available)

**Categorical (one-hot encoded):**
- `feature_type_*`: Anomaly type (metal_loss, dent, crack, etc.)

### Model Performance

Expected performance on real data:
- **R² score**: > 0.80 (explains 80%+ of variance)
- **MAE**: < 1.0 pp/year (mean absolute error)
- **RMSE**: < 1.5 pp/year (root mean squared error)

### SHAP Explanations

SHAP (SHapley Additive exPlanations) provides interpretable predictions:

```python
# Get top 5 contributing features
shap_values = predictor.explain_prediction(X, index=0, top_n=5)

# Example output:
# {
#   'depth_pct': +2.3,           # High depth increases predicted growth
#   'historical_growth_rate': +1.8,  # Past growth predicts future growth
#   'dist_to_nearest_ref': -0.5,     # Distance from weld reduces risk
#   'length_width_ratio': +0.3,      # Elongated shape increases risk
#   'clock_position': -0.2           # Position has minor effect
# }
```

### Saving and Loading Models

```python
# Save trained model
predictor.save_model('models/growth_predictor.json')

# Load model later
predictor = GrowthPredictor()
predictor.load_model('models/growth_predictor.json')
```

---

## Natural Language Queries

### Overview

The natural language query system uses Google Gemini to understand and execute queries in plain English.

### Features

- **Natural Language Understanding**: Parse queries in plain English
- **Automatic Query Execution**: Convert to Pandas operations
- **Result Summarization**: Generate natural language summaries
- **Conversation Context**: Handle follow-up questions

### Quick Start

```python
from src.query.nl_query_parser import NLQueryParser
from src.query.query_executor import QueryExecutor

# Initialize (requires GOOGLE_API_KEY environment variable)
parser = NLQueryParser()
executor = QueryExecutor()

# Parse and execute query
query = "Show me all metal loss anomalies deeper than 50%"
parsed = parser.parse_query(query)
result = executor.execute(dataframe, parsed)

print(result['summary'])  # Natural language summary
print(result['results'])  # DataFrame with results
```

### Example Queries

**Filtering:**
```
"Show me all metal loss anomalies deeper than 50%"
"Find anomalies between 1000 and 2000 feet"
"Which anomalies are at the 12 o'clock position?"
```

**Aggregation:**
```
"What's the average depth by feature type?"
"How many anomalies are there in each run?"
"What's the maximum depth in the dataset?"
```

**Sorting:**
```
"Top 10 deepest anomalies"
"Show me the longest anomalies first"
"Sort by distance along the pipeline"
```

**Complex Queries:**
```
"Find metal loss anomalies deeper than 60% within 5 feet of a girth weld"
"What's the average growth rate for anomalies at 6 o'clock?"
"Show me the 5 highest risk anomalies with rapid growth"
```

### Query Structure

Parsed queries have this structure:

```python
{
    'filters': [
        {'column': 'depth_pct', 'operator': '>', 'value': 50},
        {'column': 'feature_type', 'operator': '==', 'value': 'metal_loss'}
    ],
    'aggregations': [
        {'function': 'mean', 'column': 'depth_pct'}
    ],
    'sort': [
        {'column': 'depth_pct', 'ascending': False}
    ],
    'group_by': ['feature_type'],
    'limit': 10
}
```

### Supported Operations

**Filter Operators:**
- `==`, `!=`: Equality/inequality
- `>`, `<`, `>=`, `<=`: Comparisons
- `in`, `not_in`: List membership
- `contains`: String matching

**Aggregation Functions:**
- `count`: Count rows
- `sum`: Sum values
- `mean`: Average
- `median`: Median value
- `min`, `max`: Min/max values
- `std`: Standard deviation

### Conversation Context

The system maintains conversation history for follow-up questions:

```python
# First query
result1 = parser.parse_query("Show me metal loss anomalies")

# Follow-up query (uses context)
result2 = parser.parse_query("Now filter to depth > 50%")

# Clear history when starting new conversation
parser.clear_history()
```

---

## Setup and Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Google API Key for Gemini
GOOGLE_API_KEY=your_api_key_here
```

**SECURITY WARNING**: Never commit `.env` files to version control!

### Getting a Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key to your `.env` file
4. **Revoke any keys that were accidentally exposed**

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import xgboost; import langchain_google_genai; print('✓ All dependencies installed')"
```

### Testing the Setup

```bash
# Test ML prediction
python examples/ml_prediction_example.py

# Test natural language queries
python examples/nl_query_example.py
```

---

## API Reference

### ClusterDetector

```python
class ClusterDetector:
    def __init__(
        self,
        axial_threshold_ft: float = 1.0,
        clock_threshold: float = 1.5,
        min_cluster_size: int = 2,
        wall_thickness_in: float = 0.25,
    )

    def detect_clusters(
        self,
        anomalies: List[AnomalyRecord],
        run_id: str,
    ) -> Tuple[List[AnomalyRecord], List[InteractionZone]]
```

Detects ASME B31G interaction zones using DBSCAN clustering.

**Parameters:**
- `anomalies`: List of anomaly records from a single run
- `run_id`: Inspection run identifier

**Returns:** Tuple of updated anomalies (with `cluster_id` set) and list of `InteractionZone` objects.

---

### FeatureEngineer

```python
class FeatureEngineer:
    def extract_features(
        self,
        anomalies: List[Anomaly],
        reference_points: List[ReferencePoint],
        growth_rates: Dict[str, float] = None
    ) -> pd.DataFrame
```

Extracts features from anomaly data for ML training.

**Parameters:**
- `anomalies`: List of anomaly records
- `reference_points`: List of reference points
- `growth_rates`: Optional historical growth rates

**Returns:** DataFrame with engineered features

---

### GrowthPredictor

```python
class GrowthPredictor:
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1
    )
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Dict[str, float]
    
    def predict(
        self,
        X: pd.DataFrame,
        ensemble_weight: float = 0.7
    ) -> pd.DataFrame
    
    def explain_prediction(
        self,
        X: pd.DataFrame,
        index: int = 0,
        top_n: int = 5
    ) -> Dict[str, float]
```

XGBoost-based growth rate predictor.

**Key Methods:**
- `train()`: Train model on historical data
- `predict()`: Make predictions with confidence intervals
- `explain_prediction()`: Get SHAP explanations
- `get_feature_importance()`: Get feature importance scores
- `save_model()` / `load_model()`: Persist trained models

---

### NLQueryParser

```python
class NLQueryParser:
    def __init__(self, api_key: Optional[str] = None)
    
    def parse_query(self, query: str) -> Dict[str, Any]
    
    def clear_history(self)
```

Parses natural language queries using Google Gemini.

**Key Methods:**
- `parse_query()`: Convert natural language to structured query
- `clear_history()`: Clear conversation context

---

### QueryExecutor

```python
class QueryExecutor:
    def __init__(self, api_key: Optional[str] = None)
    
    def execute(
        self,
        data: pd.DataFrame,
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]
```

Executes parsed queries against data.

**Returns:**
```python
{
    'results': pd.DataFrame,  # Query results
    'summary': str,           # Natural language summary
    'row_count': int          # Number of results
}
```

---

## Best Practices

### ML Prediction

1. **Training Data**: Use at least 100 matched pairs for reliable models
2. **Feature Selection**: Let SHAP identify important features
3. **Validation**: Always check R² > 0.80 on test data
4. **Ensemble**: Use 70% ML + 30% linear for robustness
5. **Retraining**: Retrain annually with new inspection data

### Natural Language Queries

1. **Be Specific**: "metal loss deeper than 50%" vs "bad anomalies"
2. **Use Domain Terms**: "depth", "clock position", "girth weld"
3. **Start Simple**: Test basic queries before complex ones
4. **Check Results**: Always verify query results make sense
5. **Clear Context**: Use `clear_history()` for new conversations

### Security

1. **Never Commit API Keys**: Always use `.env` files
2. **Rotate Keys**: Change keys if accidentally exposed
3. **Limit Scope**: Use API keys with minimal required permissions
4. **Monitor Usage**: Track API calls to detect abuse

---

## Troubleshooting

### "Model not trained" Error

```python
# Make sure to call train() before predict()
predictor.train(X, y)
predictions = predictor.predict(X_new)
```

### "Google API key not found" Error

```bash
# Set environment variable
export GOOGLE_API_KEY='your-key-here'

# Or create .env file
echo "GOOGLE_API_KEY=your-key-here" > .env
```

### Low R² Score

- Check training data quality (outliers, missing values)
- Increase `n_estimators` (try 200-500)
- Adjust `max_depth` (try 8-10)
- Ensure sufficient training samples (>100)

### Query Parsing Errors

- Simplify query language
- Use exact column names from schema
- Check for typos in feature types
- Verify API key is valid

---

## Performance Considerations

### ML Prediction

- **Training Time**: ~1-5 seconds for 1000 samples
- **Prediction Time**: <1 second for 1000 predictions
- **Memory Usage**: ~50MB for trained model
- **Recommended**: Batch predictions for >10K anomalies

### Natural Language Queries

- **Parse Time**: ~1-2 seconds per query (API call)
- **Execution Time**: <1 second for most queries
- **Rate Limits**: Google Gemini free tier limits apply
- **Recommended**: Cache parsed queries for repeated use

---

## Future Enhancements

Planned features for future releases:

1. **AutoML**: Automatic hyperparameter tuning
2. **Time Series**: LSTM models for temporal patterns
3. **Anomaly Detection**: Identify unusual growth patterns
4. **Multi-Model Ensemble**: Combine XGBoost, Random Forest, Neural Networks
5. **Voice Queries**: Speech-to-text integration
6. **Query Suggestions**: Auto-complete for common queries

---

## Support

For questions or issues:

1. Check this documentation
2. Review example scripts in `examples/`
3. Check error messages and logs
4. Consult the main README.md

---

**Last Updated**: February 8, 2026  
**Version**: 1.1.0
