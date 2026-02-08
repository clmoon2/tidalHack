# Advanced Features Guide

This guide covers the advanced ML and LLM features of the ILI Data Alignment System.

## Table of Contents

1. [ML Growth Prediction](#ml-growth-prediction)
2. [Natural Language Queries](#natural-language-queries)
3. [Setup and Configuration](#setup-and-configuration)
4. [API Reference](#api-reference)

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

**Last Updated**: February 7, 2026  
**Version**: 1.0.0
