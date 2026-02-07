# Implementation Plan: ILI Data Alignment & Corrosion Growth Prediction System

## Overview

This implementation plan breaks down the ILI Data Alignment system into discrete, executable tasks. The system combines proven algorithms (DTW, Hungarian, XGBoost) with LLM capabilities for pipeline corrosion analysis. Implementation follows a bottom-up approach: core data structures → algorithmic components → ML/LLM features → UI integration.

**Technology Stack**: Python, Pandas, NumPy, SciPy, XGBoost, Pydantic, SQLite, Streamlit, LangChain, AutoGen

## Tasks

- [x] 1. Set up project structure and core dependencies
  - Create directory structure: `src/`, `tests/`, `data/`, `models/`
  - Set up `pyproject.toml` or `requirements.txt` with dependencies: pandas, numpy, scipy, pydantic, sqlalchemy, streamlit, langchain, autogen, xgboost, shap, plotly, openpyxl, reportlab
  - Create `src/__init__.py` and module structure
  - Set up pytest configuration for testing
  - _Requirements: All (foundational)_

- [ ] 2. Implement core data models and validation
  - [x] 2.1 Create Pydantic data models
    - Implement `AnomalyRecord` with validators for clock_position, depth_pct, dimensions
    - Implement `ReferencePoint` model
    - Implement `Match` model with confidence auto-calculation
    - Implement `GrowthMetrics` model with rapid_growth validator
    - Implement `Prediction` model
    - Implement `AlignmentResult` model with match_rate and RMSE validators
    - _Requirements: 1.2, 10.1_

  - [ ]* 2.2 Write property test for data model validation
    - **Property 2: Schema Validation Correctness**
    - **Validates: Requirements 1.2, 10.1, 10.2**

- [ ] 3. Implement database layer
  - [x] 3.1 Create SQLite schema and database utilities
    - Write SQL schema creation script with all tables (inspection_runs, anomalies, reference_points, matches, growth_metrics, predictions)
    - Create database connection manager
    - Implement CRUD operations for each table
    - Add indexes for performance (anomalies by run_id, corrected_distance)
    - _Requirements: All (data persistence)_

  - [ ]* 3.2 Write unit tests for database operations
    - Test table creation, insertions, queries, updates
    - Test foreign key constraints
    - _Requirements: All (data persistence)_

- [ ] 4. Implement data ingestion pipeline
  - [x] 4.1 Create ILIDataLoader class
    - Implement `load_excel()` method with pandas.read_excel
    - Implement `standardize_units()` for distance (miles→feet), dimensions (mm→inches), depth (→percentage)
    - Implement clock position standardization (text formats → numeric 1-12)
    - Implement `extract_reference_points()` to filter girth_weld, valve, tee features
    - _Requirements: 1.1, 1.4, 1.5, 1.6_

  - [x] 4.2 Create DataValidator class
    - Implement `validate_schema()` using Pydantic models
    - Implement `check_required_fields()` and `validate_ranges()`
    - Implement missing value imputation (forward-fill for clock, median for dimensions)
    - Generate validation report with error messages and warnings
    - _Requirements: 1.2, 1.3, 10.1, 10.2_

  - [x] 4.3 Implement data quality reporting
    - Generate summary report with record counts, validation issues, data quality metrics
    - Log all imputation actions
    - _Requirements: 1.7_

  - [ ]* 4.4 Write property test for data transformation
    - **Property 1: Data Transformation Consistency**
    - **Validates: Requirements 1.1, 1.4, 1.5**

  - [ ]* 4.5 Write property test for imputation idempotence
    - **Property 3: Missing Value Imputation Idempotence**
    - **Validates: Requirements 1.3**

  - [ ]* 4.6 Write property test for reference point extraction
    - **Property 4: Reference Point Extraction Completeness**
    - **Validates: Requirements 1.6**

- [x] 5. Checkpoint - Verify data ingestion
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement DTW alignment engine
  - [x] 6.1 Create DTWAligner class
    - Implement `calculate_distance_matrix()` with 10% drift constraint
    - Implement `find_optimal_path()` using dynamic programming
    - Implement DTW algorithm with backtracking
    - Calculate alignment metrics (match_rate, RMSE)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 6.2 Create DistanceCorrectionFunction class
    - Implement piecewise linear interpolation using scipy.interpolate.interp1d
    - Implement `correct_distance()` method with extrapolation handling
    - Apply correction to all anomaly distances
    - _Requirements: 2.6_

  - [ ] 6.3 Implement alignment validation
    - Validate match_rate >= 95%
    - Validate RMSE <= 10 feet
    - Flag unmatched reference points with diagnostic info
    - _Requirements: 2.3, 2.4, 2.5_

  - [ ]* 6.4 Write property test for DTW alignment quality
    - Test that alignment achieves required match_rate and RMSE thresholds
    - **Validates: Requirements 2.3, 2.4**

  - [ ]* 6.5 Write property test for distance correction
    - Test that correction function properly transforms distances
    - **Validates: Requirements 2.6**

