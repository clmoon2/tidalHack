# ILI Data Alignment System - Implementation Guide

## Project Status Summary

### ✅ Completed Components

#### 1. Project Foundation (Task 1)
- ✅ Directory structure created
- ✅ Dependencies configured (pyproject.toml, requirements.txt)
- ✅ Added reportlab for PDF generation
- ✅ pytest configuration complete
- ✅ Module structure established

#### 2. Data Models (Task 2.1)
- ✅ Core Pydantic models: `AnomalyRecord`, `ReferencePoint`, `Match`, `GrowthMetrics`, `Prediction`, `AlignmentResult`
- ✅ Regulatory models: `RegulatoryRiskScore`, `InspectionInterval`, `ComplianceReport`, `AnomalyWithRegulatory`
- ✅ Validation logic with field validators
- ✅ Regulatory thresholds constants class
- ✅ Color scheme constants for compliance

#### 3. Database Layer (Task 3.1)
- ✅ SQLAlchemy schema with 8 tables:
  - `inspection_runs`, `anomalies`, `reference_points`, `matches`
  - `growth_metrics`, `predictions`, `alignment_results`, `compliance_reports`
- ✅ Database connection manager with context manager
- ✅ Comprehensive CRUD operations for all entities
- ✅ Indexes for performance optimization
- ✅ Regulatory fields integrated into schema

#### 4. Regulatory Compliance Module (Task 10.1 - Partial)
- ✅ `RegulatoryRiskScorer` class fully implemented:
  - Multi-factor risk scoring (depth + growth + location)
  - 49 CFR 192.933 classification
  - ASME B31.8S growth rate classification
  - Risk level determination (CRITICAL/HIGH/MODERATE/LOW/ACCEPTABLE)
  - Action requirement logic (Immediate/Scheduled/Monitor/Standard)

### ⏳ Remaining Implementation (18 Major Tasks)

## Implementation Roadmap

### Phase 1: Core Data Processing (Tasks 4-9)
**Estimated Time: 2-3 weeks**

#### Task 4: Data Ingestion Pipeline
**Priority: HIGH** | **Complexity: Medium**

Components to build:
```python
# src/ingestion/loader.py
class ILIDataLoader:
    def load_excel(file_path, run_id) -> pd.DataFrame
    def validate_schema(df) -> ValidationResult
    def standardize_units(df) -> pd.DataFrame
    def extract_reference_points(df) -> pd.DataFrame

# src/ingestion/validator.py
class DataValidator:
    def validate_anomaly_record(record) -> List[ValidationError]
    def check_required_fields(record) -> bool
    def validate_ranges(record) -> List[str]
```

**Key Requirements:**
- Parse Excel files with pandas
- Standardize clock positions (text → numeric 1-12)
- Convert units (miles→feet, mm→inches, depth→percentage)
- Extract reference points (girth_weld, valve, tee)
- Handle missing values (forward-fill, median imputation)
- Generate data quality reports

**Testing:**
- Property test: Data transformation consistency
- Property test: Imputation idempotence
- Property test: Reference point extraction completeness

---

#### Task 6: DTW Alignment Engine
**Priority: HIGH** | **Complexity: High**

Components to build:
```python
# src/alignment/dtw_aligner.py
class DTWAligner:
    def align_sequences(seq1, seq2) -> AlignmentResult
    def calculate_distance_matrix(seq1, seq2) -> np.ndarray
    def find_optimal_path(distance_matrix) -> List[Tuple[int, int]]

# src/alignment/correction.py
class DistanceCorrectionFunction:
    def __init__(matched_points)
    def correct_distance(source_distance) -> float
    def interpolate(distance) -> float
```

**Algorithm:**
- Dynamic Time Warping with 10% drift constraint
- Piecewise linear interpolation (scipy.interpolate.interp1d)
- Match rate >= 95%, RMSE <= 10 feet

**Testing:**
- Property test: Alignment quality thresholds
- Property test: Distance correction accuracy

---

#### Task 7: Anomaly Matching Engine
**Priority: HIGH** | **Complexity: High**

