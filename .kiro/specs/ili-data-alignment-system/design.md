# Design Document: ILI Data Alignment & Corrosion Growth Prediction System

## Overview

The ILI Data Alignment & Corrosion Growth Prediction System is a hybrid architecture combining proven algorithmic approaches with LLM-augmented capabilities. The system processes In-Line Inspection data from multiple pipeline runs, aligns them despite odometer drift, matches anomalies across time, and predicts corrosion growth to optimize excavation decisions.

### Architecture Philosophy

The design follows a 70/30 split:
- **70% Proven Algorithms**: DTW for alignment, Hungarian algorithm for matching, XGBoost for prediction
- **30% LLM Augmentation**: Natural language queries, agentic explanations, RAG over standards

This approach ensures reliability for core functionality while leveraging AI for enhanced usability and insights.

### Key Design Decisions

1. **Pandas-centric data processing**: Use DataFrames as the primary data structure for flexibility and performance
2. **Modular pipeline architecture**: Separate ingestion, alignment, matching, and prediction into independent modules
3. **SQLite for persistence**: Lightweight database for storing processed results and match history
4. **Streamlit for UI**: Rapid development of interactive dashboard with minimal frontend complexity
5. **LangChain for LLM orchestration**: Standardized framework for NL queries and agentic workflows
6. **Pydantic for validation**: Type-safe data models with automatic validation

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌──────────────────┐              ┌──────────────────────┐    │
│  │  Streamlit UI    │              │   FastAPI REST API   │    │
│  │  - Upload        │              │   - /upload          │    │
│  │  - Alignment     │              │   - /align           │    │
│  │  - Matching      │              │   - /match           │    │
│  │  - Growth        │              │   - /predict         │    │
│  │  - NL Query      │              │   - /query           │    │
│  └──────────────────┘              └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Ingestion   │  │  Alignment   │  │  Matching Engine     │ │
│  │  Pipeline    │  │  Engine      │  │  - Similarity Calc   │ │
│  │              │  │  - DTW       │  │  - Hungarian Algo    │ │
│  └──────────────┘  │  - Correction│  │  - Confidence Score  │ │
│                    └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Growth      │  │  ML Predictor│  │  NL Query Engine     │ │
│  │  Analysis    │  │  - XGBoost   │  │  - LLM Parser        │ │
│  │              │  │  - SHAP      │  │  - Query Executor    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Agentic Explanation System                      │  │
│  │  - Alignment Agent  - Matching Agent                      │  │
│  │  - Validator Agent  - Explainer Agent                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  SQLite DB   │  │  ChromaDB    │  │  File Storage        │ │
│  │  - Anomalies │  │  - Standards │  │  - Uploaded Excel    │ │
│  │  - Matches   │  │  - Embeddings│  │  - Exports           │ │
│  │  - Runs      │  │              │  │  - Model Artifacts   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: Excel files → Pandas DataFrame → Validation → SQLite
2. **Alignment**: Reference points → DTW → Distance correction function → Corrected coordinates
3. **Matching**: Aligned anomalies → Similarity matrix → Hungarian algorithm → Matched pairs
4. **Growth Analysis**: Matched pairs → Growth rate calculation → Risk scoring → Prioritization
5. **Prediction**: Historical data → Feature engineering → XGBoost → Future depth predictions
6. **Query**: NL text → LLM parsing → Pandas/SQL execution → Results + Explanation

## Components and Interfaces

### 1. Data Ingestion Pipeline

**Purpose**: Load, validate, and standardize ILI data from Excel files.

**Key Classes**:

```python
class ILIDataLoader:
    def load_excel(file_path: str, run_id: str) -> pd.DataFrame
    def validate_schema(df: pd.DataFrame) -> ValidationResult
    def standardize_units(df: pd.DataFrame) -> pd.DataFrame
    def extract_reference_points(df: pd.DataFrame) -> pd.DataFrame
    
class DataValidator:
    def validate_anomaly_record(record: AnomalyRecord) -> List[ValidationError]
    def check_required_fields(record: dict) -> bool
    def validate_ranges(record: dict) -> List[str]
```

**Interfaces**:
- Input: Excel file path, run metadata
- Output: Validated DataFrame, reference points DataFrame, validation report