- [ ] 7. Implement anomaly matching engine
  - [-] 7.1 Create SimilarityCalculator class
    - Implement `distance_similarity()` using exponential decay (sigma=5 feet)
    - Implement `clock_similarity()` with circular distance (sigma=1.0)
    - Implement `type_similarity()` (exact match)
    - Implement `dimension_similarity()` for depth, length, width
    - Implement `calculate_similarity()` with weighted combination (default weights: dist=0.35, clock=0.20, type=0.15, depth=0.15, length=0.075, width=0.075)
    - _Requirements: 3.1_

  - [ ] 7.2 Create HungarianMatcher class
    - Implement `create_cost_matrix()` (cost = 1 - similarity)
    - Implement `solve_assignment()` using scipy.optimize.linear_sum_assignment
    - Implement `filter_low_confidence()` with threshold=0.6
    - Classify unmatched anomalies as "new" or "repaired_or_removed"
    - Detect merged/split patterns
    - _Requirements: 3.2, 3.5, 3.6, 3.7_

  - [ ] 7.3 Implement match confidence scoring
    - Calculate confidence scores for each match
    - Assign confidence levels (HIGH >= 0.8, MEDIUM >= 0.6, LOW < 0.6)
    - _Requirements: 3.8_

  - [ ]* 7.4 Write property test for matching precision and recall
    - Test that matching achieves >= 90% precision and >= 85% recall
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 7.5 Write property test for unmatched classification
    - Test that unmatched anomalies are correctly classified
    - **Validates: Requirements 3.5, 3.6**

- [ ] 8. Checkpoint - Verify alignment and matching
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement growth rate analysis
  - [ ] 9.1 Create GrowthAnalyzer class
    - Implement `calculate_growth_rate()` for depth, length, width (delta / time_interval_years)
    - Implement `identify_rapid_growth()` with threshold=5.0% per year
    - Generate statistical summaries (mean, std dev, distribution by feature type)
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [ ] 9.2 Create RiskScorer class
    - Implement `composite_risk()` formula: (depth/100)*0.6 + (growth_rate/10)*0.3 + location_factor*0.1
    - Implement `rank_by_risk()` to sort anomalies by risk score
    - Calculate location_factor based on proximity to girth welds
    - _Requirements: 4.4, 4.5_

  - [ ]* 9.3 Write property test for growth rate calculations
    - Test that growth rates are correctly calculated for all dimensions
    - **Validates: Requirements 4.1, 4.2**

  - [ ]* 9.4 Write property test for rapid growth identification
    - Test that anomalies with growth_rate > 5% are flagged
    - **Validates: Requirements 4.3**

  - [ ]* 9.5 Write unit tests for risk scoring
    - Test risk score calculation with various inputs
    - Test ranking functionality
    - _Requirements: 4.4, 4.5_

- [ ] 10. Implement regulatory compliance module
  - [ ] 10.1 Create RegulatoryRiskScorer class
    - Implement `calculate_depth_points()` with thresholds: <30%=10pts, 30-49%=20pts, 50-79%=35pts, ≥80%=50pts
    - Implement `calculate_growth_rate_points()` with thresholds: ≤0.5%=5pts, 0.5-2%=10pts, 2-5%=20pts, >5%=30pts
    - Implement `calculate_location_points()` considering HCA status, proximity to welds, coating condition
    - Implement `calculate_total_risk_score()` summing all point contributions
    - Implement `classify_risk_level()` with thresholds: ≥85=CRITICAL, ≥70=HIGH, ≥50=MODERATE, ≥30=LOW, <30=ACCEPTABLE
    - Implement `classify_cfr_action()` for 49 CFR 192.933 compliance (>80% depth or <1.1 MAOP = immediate action)
    - Implement `classify_asme_growth_rate()` for ASME B31.8S compliance
    - _Requirements: 11.1, 11.2, 11.3, 12.1, 12.2, 12.3, 13.1, 13.2, 13.3, 13.4_

  - [ ]* 10.2 Write property test for regulatory classification accuracy
    - **Property 20: Federal Regulatory Classification Accuracy**
    - **Validates: Requirements 11.1, 11.2, 11.3**

  - [ ]* 10.3 Write property test for ASME growth rate classification
    - **Property 21: ASME B31.8S Growth Rate Classification**
    - **Validates: Requirements 12.1, 12.2, 12.3**

  - [ ]* 10.4 Write property test for risk score calculation
    - **Property 22: Multi-Factor Risk Score Calculation**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4**

  - [ ]* 10.5 Write property test for risk score determinism
    - **Property 23: Risk Score Determinism**
    - **Validates: Requirements 17.3**

  - [ ]* 10.6 Write unit tests for critical threshold detection
    - Test 100% accuracy on >80% depth detection
    - Test 100% accuracy on >5%/yr growth detection
    - **Validates: Requirements 17.1, 17.2**