Components to build:
```python
# src/matching/similarity.py
class SimilarityCalculator:
    def calculate_similarity(anomaly1, anomaly2) -> float
    def distance_similarity(dist1, dist2) -> float
    def clock_similarity(clock1, clock2) -> float
    def dimension_similarity(dim1, dim2) -> float

# src/matching/hungarian.py
class HungarianMatcher:
    def create_cost_matrix(anomalies1, anomalies2) -> np.ndarray
    def solve_assignment(cost_matrix) -> List[Tuple[int, int]]
    def filter_low_confidence(matches, threshold) -> List[Match]
```

**Algorithm:**
- Multi-criteria similarity (distance, clock, type, dimensions)
- Hungarian algorithm (scipy.optimize.linear_sum_assignment)
- Confidence threshold: 0.6
- Precision >= 90%, Recall >= 85%

**Testing:**
- Property test: Matching precision and recall
- Property test: Unmatched classification

---

#### Task 9: Growth Rate Analysis
**Priority: HIGH** | **Complexity: Medium**

Components to build:
```python
# src/growth/analyzer.py
class GrowthAnalyzer:
    def calculate_growth_rate(match) -> GrowthMetrics
    def identify_rapid_growth(matches, threshold=5.0) -> List[Match]
    def calculate_risk_score(anomaly, growth_rate) -> float

# src/growth/risk_scorer.py
class RiskScorer:
    def composite_risk(depth, growth_rate, location) -> float
    def rank_by_risk(anomalies) -> List[Anomaly]
```

**Algorithm:**
- Growth rate = (depth_t2 - depth_t1) / (year_t2 - year_t1)
- Rapid growth threshold: >5% per year
- Risk score: (depth/100)*0.6 + (growth_rate/10)*0.3 + location*0.1

**Testing:**
- Property test: Growth rate calculations
- Property test: Rapid growth identification
- Unit tests: Risk scoring

---

### Phase 2: Regulatory Compliance (Tasks 10-13)
**Estimated Time: 1 week**

#### Task 11: Inspection Interval Calculator
**Priority: HIGH** | **Complexity: Medium**

Components to build:
```python
# src/compliance/interval_calculator.py
class InspectionIntervalCalculator:
    def calculate_time_to_critical(current_depth, growth_rate) -> float
    def apply_safety_factor(time_to_critical, factor=0.5) -> float
    def apply_regulatory_maximum(interval, is_hca) -> float
    def calculate_inspection_interval(anomaly, growth_rate) -> InspectionInterval
    def determine_interval_basis(interval, time_to_critical, is_hca) -> str
```

**Algorithm:**
- Time to critical = (80 - current_depth) / growth_rate
- Safety factor: 50%
- HCA max: 5 years, Non-HCA max: 7 years
- Depth overrides: 3 years for >60%, 5 years for >40%

**Testing:**
- Property test: Safety factor application
- Property test: Regulatory maximums
- Unit tests: Edge cases (zero/negative growth)

---

#### Task 13: Compliance Report Generator
**Priority: HIGH** | **Complexity: Medium**

Components to build:
```python
# src/compliance/report_generator.py
class ComplianceReportGenerator:
    def generate_executive_summary(anomalies, risk_scores) -> dict
    def generate_immediate_action_table(anomalies) -> pd.DataFrame
    def generate_risk_distribution_chart(risk_scores) -> Figure
    def generate_growth_rate_analysis(growth_metrics) -> Figure
    def generate_pdf_report(report_data, output_path) -> None
    def add_regulatory_disclaimers() -> str
    def add_regulatory_references() -> str
```

**Features:**
- PDF generation with ReportLab
- Executive summary with counts by risk level
- Immediate action table (sorted by risk score)
- Risk distribution charts (color-coded)
- Growth rate histograms with ASME threshold lines
- Regulatory disclaimers and references

**Testing:**
- Property test: Export field completeness
- Property test: Report summary accuracy
- Unit tests: PDF generation, CSV export

---

### Phase 3: ML & AI Features (Tasks 14-17)
**Estimated Time: 2 weeks**

#### Task 14: ML Growth Prediction
**Priority: MEDIUM** | **Complexity: High**

Components to build:
```python
# src/prediction/feature_engineer.py
class FeatureEngineer:
    def create_features(anomaly, matches) -> np.ndarray
    def calculate_derived_features(anomaly) -> dict

# src/prediction/predictor.py
class GrowthPredictor:
    def train(training_data) -> TrainingResult
    def predict(anomaly, years_ahead) -> Prediction
    def explain_prediction(anomaly, prediction) -> Explanation
```