**Algorithm**: 
1. Parse Excel using pandas.read_excel with appropriate dtype specifications
2. Apply Pydantic schema validation to each row
3. Standardize clock positions: convert text (e.g., "3 o'clock") to numeric (3.0)
4. Convert units: miles→feet, mm→inches, apply percentage normalization
5. Extract reference points by filtering feature_type in ['girth_weld', 'valve', 'tee']
6. Handle missing values: forward-fill for clock position, median for dimensions
7. Generate data quality report with counts, missing value percentages, outliers

### 2. Reference Point Alignment Engine

**Purpose**: Align inspection runs using Dynamic Time Warping on reference point sequences.

**Key Classes**:

```python
class DTWAligner:
    def align_sequences(seq1: np.ndarray, seq2: np.ndarray) -> AlignmentResult
    def calculate_distance_matrix(seq1: np.ndarray, seq2: np.ndarray) -> np.ndarray
    def find_optimal_path(distance_matrix: np.ndarray) -> List[Tuple[int, int]]
    
class DistanceCorrectionFunction:
    def __init__(matched_points: List[Tuple[float, float]])
    def correct_distance(source_distance: float) -> float
    def interpolate(distance: float) -> float
```

**Interfaces**:
- Input: Two DataFrames of reference points with odometer readings
- Output: Matched reference point pairs, distance correction function, alignment metrics

**Algorithm**:

1. **Extract sequences**: Get odometer readings for girth welds from both runs
2. **Compute DTW distance matrix**: 
   - For each pair (i, j), calculate |distance1[i] - distance2[j]|
   - Apply local constraint: only allow matches within ±10% odometer drift window
3. **Find optimal warping path**: Use dynamic programming to minimize cumulative distance
4. **Create correction function**:
   - Fit piecewise linear interpolation through matched points
   - Use scipy.interpolate.interp1d with 'linear' method
   - Extrapolate using nearest boundary values for out-of-range distances
5. **Calculate metrics**:
   - Match rate: (matched points / total points) * 100
   - RMSE: sqrt(mean((corrected_dist1 - dist2)²))

**DTW Pseudocode**:
```
function DTW(seq1, seq2):
    n = length(seq1)
    m = length(seq2)
    cost = matrix(n+1, m+1, fill=infinity)
    cost[0, 0] = 0
    
    for i in 1 to n:
        for j in 1 to m:
            if abs(seq1[i] - seq2[j]) / seq1[i] <= 0.10:  # 10% drift constraint
                distance = abs(seq1[i] - seq2[j])
                cost[i, j] = distance + min(
                    cost[i-1, j],    # insertion
                    cost[i, j-1],    # deletion
                    cost[i-1, j-1]   # match
                )
    
    return backtrack_path(cost)
```

### 3. Anomaly Matching Engine

**Purpose**: Match anomalies across aligned runs using multi-criteria similarity and optimal assignment.

**Key Classes**:

```python
class SimilarityCalculator:
    def calculate_similarity(anomaly1: Anomaly, anomaly2: Anomaly) -> float
    def distance_similarity(dist1: float, dist2: float) -> float
    def clock_similarity(clock1: float, clock2: float) -> float
    def dimension_similarity(dim1: dict, dim2: dict) -> float
    
class HungarianMatcher:
    def create_cost_matrix(anomalies1: List[Anomaly], anomalies2: List[Anomaly]) -> np.ndarray
    def solve_assignment(cost_matrix: np.ndarray) -> List[Tuple[int, int]]
    def filter_low_confidence(matches: List[Match], threshold: float) -> List[Match]
```

**Interfaces**:
- Input: Two DataFrames of anomalies (with corrected distances), similarity weights
- Output: List of matched pairs with confidence scores, unmatched anomalies

**Algorithm**:

1. **Build similarity matrix** (n × m where n, m are anomaly counts):
   ```
   similarity(a1, a2) = w_dist * sim_dist(a1, a2) +
                        w_clock * sim_clock(a1, a2) +
                        w_type * sim_type(a1, a2) +
                        w_depth * sim_depth(a1, a2) +
                        w_length * sim_length(a1, a2) +
                        w_width * sim_width(a1, a2)
   ```

