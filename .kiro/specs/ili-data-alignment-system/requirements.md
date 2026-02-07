# Requirements Document

## Introduction

The ILI Data Alignment & Corrosion Growth Prediction System automates the alignment of In-Line Inspection (ILI) data across multiple pipeline inspection runs to predict corrosion growth patterns and optimize excavation decisions. This system addresses the critical challenge of manual ILI analysis which takes 40+ hours per pipeline segment and leads to costly unnecessary excavations ($50K-$500K each). By combining proven algorithms (Dynamic Time Warping, Hungarian matching, XGBoost) with LLM-augmented capabilities for natural language queries and intelligent explanations, the system aims to reduce excavation costs by 30% while improving inspection accuracy.

## Glossary

- **ILI_System**: The In-Line Inspection Data Alignment & Corrosion Growth Prediction System
- **Anomaly**: A detected defect or feature in the pipeline (corrosion, dent, crack, etc.)
- **Inspection_Run**: A complete ILI survey of a pipeline segment at a specific point in time
- **Reference_Point**: A known physical feature used for alignment (girth weld, valve, tee, etc.)
- **Odometer_Drift**: The cumulative measurement error in ILI tool distance readings (typically ±10%)
- **DTW**: Dynamic Time Warping algorithm for sequence alignment
- **Growth_Rate**: The change in anomaly dimensions (depth, length, width) per unit time
- **Match_Confidence**: A numerical score (0-1) indicating the likelihood that two anomalies are the same defect
- **Clock_Position**: The circumferential location on the pipe (1-12 o'clock notation)
- **NL_Query**: Natural Language Query interface for data exploration
- **RAG_System**: Retrieval-Augmented Generation system for standards documents
- **Agentic_System**: Multi-agent AI system for match explanation and validation
- **MAOP**: Maximum Allowable Operating Pressure for the pipeline
- **HCA**: High Consequence Area - populated areas or environmentally sensitive zones requiring enhanced oversight
- **CFR**: Code of Federal Regulations - federal regulatory standards for pipeline safety
- **ASME_B31_8S**: American Society of Mechanical Engineers standard for managing system integrity of gas pipelines
- **Regulatory_Risk_Score**: Composite score (0-100) based on depth, growth rate, and location factors
- **Immediate_Action**: Regulatory classification requiring response within specified timeframe per 49 CFR 192.933
- **Scheduled_Action**: Regulatory classification requiring planned remediation within assessment interval
- **Inspection_Interval**: Time period until next required inspection based on regulatory requirements and growth projections

## Requirements

### Requirement 1: Data Ingestion and Preprocessing

**User Story:** As a pipeline integrity engineer, I want to upload ILI data files from multiple inspection runs, so that the system can process and standardize the data for analysis.

#### Acceptance Criteria

1. WHEN an engineer uploads Excel files from multiple inspection runs, THE ILI_System SHALL parse each file and extract anomaly records with their attributes (distance, clock position, depth, length, width, feature type)
2. WHEN parsing ILI data, THE ILI_System SHALL validate each record against a defined schema and reject files with critical validation errors
3. WHEN ILI data contains missing values in non-critical fields, THE ILI_System SHALL apply appropriate imputation strategies and log the imputation actions
4. WHEN ILI data contains clock positions in different formats, THE ILI_System SHALL standardize all clock positions to a consistent numeric format (1-12)
5. WHEN ILI data contains measurements in different units, THE ILI_System SHALL convert all measurements to a standard unit system (feet for distance, inches for dimensions, percentage for depth)
6. WHEN extracting reference points from ILI data, THE ILI_System SHALL identify and catalog all girth welds, valves, and tees with their odometer readings
7. WHEN data ingestion completes, THE ILI_System SHALL generate a summary report showing record counts, validation issues, and data quality metrics

### Requirement 2: Reference Point Alignment Engine

**User Story:** As a pipeline integrity engineer, I want the system to automatically align reference points across inspection runs, so that I can accurately compare anomalies despite odometer drift.

#### Acceptance Criteria

1. WHEN aligning two inspection runs, THE ILI_System SHALL extract girth weld sequences from both runs and apply Dynamic Time Warping to find optimal alignment
2. WHEN DTW alignment completes, THE ILI_System SHALL calculate a distance correction function that maps odometer readings between runs
3. WHEN calculating alignment accuracy, THE ILI_System SHALL achieve greater than 95% successful girth weld matches between runs
4. WHEN measuring alignment precision, THE ILI_System SHALL achieve Root Mean Square Error less than 10 feet for matched reference points
5. WHEN reference points cannot be matched with high confidence, THE ILI_System SHALL flag unmatched points and provide diagnostic information
6. WHEN applying distance correction, THE ILI_System SHALL transform all anomaly distances from the source run to the target run coordinate system

### Requirement 3: Anomaly Matching Engine

**User Story:** As a pipeline integrity engineer, I want the system to match anomalies across inspection runs, so that I can track individual defects over time and calculate growth rates.

#### Acceptance Criteria

1. WHEN matching anomalies between aligned runs, THE ILI_System SHALL calculate a multi-criteria similarity score based on corrected distance, clock position, feature type, depth, length, and width
2. WHEN similarity scores are calculated, THE ILI_System SHALL apply the Hungarian Algorithm to find optimal one-to-one matches that maximize total similarity
3. WHEN evaluating matching performance, THE ILI_System SHALL achieve greater than 90% precision for matched anomalies
4. WHEN evaluating matching performance, THE ILI_System SHALL achieve greater than 85% recall for matched anomalies
5. WHEN an anomaly in a later run has no suitable match in an earlier run, THE ILI_System SHALL classify it as a new anomaly
6. WHEN an anomaly in an earlier run has no match in a later run, THE ILI_System SHALL classify it as potentially repaired or removed
7. WHEN anomalies exhibit merged or split patterns, THE ILI_System SHALL detect and flag these special cases with appropriate confidence scores
8. WHEN matching completes, THE ILI_System SHALL assign a match confidence score to each matched pair

### Requirement 4: Growth Rate Analysis and Risk Scoring

**User Story:** As a pipeline integrity engineer, I want the system to calculate corrosion growth rates and risk scores, so that I can prioritize excavations and maintenance activities.

#### Acceptance Criteria

1. WHEN anomalies are matched across runs, THE ILI_System SHALL calculate depth growth rate as the change in depth percentage divided by time interval in years
2. WHEN anomalies are matched across runs, THE ILI_System SHALL calculate length growth rate and width growth rate using the same methodology
3. WHEN growth rates are calculated, THE ILI_System SHALL identify anomalies with rapid growth defined as greater than 5% depth increase per year
4. WHEN calculating risk scores, THE ILI_System SHALL combine current depth percentage and growth rate into a composite risk metric
5. WHEN risk scores are assigned, THE ILI_System SHALL rank all anomalies by risk score to support excavation prioritization
6. WHEN growth analysis completes, THE ILI_System SHALL generate statistical summaries including mean growth rate, standard deviation, and distribution by feature type

### Requirement 11: Regulatory Compliance - Federal Regulations (49 CFR Parts 192 & 195)

**User Story:** As a pipeline integrity engineer, I want the system to classify anomalies according to federal regulatory thresholds, so that I can ensure compliance with 49 CFR Parts 192 and 195 requirements.

#### Acceptance Criteria

1. WHEN an anomaly has depth greater than 80% of wall thickness, THE ILI_System SHALL classify it as requiring immediate action per 49 CFR 192.933
2. WHEN an anomaly has depth between 50% and 80% of wall thickness, THE ILI_System SHALL classify it as requiring scheduled action
3. WHEN an anomaly has MAOP (Maximum Allowable Operating Pressure) ratio less than 1.1, THE ILI_System SHALL flag it as requiring immediate action
4. WHEN displaying anomaly classifications, THE ILI_System SHALL provide regulatory reference citations (49 CFR section numbers)
5. WHEN generating compliance reports, THE ILI_System SHALL include a count of immediate action items per 49 CFR 192.933
6. WHEN exporting data, THE ILI_System SHALL include regulatory classification fields for all anomalies

### Requirement 12: Regulatory Compliance - ASME B31.8S Growth Rate Standards

**User Story:** As a pipeline integrity engineer, I want the system to evaluate growth rates against ASME B31.8S standards, so that I can identify anomalies exceeding acceptable corrosion rates.

#### Acceptance Criteria

1. WHEN growth rate is less than or equal to 0.5% wall thickness per year, THE ILI_System SHALL classify it as acceptable per ASME B31.8S
2. WHEN growth rate is between 2% and 5% wall thickness per year, THE ILI_System SHALL classify it as moderate risk
3. WHEN growth rate is greater than 5% wall thickness per year, THE ILI_System SHALL classify it as high risk per ASME B31.8S
4. WHEN displaying growth rate analysis, THE ILI_System SHALL show threshold lines at 0.5%, 2%, and 5% per year
5. WHEN generating growth rate distributions, THE ILI_System SHALL annotate ASME B31.8S threshold boundaries
6. WHEN calculating inspection intervals, THE ILI_System SHALL use ASME B31.8S growth rate thresholds as input parameters

### Requirement 13: Multi-Factor Regulatory Risk Scoring

**User Story:** As a pipeline integrity engineer, I want the system to calculate comprehensive risk scores using regulatory factors, so that I can prioritize actions based on compliance requirements.

#### Acceptance Criteria

1. WHEN calculating risk scores, THE ILI_System SHALL assign up to 50 points based on current depth percentage (0-29%=10pts, 30-49%=20pts, 50-79%=35pts, 80-100%=50pts)
2. WHEN calculating risk scores, THE ILI_System SHALL assign up to 30 points based on growth rate (≤0.5%/yr=5pts, 0.5-2%/yr=10pts, 2-5%/yr=20pts, >5%/yr=30pts)
3. WHEN calculating risk scores, THE ILI_System SHALL assign up to 20 points based on location and context factors (HCA status, proximity to welds, coating condition)
4. WHEN risk scores are calculated, THE ILI_System SHALL classify anomalies as CRITICAL (85-100), HIGH (70-84), MODERATE (50-69), LOW (30-49), or ACCEPTABLE (0-29)
5. WHEN displaying risk classifications, THE ILI_System SHALL use regulatory color coding (Red for CRITICAL, Orange for HIGH, Yellow for MODERATE, Green for LOW/ACCEPTABLE)
6. WHEN risk scores change between runs, THE ILI_System SHALL track and display risk level transitions

### Requirement 14: Inspection Interval Calculations

**User Story:** As a pipeline integrity engineer, I want the system to calculate regulatory-compliant inspection intervals, so that I can schedule re-inspections according to federal requirements.

#### Acceptance Criteria

1. WHEN calculating inspection intervals, THE ILI_System SHALL compute time to critical depth based on current depth and growth rate
2. WHEN time to critical is calculated, THE ILI_System SHALL apply a 50% safety factor (inspection interval = 0.5 × time to critical)
3. WHEN the anomaly is in a High Consequence Area (HCA), THE ILI_System SHALL cap inspection interval at 5 years maximum
4. WHEN the anomaly is not in an HCA, THE ILI_System SHALL cap inspection interval at 7 years maximum
5. WHEN growth rate is zero or negative, THE ILI_System SHALL assign the maximum regulatory interval based on HCA status
6. WHEN displaying inspection intervals, THE ILI_System SHALL show the calculation basis (depth-based, growth-based, or regulatory maximum)

### Requirement 15: Regulatory Dashboard Display Requirements

**User Story:** As a pipeline integrity engineer, I want the dashboard to display regulatory compliance information prominently, so that I can quickly assess compliance status.

#### Acceptance Criteria

1. WHEN viewing the dashboard, THE ILI_System SHALL display an immediate action counter showing count of anomalies requiring immediate action per 49 CFR 192.933
2. WHEN viewing the dashboard, THE ILI_System SHALL display a regulatory compliance summary table with counts by risk classification (CRITICAL, HIGH, MODERATE, LOW, ACCEPTABLE)
3. WHEN viewing growth rate distributions, THE ILI_System SHALL overlay threshold lines at ASME B31.8S boundaries (0.5%, 2%, 5% per year)
4. WHEN viewing any dashboard page, THE ILI_System SHALL display a regulatory reference footer citing applicable standards (49 CFR Parts 192/195, ASME B31.8S)
5. WHEN displaying anomalies, THE ILI_System SHALL use regulatory color coding (Red >80% depth, Orange 50-80% depth, Yellow >2%/yr growth, Green acceptable)
6. WHEN viewing inspection intervals, THE ILI_System SHALL display a timeline chart showing scheduled re-inspection dates with regulatory basis

### Requirement 16: Regulatory Export and Reporting

**User Story:** As a pipeline integrity engineer, I want to export data with regulatory compliance fields, so that I can provide documentation for regulatory audits.

#### Acceptance Criteria

1. WHEN exporting to CSV, THE ILI_System SHALL include columns for regulatory classification, risk score, risk level, inspection interval, and regulatory basis
2. WHEN generating PDF compliance reports, THE ILI_System SHALL include executive summary with immediate action count and risk distribution
3. WHEN generating PDF reports, THE ILI_System SHALL include detailed anomaly tables sorted by risk score with regulatory classifications
4. WHEN generating PDF reports, THE ILI_System SHALL include growth rate analysis with ASME B31.8S threshold annotations
5. WHEN generating any export or report, THE ILI_System SHALL include regulatory disclaimers stating that engineering judgment is required
6. WHEN generating reports, THE ILI_System SHALL include references to applicable regulatory standards (49 CFR sections, ASME B31.8S)

### Requirement 17: Regulatory Validation and Testing

**User Story:** As a pipeline integrity engineer, I want the system to accurately apply regulatory thresholds, so that I can trust the compliance classifications.

#### Acceptance Criteria

1. WHEN testing critical depth thresholds, THE ILI_System SHALL achieve 100% accuracy in identifying anomalies greater than 80% depth
2. WHEN testing growth rate thresholds, THE ILI_System SHALL achieve 100% accuracy in identifying anomalies with growth greater than 5% per year
3. WHEN testing risk score calculations, THE ILI_System SHALL produce consistent scores for identical input parameters
4. WHEN testing inspection interval calculations, THE ILI_System SHALL correctly apply safety factors and regulatory maximums
5. WHEN displaying regulatory information, THE ILI_System SHALL include legal disclaimers that the system provides decision support only
6. WHEN regulatory thresholds are updated, THE ILI_System SHALL provide a configuration mechanism to adjust threshold values

### Requirement 5: Natural Language Query Interface

**User Story:** As a pipeline integrity engineer, I want to query the aligned data using natural language, so that I can quickly explore the data without writing SQL or code.

#### Acceptance Criteria

1. WHEN an engineer submits a natural language query, THE ILI_System SHALL parse the query using an LLM to extract intent, entities, and filter criteria
2. WHEN the query is parsed, THE ILI_System SHALL convert the natural language query into executable Pandas operations or SQL statements
3. WHEN the query executes, THE ILI_System SHALL return results in a structured format with relevant columns and visualizations
4. WHEN query results are returned, THE ILI_System SHALL provide a natural language summary of the findings
5. WHEN an engineer asks follow-up questions, THE ILI_System SHALL maintain conversation context to interpret references to previous queries
6. WHEN evaluating query success rate, THE ILI_System SHALL correctly interpret and execute greater than 90% of well-formed natural language queries
7. WHEN a query cannot be interpreted, THE ILI_System SHALL provide helpful error messages and suggest query reformulations

### Requirement 6: Agentic Match Explanation System

**User Story:** As a pipeline integrity engineer, I want to understand why the system matched specific anomalies, so that I can validate the results and build trust in the system.

#### Acceptance Criteria

1. WHEN an engineer requests an explanation for a matched pair, THE Agentic_System SHALL generate a human-readable explanation describing the matching rationale
2. WHEN generating explanations, THE Agentic_System SHALL include specific evidence such as distance proximity, clock position similarity, and dimensional consistency
3. WHEN the Alignment Agent processes a match, THE Agentic_System SHALL verify that distance correction was properly applied
4. WHEN the Matching Agent evaluates similarity, THE Agentic_System SHALL explain which criteria contributed most to the match score
5. WHEN the Validator Agent reviews a match, THE Agentic_System SHALL identify potential issues such as low confidence scores or conflicting evidence
6. WHEN the Explainer Agent synthesizes information, THE Agentic_System SHALL produce explanations that are concise, accurate, and actionable
7. WHEN multiple agents collaborate, THE Agentic_System SHALL coordinate their outputs into a coherent explanation workflow

### Requirement 7: Machine Learning Growth Prediction

**User Story:** As a pipeline integrity engineer, I want the system to predict future corrosion depth, so that I can proactively plan maintenance before defects become critical.

#### Acceptance Criteria

1. WHEN training the prediction model, THE ILI_System SHALL use XGBoost with features including current depth, length, width, growth rate, distance from reference points, and coating type
2. WHEN the model is trained, THE ILI_System SHALL achieve an R-squared score greater than 0.80 on held-out test data
3. WHEN making predictions, THE ILI_System SHALL output predicted depth at a specified future time point with confidence intervals
4. WHEN explaining predictions, THE ILI_System SHALL generate SHAP values to show feature importance for individual predictions
5. WHEN the model encounters anomalies with insufficient historical data, THE ILI_System SHALL flag predictions as low confidence
6. WHEN model performance degrades, THE ILI_System SHALL detect distribution drift and recommend retraining

### Requirement 8: Interactive Dashboard

**User Story:** As a pipeline integrity engineer, I want an interactive web interface to visualize alignment results and explore matched anomalies, so that I can efficiently review and validate the analysis.

#### Acceptance Criteria

1. WHEN an engineer accesses the dashboard, THE ILI_System SHALL display a navigation menu with pages for upload, alignment, matching, growth analysis, and natural language query
2. WHEN viewing the alignment page, THE ILI_System SHALL display a pipeline schematic showing matched reference points and alignment quality metrics
3. WHEN viewing the matching page, THE ILI_System SHALL provide side-by-side comparison of matched anomaly pairs with their attributes
4. WHEN viewing the growth analysis page, THE ILI_System SHALL display growth trend charts, risk score distributions, and rapid growth alerts
5. WHEN interacting with visualizations, THE ILI_System SHALL support filtering, sorting, and drill-down capabilities
6. WHEN analysis is complete, THE ILI_System SHALL provide export functionality to download matched datasets in Excel or CSV format
7. WHEN processing large datasets, THE ILI_System SHALL display progress indicators and estimated completion times

### Requirement 9: Performance and Scalability

**User Story:** As a pipeline integrity engineer, I want the system to process large datasets efficiently, so that I can analyze entire pipeline segments within reasonable time frames.

#### Acceptance Criteria

1. WHEN processing a dataset with 10,000 anomalies, THE ILI_System SHALL complete alignment and matching within 5 minutes
2. WHEN handling multiple concurrent users, THE ILI_System SHALL maintain responsive performance with sub-second query response times
3. WHEN memory usage exceeds thresholds, THE ILI_System SHALL implement chunking strategies to process data in batches
4. WHEN alignment algorithms execute, THE ILI_System SHALL utilize vectorized operations to minimize computational overhead
5. WHEN storing intermediate results, THE ILI_System SHALL use efficient data structures and caching to avoid redundant computation

### Requirement 10: Data Validation and Error Handling

**User Story:** As a pipeline integrity engineer, I want the system to validate data quality and handle errors gracefully, so that I can trust the results and troubleshoot issues effectively.

#### Acceptance Criteria

1. WHEN validating uploaded data, THE ILI_System SHALL check for required fields, valid ranges, and logical consistency
2. WHEN validation errors are detected, THE ILI_System SHALL provide specific error messages indicating which records and fields are problematic
3. WHEN processing encounters an unexpected error, THE ILI_System SHALL log detailed diagnostic information and display a user-friendly error message
4. WHEN data quality issues are identified, THE ILI_System SHALL generate warnings without blocking the analysis workflow
5. WHEN alignment fails due to insufficient reference points, THE ILI_System SHALL provide actionable guidance on data requirements
6. WHEN matching produces low confidence results, THE ILI_System SHALL alert the user and suggest manual review