**Features:**
- XGBoost regression (n_estimators=100, max_depth=6)
- 80/20 train/test split, stratified by feature_type
- R² > 0.80 requirement
- SHAP explanations for feature importance
- Confidence intervals (quantile regression or bootstrap)

**Testing:**
- Property test: Model performance (R² > 0.80)
- Unit tests: Feature engineering

---

#### Task 16: Natural Language Query Engine
**Priority: MEDIUM** | **Complexity: High**

Components to build:
```python
# src/query/parser.py
class NLQueryParser:
    def parse_query(query, context) -> ParsedQuery
    def extract_filters(query) -> List[Filter]
    def extract_aggregations(query) -> List[Aggregation]

# src/query/executor.py
class QueryExecutor:
    def execute_pandas(parsed_query, df) -> pd.DataFrame
    def execute_sql(parsed_query, db) -> pd.DataFrame
    def format_results(results) -> str
```

**Features:**
- LLM-powered query parsing (LangChain)
- Convert NL to Pandas/SQL operations
- Maintain conversation context
- Success rate >= 90%

**Testing:**
- Property test: Query success rate
- Unit tests: Query parsing patterns

---

#### Task 17: Agentic Match Explanation System
**Priority: LOW** | **Complexity: High**

Components to build:
```python
# src/agents/alignment_agent.py
class AlignmentAgent:
    def verify_alignment(match) -> AlignmentVerification
    def explain_distance_correction(match) -> str

# src/agents/matching_agent.py
class MatchingAgent:
    def explain_similarity_score(match) -> str
    def identify_key_factors(match) -> List[str]

# src/agents/validator_agent.py
class ValidatorAgent:
    def validate_match_quality(match) -> ValidationResult
    def identify_issues(match) -> List[Issue]

# src/agents/explainer_agent.py
class ExplainerAgent:
    def synthesize_explanation(match, agent_outputs) -> str
    def format_for_user(explanation) -> str
```

**Features:**
- Multi-agent system using AutoGen
- Agent workflow: Alignment → Matching → Validator → Explainer
- Human-readable explanations with evidence

**Testing:**
- Unit tests: Agent explanations
- Unit tests: Agent coordination

---

### Phase 4: UI & Integration (Tasks 18-22)
**Estimated Time: 2 weeks**

#### Task 18: Streamlit Dashboard
**Priority: HIGH** | **Complexity: Medium**

Components to build:
```python
# src/dashboard/app.py
def main():
    # Multi-page Streamlit app

# src/dashboard/pages/upload.py
def upload_page():
    # File uploader, validation display

# src/dashboard/pages/alignment.py
def alignment_page():
    # Pipeline schematic, metrics

# src/dashboard/pages/matching.py
def matching_page():
    # Side-by-side comparison

# src/dashboard/pages/growth.py
def growth_analysis_page():
    # Growth trends, risk scores

# src/dashboard/pages/compliance.py
def compliance_page():
    # Immediate action counter
    # Regulatory compliance summary
    # Growth rate distribution with thresholds
    # Inspection interval timeline
    # Color-coded risk matrix

# src/dashboard/pages/query.py
def nl_query_page():
    # Query input, results, conversation history
```

**Key Features:**
- **Compliance Page** (NEW):
  - Immediate action counter (large, prominent)
  - Regulatory compliance summary table
  - Growth rate distribution with ASME threshold lines (0.5%, 2%, 5%)
  - Inspection interval timeline chart
  - Regulatory reference footer
  - Color-coded risk matrix (depth vs growth rate)
  - Regulatory color scheme: Red (CRITICAL), Orange (HIGH), Yellow (MODERATE), Green (LOW/ACCEPTABLE)

**Testing:**
- Integration tests: Page navigation, state management

---

#### Task 19: Performance Optimizations
**Priority: MEDIUM** | **Complexity: Medium**

Optimizations:
- Vectorized operations in similarity calculations
- NumPy arrays for efficient data structures
- Caching for intermediate results
- Memory monitoring and chunking for >10K anomalies
- Database query optimization with proper indexes

**Testing:**
- Performance tests: 10K anomalies in <5 minutes
- Performance tests: Query response <1 second

---

#### Task 20: Error Handling
**Priority: MEDIUM** | **Complexity: Low**