2. **Component similarities**:
   - Distance: `sim_dist = exp(-|dist1 - dist2| / sigma_dist)` where sigma_dist = 5 feet
   - Clock: `sim_clock = exp(-min(|c1 - c2|, 12 - |c1 - c2|) / sigma_clock)` where sigma_clock = 1.0
   - Type: `sim_type = 1.0 if type1 == type2 else 0.0`
   - Dimensions: `sim_dim = exp(-|dim1 - dim2| / (dim1 + dim2 + epsilon))`

3. **Default weights**: w_dist=0.35, w_clock=0.20, w_type=0.15, w_depth=0.15, w_length=0.075, w_width=0.075

4. **Convert to cost matrix**: `cost = 1 - similarity` (Hungarian minimizes cost)

5. **Apply Hungarian algorithm**: Use scipy.optimize.linear_sum_assignment

6. **Filter matches**: Keep only matches with similarity > 0.6 threshold

7. **Classify unmatched**:
   - Anomalies in run2 with no match → "new"
   - Anomalies in run1 with no match → "repaired_or_removed"

8. **Detect merged/split**: Check if multiple anomalies in one run map to nearby region in other run

### 4. Growth Rate Analysis

**Purpose**: Calculate growth rates and risk scores for matched anomalies.

**Key Classes**:

```python
class GrowthAnalyzer:
    def calculate_growth_rate(match: Match) -> GrowthMetrics
    def identify_rapid_growth(matches: List[Match], threshold: float) -> List[Match]
    def calculate_risk_score(anomaly: Anomaly, growth_rate: float) -> float
    
class RiskScorer:
    def composite_risk(depth: float, growth_rate: float, location: str) -> float
    def rank_by_risk(anomalies: List[Anomaly]) -> List[Anomaly]
```

**Interfaces**:
- Input: List of matched anomaly pairs with timestamps
- Output: Growth metrics, risk scores, prioritized excavation list

**Algorithm**:

1. **Calculate growth rates**:
   ```
   depth_growth_rate = (depth_t2 - depth_t1) / (year_t2 - year_t1)
   length_growth_rate = (length_t2 - length_t1) / (year_t2 - year_t1)
   width_growth_rate = (width_t2 - width_t1) / (year_t2 - year_t1)
   ```

2. **Identify rapid growth**: Flag if `depth_growth_rate > 5.0` (5% per year)

3. **Calculate risk score**:
   ```
   risk_score = (current_depth / 100) * 0.6 +
                (depth_growth_rate / 10) * 0.3 +
                location_factor * 0.1
   
   location_factor = 1.0 if near_girth_weld else 0.5
   ```

4. **Rank anomalies**: Sort by risk_score descending

5. **Generate statistics**:
   - Mean, median, std dev of growth rates by feature type
   - Distribution of risk scores
   - Count of rapid growth anomalies

### 5. Natural Language Query Engine

**Purpose**: Enable engineers to query data using natural language.

**Key Classes**:

```python
class NLQueryParser:
    def __init__(llm: BaseLLM)
    def parse_query(query: str, context: QueryContext) -> ParsedQuery
    def extract_filters(query: str) -> List[Filter]
    def extract_aggregations(query: str) -> List[Aggregation]
    
class QueryExecutor:
    def execute_pandas(parsed_query: ParsedQuery, df: pd.DataFrame) -> pd.DataFrame
    def execute_sql(parsed_query: ParsedQuery, db: Database) -> pd.DataFrame
    def format_results(results: pd.DataFrame) -> str
```

**Interfaces**:
- Input: Natural language query string, conversation context
- Output: Query results DataFrame, natural language summary

**Algorithm**:

1. **LLM Prompt Template**:
   ```
   You are a data query assistant for pipeline inspection data.
   
   Available columns: distance, clock_position, depth_pct, length, width, 
                      feature_type, run_id, match_confidence, growth_rate
   
   User query: "{query}"
   
   Convert this to a Pandas operation. Return JSON:
   {
     "operation": "filter" | "aggregate" | "sort",
     "filters": [{"column": "...", "operator": "...", "value": ...}],
     "aggregations": [{"function": "...", "column": "..."}],
     "sort": {"column": "...", "ascending": true/false}
   }
   ```

2. **Parse LLM response**: Extract JSON and validate structure