- [ ] 11. Implement inspection interval calculator
  - [ ] 11.1 Create InspectionIntervalCalculator class
    - Implement `calculate_time_to_critical()` using (critical_threshold - current_depth) / growth_rate
    - Implement `apply_safety_factor()` multiplying time to critical by 0.5
    - Implement `apply_regulatory_maximum()` capping at 5 years for HCA, 7 years for non-HCA
    - Implement `calculate_inspection_interval()` combining all factors
    - Implement `determine_interval_basis()` to explain calculation method
    - Handle zero/negative growth rates appropriately (assign regulatory maximum)
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [ ]* 11.2 Write property test for safety factor application
    - **Property 24: Inspection Interval Safety Factor**
    - **Validates: Requirements 14.2**

  - [ ]* 11.3 Write property test for regulatory maximums
    - **Property 25: Inspection Interval Regulatory Maximums**
    - **Validates: Requirements 14.3, 14.4**

  - [ ]* 11.4 Write unit tests for edge cases
    - Test zero growth rate handling
    - Test negative growth rate handling
    - Test very high growth rates
    - _Requirements: 14.5_

- [ ] 12. Checkpoint - Verify regulatory compliance calculations
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement compliance report generator
  - [ ] 13.1 Create ComplianceReportGenerator class
    - Implement `generate_executive_summary()` with counts by risk level and CFR classification
    - Implement `generate_immediate_action_table()` filtering and sorting by risk score
    - Implement `generate_risk_distribution_chart()` using Plotly with regulatory color scheme
    - Implement `generate_growth_rate_analysis()` with ASME B31.8S threshold lines
    - Implement `add_regulatory_disclaimers()` with required legal text
    - Implement `add_regulatory_references()` citing 49 CFR and ASME B31.8S
    - _Requirements: 16.2, 16.3, 16.4, 16.5, 16.6_

  - [ ] 13.2 Implement PDF report generation
    - Set up ReportLab for PDF creation
    - Create title page with report metadata
    - Add executive summary section
    - Add immediate action items table
    - Add risk distribution charts
    - Add growth rate analysis with threshold annotations
    - Add detailed anomaly tables sorted by risk
    - Add inspection interval recommendations
    - Add regulatory references footer
    - Add legal disclaimers
    - _Requirements: 16.2, 16.3, 16.5, 16.6_

  - [ ] 13.3 Implement CSV export with regulatory fields
    - Add columns: regulatory_classification, risk_score, risk_level, cfr_classification, asme_classification, inspection_interval, interval_basis
    - Include regulatory references in header comments
    - _Requirements: 16.1_

  - [ ]* 13.4 Write property test for export field completeness
    - **Property 27: Regulatory Export Field Completeness**
    - **Validates: Requirements 16.1, 16.2, 16.3**

  - [ ]* 13.5 Write property test for report summary accuracy
    - **Property 28: Compliance Report Summary Accuracy**
    - **Validates: Requirements 16.2**

  - [ ]* 13.6 Write unit tests for report generation
    - Test PDF generation with sample data
    - Test CSV export format
    - Test disclaimer inclusion
    - _Requirements: 16.2, 16.3, 16.5, 16.6_