Components:
- Try-catch blocks with specific error messages
- Detailed diagnostic logging
- User-friendly error messages in UI
- Data quality warnings (non-blocking)
- Actionable guidance for failures

**Testing:**
- Unit tests: Error scenarios and recovery

---

#### Task 21-22: Final Integration & Testing
**Priority: HIGH** | **Complexity: Medium**

Activities:
- End-to-end integration tests
- Sample data generation
- User documentation
- API documentation
- Performance validation
- All tests passing (unit, property, integration)

---

## Quick Start for Developers

### 1. Set Up Environment
```bash
# Clone and setup
git clone <repo-url>
cd ili-data-alignment-system
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python -c "from src.database import init_database; init_database()"
```

### 2. Run Tests
```bash
# All tests
pytest

# Specific markers
pytest -m unit
pytest -m property
pytest -m integration
```

### 3. Start Implementing
Open `.kiro/specs/ili-data-alignment-system/tasks.md` and start with Task 4.

---

## Key Implementation Notes

### Regulatory Compliance Requirements

**100% Accuracy Required:**
- >80% depth detection (49 CFR 192.933)
- >5%/year growth detection (ASME B31.8S)
- Risk score calculations must be deterministic

**Mandatory Disclaimers:**
All reports and exports must include:
```
REGULATORY DISCLAIMER

This system provides automated analysis per 49 CFR Parts 192/195
and ASME B31.8S-2022 standards. All risk classifications and action
recommendations are computational outputs and MUST be validated by
qualified pipeline integrity engineers before operational decisions.

This tool does not replace engineering judgment or regulatory
compliance obligations. Operators remain responsible for all
regulatory submissions and safety determinations per PHMSA requirements.

For Official Guidance: https://www.phmsa.dot.gov/
```

### Color Scheme (Regulatory-Aligned)
```python
REGULATORY_COLORS = {
    "CRITICAL": "#DC143C",      # Red
    "HIGH": "#FF8C00",          # Orange
    "MODERATE": "#FFD700",      # Yellow
    "LOW": "#90EE90",           # Light Green
    "ACCEPTABLE": "#228B22",    # Dark Green
}
```

### Performance Targets
- Process 10,000 anomalies: <5 minutes
- Query response: <1 second
- Alignment match rate: ≥95%
- Alignment RMSE: ≤10 feet
- Matching precision: ≥90%
- Matching recall: ≥85%
- ML model R²: >0.80

---

## Testing Strategy

### Unit Tests
- Test individual functions and methods
- Focus on edge cases and boundary conditions
- Mock external dependencies

### Property-Based Tests (Hypothesis)
- Test universal properties across all inputs
- Minimum 100 iterations per property
- Reference design document property numbers

### Integration Tests
- Test end-to-end workflows
- Validate data flow through components
- Test UI interactions

### Regulatory Compliance Tests
- **CRITICAL**: 100% accuracy on >80% depth detection
- **CRITICAL**: 100% accuracy on >5%/year growth detection
- Deterministic risk score calculations
- Correct application of safety factors and regulatory maximums

---

## Resources

### Documentation
- **Requirements**: `.kiro/specs/ili-data-alignment-system/requirements.md`
- **Design**: `.kiro/specs/ili-data-alignment-system/design.md`
- **Tasks**: `.kiro/specs/ili-data-alignment-system/tasks.md`

### Regulatory References
- **49 CFR Part 192**: https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-192
- **49 CFR Part 195**: https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-D/part-195
- **ASME B31.8S**: https://www.asme.org/codes-standards/find-codes-standards/b31-8s-managing-system-integrity-gas-pipelines
- **PHMSA Portal**: https://www.phmsa.dot.gov/

### Technology Stack
- **Core**: Python 3.9+, Pandas, NumPy, SciPy
- **Database**: SQLAlchemy, SQLite
- **ML**: XGBoost, SHAP
- **UI**: Streamlit, Plotly
- **AI**: LangChain, AutoGen
- **Testing**: Pytest, Hypothesis
- **Reporting**: ReportLab

---

## Support

For questions or issues:
1. Check the design specifications in `.kiro/specs/`
2. Review this implementation guide
3. Consult the README.md
4. Open an issue on GitHub

---

**Last Updated**: February 7, 2026  
**System Version**: 0.1.0  
**Regulatory Basis**: 49 CFR Parts 192/195 (2026 Edition), ASME B31.8S-2022