3. **Build Pandas query**:
   ```python
   result = df.copy()
   for filter in parsed_query.filters:
       result = result[result[filter.column].apply(filter.operator, filter.value)]
   if parsed_query.aggregations:
       result = result.groupby(...).agg(...)
   if parsed_query.sort:
       result = result.sort_values(...)
   ```

4. **Generate summary**: Use LLM to create natural language description of results

5. **Maintain context**: Store query history in session state for follow-up questions

**Example Queries**:
- "Show all external corrosion over 30% depth within 10 feet of girth welds"
  → Filter: feature_type=='external_corrosion' AND depth_pct>30 AND distance_to_girth_weld<10
- "What's the average growth rate for internal corrosion?"
  → Aggregate: df[df.feature_type=='internal_corrosion'].growth_rate.mean()

### 6. Agentic Match Explanation System

**Purpose**: Provide human-understandable explanations for anomaly matches using multi-agent collaboration.

**Key Classes**:

```python
class AlignmentAgent:
    def verify_alignment(match: Match) -> AlignmentVerification
    def explain_distance_correction(match: Match) -> str
    
class MatchingAgent:
    def explain_similarity_score(match: Match) -> str
    def identify_key_factors(match: Match) -> List[str]
    
class ValidatorAgent:
    def validate_match_quality(match: Match) -> ValidationResult
    def identify_issues(match: Match) -> List[Issue]
    
class ExplainerAgent:
    def synthesize_explanation(match: Match, agent_outputs: dict) -> str
    def format_for_user(explanation: dict) -> str
```

**Interfaces**:
- Input: Matched anomaly pair, similarity components, alignment data
- Output: Structured explanation with evidence, confidence assessment, potential issues

**Algorithm** (using AutoGen framework):

1. **Initialize agents**:
   ```python
   alignment_agent = AssistantAgent(
       name="AlignmentAgent",
       system_message="Verify distance correction and alignment quality"
   )
   matching_agent = AssistantAgent(
       name="MatchingAgent", 
       system_message="Explain similarity scoring and key matching factors"
   )
   validator_agent = AssistantAgent(
       name="ValidatorAgent",
       system_message="Identify potential issues with match quality"
   )
   explainer_agent = AssistantAgent(
       name="ExplainerAgent",
       system_message="Synthesize agent outputs into coherent explanation"
   )
   ```

2. **Agent workflow**:
   ```
   User Request → AlignmentAgent → MatchingAgent → ValidatorAgent → ExplainerAgent → User
   ```

3. **AlignmentAgent output**:
   - Original distances: run1=1234.5 ft, run2=1240.2 ft
   - Corrected distance: 1235.1 ft (correction: +0.6 ft)
   - Alignment quality: RMSE=8.2 ft (within 10 ft threshold)