- [ ] 14. Implement ML growth prediction
  - [ ] 14.1 Create FeatureEngineer class
    - Implement feature extraction: current dimensions, growth rates, distance from reference points, clock position, feature type encoding, coating type encoding, derived ratios
    - Implement one-hot encoding for categorical features
    - _Requirements: 7.1_

  - [ ] 14.2 Create GrowthPredictor class
    - Implement XGBoost model configuration (n_estimators=100, max_depth=6, learning_rate=0.1)
    - Implement `train()` method with 80/20 split, stratified by feature_type
    - Implement early stopping (10 rounds)
    - Calculate evaluation metrics (R², MAE, RMSE)
    - _Requirements: 7.1, 7.2_

  - [ ] 14.3 Implement prediction with confidence intervals
    - Implement `predict()` method with ensemble (0.7*ML + 0.3*linear)
    - Implement confidence interval calculation (quantile regression or bootstrap)
    - Flag low-confidence predictions for insufficient data
    - _Requirements: 7.3, 7.5_

  - [ ] 14.4 Implement SHAP explanations
    - Integrate shap.TreeExplainer
    - Generate feature importance for individual predictions
    - Visualize top 5 contributing features
    - _Requirements: 7.4_

  - [ ] 14.5 Implement model monitoring
    - Detect distribution drift
    - Recommend retraining when performance degrades
    - _Requirements: 7.6_

  - [ ]* 14.6 Write property test for model performance
    - Test that trained model achieves R² > 0.80 on test data
    - **Validates: Requirements 7.2**

  - [ ]* 14.7 Write unit tests for feature engineering
    - Test feature extraction and encoding
    - Test derived feature calculations
    - _Requirements: 7.1_

- [ ] 15. Checkpoint - Verify growth analysis and ML
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement natural language query engine
  - [ ] 16.1 Create NLQueryParser class
    - Implement LLM prompt template for query parsing
    - Implement `parse_query()` to extract filters, aggregations, sort operations
    - Implement JSON response parsing and validation
    - Maintain conversation context for follow-up questions
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ] 16.2 Create QueryExecutor class
    - Implement `execute_pandas()` to build and execute Pandas operations
    - Implement `execute_sql()` for SQL query execution
    - Implement `format_results()` for structured output
    - Generate natural language summary of results using LLM
    - _Requirements: 5.2, 5.3, 5.4_

  - [ ] 16.3 Implement error handling for queries
    - Detect unparseable queries
    - Provide helpful error messages and reformulation suggestions
    - _Requirements: 5.7_

  - [ ]* 16.4 Write property test for query success rate
    - Test that >= 90% of well-formed queries execute correctly
    - **Validates: Requirements 5.6**

  - [ ]* 16.5 Write unit tests for query parsing
    - Test various query patterns (filters, aggregations, sorting)
    - Test context maintenance
    - _Requirements: 5.1, 5.2, 5.5_

- [ ] 17. Implement agentic match explanation system
  - [ ] 17.1 Create agent classes using AutoGen
    - Implement AlignmentAgent for distance correction verification
    - Implement MatchingAgent for similarity score explanation
    - Implement ValidatorAgent for match quality assessment
    - Implement ExplainerAgent for synthesis
    - _Requirements: 6.3, 6.4, 6.5, 6.6_

  - [ ] 17.2 Implement agent workflow orchestration
    - Set up agent communication pipeline
    - Coordinate agent outputs into coherent explanations
    - _Requirements: 6.7_

  - [ ] 17.3 Implement explanation generation
    - Generate human-readable explanations with evidence
    - Include distance proximity, clock position, dimensional consistency
    - Identify potential issues and conflicting evidence
    - _Requirements: 6.1, 6.2_

  - [ ]* 17.4 Write unit tests for agent explanations
    - Test explanation generation for various match scenarios
    - Test agent coordination
    - _Requirements: 6.1, 6.2, 6.7_

- [ ] 18. Implement Streamlit dashboard
  - [ ] 18.1 Create main dashboard structure
    - Set up Streamlit multi-page app
    - Create navigation menu
    - Implement session state management
    - _Requirements: 8.1_

  - [ ] 18.2 Implement upload page
    - Create file uploader for Excel files
    - Create run metadata input form
    - Display validation results and data quality report
    - Show progress indicators
    - _Requirements: 8.1, 8.7_

  - [ ] 18.3 Implement alignment page
    - Create pipeline schematic visualization using Plotly
    - Display matched reference points
    - Show alignment quality metrics (match_rate, RMSE)
    - _Requirements: 8.2_

  - [ ] 18.4 Implement matching page
    - Create side-by-side anomaly comparison view
    - Display similarity scores and confidence levels
    - Implement filtering and sorting controls
    - Highlight differences and similarities
    - _Requirements: 8.3, 8.5_

  - [ ] 18.5 Implement growth analysis page
    - Create growth trend charts (line charts, scatter plots)
    - Display risk score distributions (histograms)
    - Show rapid growth alerts
    - Implement drill-down capabilities
    - _Requirements: 8.4, 8.5_

  - [ ] 18.6 Implement regulatory compliance page
    - Display immediate action counter (large, prominent display)
    - Create regulatory compliance summary table with counts by risk level
    - Display growth rate distribution with ASME B31.8S threshold lines (0.5%, 2%, 5%)
    - Create inspection interval timeline chart
    - Add regulatory reference footer (49 CFR Parts 192/195, ASME B31.8S)
    - Implement color-coded risk matrix (depth vs growth rate)
    - Use regulatory color scheme: Red (CRITICAL), Orange (HIGH), Yellow (MODERATE), Blue (LOW), Green (ACCEPTABLE)
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

  - [ ] 18.7 Implement natural language query page
    - Create query input interface
    - Display results table and visualizations
    - Show conversation history
    - _Requirements: 8.5_

  - [ ] 18.8 Implement export functionality
    - Add download buttons for Excel/CSV/PDF export
    - Export matched datasets with all regulatory fields
    - Include regulatory disclaimers in exports
    - _Requirements: 8.6, 16.1_

  - [ ]* 18.9 Write integration tests for dashboard
    - Test page navigation and state management
    - Test data flow through UI components
    - _Requirements: 8.1-8.7_

- [ ] 19. Implement performance optimizations
  - [ ] 19.1 Optimize alignment and matching algorithms
    - Implement vectorized operations in similarity calculations
    - Use efficient data structures (NumPy arrays)
    - Add caching for intermediate results
    - _Requirements: 9.4, 9.5_

  - [ ] 19.2 Implement chunking for large datasets
    - Add memory usage monitoring
    - Implement batch processing for datasets > 10K anomalies
    - _Requirements: 9.3_

  - [ ] 19.3 Optimize database queries
    - Ensure proper index usage
    - Implement query result caching
    - _Requirements: 9.2_

  - [ ]* 19.4 Write performance tests
    - Test that 10K anomaly dataset completes in < 5 minutes
    - Test query response times < 1 second
    - **Validates: Requirements 9.1, 9.2**

- [ ] 20. Implement comprehensive error handling
  - [ ] 20.1 Add error handling throughout application
    - Implement try-catch blocks with specific error messages
    - Log detailed diagnostic information
    - Display user-friendly error messages in UI
    - _Requirements: 10.3_

  - [ ] 20.2 Implement data quality warnings
    - Generate warnings for non-critical issues
    - Provide actionable guidance for alignment failures
    - Alert users for low-confidence matches
    - _Requirements: 10.4, 10.5, 10.6_

  - [ ]* 20.3 Write unit tests for error handling
    - Test error scenarios and recovery
    - Test warning generation
    - _Requirements: 10.3, 10.4, 10.5, 10.6_

- [ ] 21. Final integration and testing
  - [ ] 21.1 Create end-to-end integration tests
    - Test complete workflow: upload → alignment → matching → growth analysis → prediction
    - Test NL query integration
    - Test agentic explanation integration
    - _Requirements: All_

  - [ ] 21.2 Create sample data and documentation
    - Generate sample ILI Excel files for testing
    - Write user documentation
    - Create API documentation
    - _Requirements: All_

  - [ ] 21.3 Final checkpoint
    - Run all tests (unit, property, integration)
    - Verify all requirements are met
    - Performance validation on realistic datasets
    - _Requirements: All_

- [ ] 22. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property-based tests should run minimum 100 iterations
- Each property test must reference its design document property number
- Unit tests focus on specific examples and edge cases
- Integration tests validate end-to-end workflows
- The system uses Python throughout with scientific computing stack (NumPy, SciPy, Pandas)
- LLM features (NL queries, agentic explanations) require API keys for OpenAI or similar
- Performance requirements: < 5 min for 10K anomalies, < 1 sec query response
- Quality thresholds: 95% alignment match rate, 90% matching precision, 85% matching recall, R² > 0.80 for ML model
- Regulatory compliance: 100% accuracy on critical thresholds (>80% depth, >5%/yr growth)
- Regulatory standards: 49 CFR Parts 192 & 195, ASME B31.8S
- Risk scoring: Multi-factor algorithm with depth (0-50pts), growth rate (0-30pts), location (0-20pts)
- Inspection intervals: 50% safety factor, 5yr max for HCA, 7yr max for non-HCA
- All reports and exports must include regulatory disclaimers and references
- PDF report generation requires ReportLab library
- Regulatory color scheme: Red (CRITICAL/immediate action), Orange (HIGH/scheduled action), Yellow (MODERATE), Blue (LOW), Green (ACCEPTABLE)