4. **MatchingAgent output**:
   - Overall similarity: 0.87
   - Key factors: Distance (0.92), Clock position (0.85), Feature type (1.0)
   - Dimension consistency: Depth 32%→35% (+3%), Length 4.2"→4.5" (+0.3")

5. **ValidatorAgent output**:
   - Confidence: HIGH (similarity > 0.8)
   - Issues: None detected
   - Alternative matches: Next best similarity = 0.45 (significantly lower)

6. **ExplainerAgent synthesis**:
   ```
   This is a HIGH CONFIDENCE match (87% similarity). The anomalies are located 
   within 0.6 feet after alignment correction, at the same clock position (3 o'clock),
   and both are external corrosion. The depth increased from 32% to 35% over 7 years,
   indicating a growth rate of 0.43% per year, which is below the rapid growth threshold.
   No issues were identified with this match.
   ```

### 7. Machine Learning Growth Prediction

**Purpose**: Predict future corrosion depth using XGBoost regression.

**Key Classes**:

```python
class GrowthPredictor:
    def __init__(model_path: str)
    def train(training_data: pd.DataFrame) -> TrainingResult
    def predict(anomaly: Anomaly, years_ahead: float) -> Prediction
    def explain_prediction(anomaly: Anomaly, prediction: float) -> Explanation
    
class FeatureEngineer:
    def create_features(anomaly: Anomaly, matches: List[Match]) -> np.ndarray
    def calculate_derived_features(anomaly: Anomaly) -> dict
```

**Interfaces**:
- Input: Historical matched anomalies with growth data
- Output: Trained model, predictions with confidence intervals, SHAP explanations

**Algorithm**:

1. **Feature engineering**:
   ```python
   features = [
       'current_depth_pct',
       'current_length',
       'current_width',
       'depth_growth_rate',
       'length_growth_rate', 
       'width_growth_rate',
       'distance_from_nearest_girth_weld',
       'clock_position',
       'feature_type_encoded',  # one-hot encoding
       'coating_type_encoded',  # one-hot encoding
       'years_since_installation',
       'depth_to_length_ratio',
       'depth_to_width_ratio'
   ]
   ```

2. **Train/test split**: 80/20 split, stratified by feature_type

3. **XGBoost configuration**:
   ```python
   model = xgb.XGBRegressor(
       n_estimators=100,
       max_depth=6,
       learning_rate=0.1,
       subsample=0.8,
       colsample_bytree=0.8,
       objective='reg:squarederror',
       random_state=42
   )
   ```

4. **Training**: Fit model on training data with early stopping (10 rounds)

5. **Evaluation**: Calculate R², MAE, RMSE on test set

6. **Prediction**:
   ```python
   future_depth = current_depth + (growth_rate * years_ahead)
   ml_prediction = model.predict(features)
   final_prediction = 0.7 * ml_prediction + 0.3 * future_depth  # ensemble
   ```

7. **Confidence intervals**: Use quantile regression or bootstrap for uncertainty

8. **SHAP explanation**:
   ```python
   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(features)
   # Visualize top 5 contributing features
   ```

### 8. Interactive Dashboard

**Purpose**: Provide web-based UI for all system functionality.

**Key Components**:

```python
# Streamlit pages
def upload_page():
    # File uploader, run metadata input, validation display
    
def alignment_page():
    # Pipeline schematic, reference point visualization, metrics
    
def matching_page():
    # Side-by-side anomaly comparison, confidence scores, filters
    
def growth_analysis_page():
    # Growth trends, risk scores, rapid growth alerts, export
    
def nl_query_page():
    # Query input, results table, visualizations, conversation history
```

**Interfaces**:
- Input: User interactions (file uploads, button clicks, query text)
- Output: Interactive visualizations, tables, download links

**Key Visualizations**:

1. **Pipeline Schematic** (Plotly):
   - X-axis: Distance along pipeline
   - Y-axis: Clock position (1-12)
   - Points: Anomalies colored by depth percentage
   - Markers: Reference points (girth welds, valves)

2. **Side-by-Side Comparison**:
   - Two columns showing matched anomaly attributes
   - Highlight differences in red, similarities in green
   - Display similarity score and confidence

3. **Growth Trend Chart**:
   - Line chart: Depth over time for selected anomaly
   - Scatter plot: Growth rate distribution
   - Histogram: Risk score distribution

4. **Match Confidence Distribution**:
   - Histogram of match confidence scores
   - Threshold line at 0.6

## Data Models

### Core Data Structures

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

class AnomalyRecord(BaseModel):
    """Single anomaly from ILI run"""
    id: str = Field(..., description="Unique identifier")
    run_id: str = Field(..., description="Inspection run identifier")
    distance: float = Field(..., ge=0, description="Odometer reading in feet")
    clock_position: float = Field(..., ge=1, le=12, description="Circumferential position")
    depth_pct: float = Field(..., ge=0, le=100, description="Depth as percentage of wall thickness")
    length: float = Field(..., gt=0, description="Axial length in inches")
    width: float = Field(..., gt=0, description="Circumferential width in inches")
    feature_type: Literal['external_corrosion', 'internal_corrosion', 'dent', 'crack', 'other']
    coating_type: Optional[str] = None
    inspection_date: datetime
    
    @validator('clock_position')
    def validate_clock(cls, v):
        if not (1 <= v <= 12):
            raise ValueError('Clock position must be between 1 and 12')
        return v

class ReferencePoint(BaseModel):
    """Reference point for alignment"""
    id: str
    run_id: str
    distance: float = Field(..., ge=0)
    point_type: Literal['girth_weld', 'valve', 'tee', 'other']
    description: Optional[str] = None

class Match(BaseModel):
    """Matched anomaly pair"""
    id: str
    anomaly1_id: str
    anomaly2_id: str
    similarity_score: float = Field(..., ge=0, le=1)
    confidence: Literal['HIGH', 'MEDIUM', 'LOW']
    distance_similarity: float
    clock_similarity: float
    type_similarity: float
    depth_similarity: float
    length_similarity: float
    width_similarity: float
    
    @validator('confidence', pre=True, always=True)
    def set_confidence(cls, v, values):
        score = values.get('similarity_score', 0)
        if score >= 0.8:
            return 'HIGH'
        elif score >= 0.6:
            return 'MEDIUM'
        else:
            return 'LOW'

class GrowthMetrics(BaseModel):
    """Growth analysis for matched pair"""
    match_id: str
    time_interval_years: float
    depth_growth_rate: float = Field(..., description="Percentage points per year")
    length_growth_rate: float = Field(..., description="Inches per year")
    width_growth_rate: float = Field(..., description="Inches per year")
    is_rapid_growth: bool
    risk_score: float = Field(..., ge=0, le=1)
    
    @validator('is_rapid_growth', pre=True, always=True)
    def check_rapid_growth(cls, v, values):
        return values.get('depth_growth_rate', 0) > 5.0

class Prediction(BaseModel):
    """ML prediction for future depth"""
    anomaly_id: str
    current_depth_pct: float
    predicted_depth_pct: float
    years_ahead: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    model_confidence: Literal['HIGH', 'MEDIUM', 'LOW']
    top_features: List[tuple[str, float]]  # (feature_name, shap_value)

class AlignmentResult(BaseModel):
    """Result of DTW alignment"""
    run1_id: str
    run2_id: str
    matched_points: List[tuple[str, str]]  # (ref_point1_id, ref_point2_id)
    match_rate: float = Field(..., ge=0, le=100)
    rmse: float = Field(..., ge=0)
    correction_function_params: dict
    
    @validator('match_rate')
    def validate_match_rate(cls, v):
        if v < 95.0:
            raise ValueError('Match rate below 95% threshold')
        return v
    
    @validator('rmse')
    def validate_rmse(cls, v):
        if v > 10.0:
            raise ValueError('RMSE exceeds 10 feet threshold')
        return v
```

### Database Schema

```sql
-- SQLite schema

CREATE TABLE inspection_runs (
    id TEXT PRIMARY KEY,
    pipeline_segment TEXT NOT NULL,
    inspection_date DATE NOT NULL,
    vendor TEXT,
    tool_type TEXT,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE anomalies (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    distance REAL NOT NULL,
    corrected_distance REAL,  -- After alignment
    clock_position REAL NOT NULL,
    depth_pct REAL NOT NULL,
    length REAL NOT NULL,
    width REAL NOT NULL,
    feature_type TEXT NOT NULL,
    coating_type TEXT,
    FOREIGN KEY (run_id) REFERENCES inspection_runs(id)
);

CREATE INDEX idx_anomalies_run ON anomalies(run_id);
CREATE INDEX idx_anomalies_distance ON anomalies(corrected_distance);

CREATE TABLE reference_points (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    distance REAL NOT NULL,
    point_type TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (run_id) REFERENCES inspection_runs(id)
);

CREATE TABLE matches (
    id TEXT PRIMARY KEY,
    anomaly1_id TEXT NOT NULL,
    anomaly2_id TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    confidence TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anomaly1_id) REFERENCES anomalies(id),
    FOREIGN KEY (anomaly2_id) REFERENCES anomalies(id),
    UNIQUE(anomaly1_id, anomaly2_id)
);

CREATE TABLE growth_metrics (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    time_interval_years REAL NOT NULL,
    depth_growth_rate REAL NOT NULL,
    length_growth_rate REAL NOT NULL,
    width_growth_rate REAL NOT NULL,
    is_rapid_growth BOOLEAN NOT NULL,
    risk_score REAL NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

CREATE TABLE predictions (
    id TEXT PRIMARY KEY,
    anomaly_id TEXT NOT NULL,
    predicted_depth_pct REAL NOT NULL,
    years_ahead REAL NOT NULL,
    confidence_interval_lower REAL,
    confidence_interval_upper REAL,
    model_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anomaly_id) REFERENCES anomalies(id)
);
```

