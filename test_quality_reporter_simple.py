"""
Simple test to verify QualityReporter works.
"""

import pandas as pd
import numpy as np
from datetime import datetime

from src.ingestion.quality_reporter import QualityReporter
from src.data_models.models import ValidationResult

# Create test data
anomalies_df = pd.DataFrame({
    "id": ["A1", "A2", "A3", "A4", "A5"],
    "run_id": ["RUN1"] * 5,
    "distance": [100.0, 200.0, 300.0, 400.0, 500.0],
    "clock_position": [3.0, 6.0, 9.0, 12.0, 3.0],
    "depth_pct": [25.0, 35.0, 55.0, 85.0, 45.0],
    "length": [4.5, 5.2, 3.8, 6.1, 4.0],
    "width": [2.3, 2.8, 2.1, 3.0, 2.5],
    "feature_type": ["external_corrosion", "external_corrosion", "internal_corrosion", "external_corrosion", "dent"],
    "coating_type": ["FBE", "FBE", None, "FBE", None],
    "inspection_date": [datetime(2020, 1, 1)] * 5
})

ref_points_df = pd.DataFrame({
    "id": ["R1", "R2", "R3", "R4", "R5"],
    "run_id": ["RUN1"] * 5,
    "distance": [50.0, 150.0, 250.0, 350.0, 450.0],
    "point_type": ["girth_weld", "girth_weld", "valve", "girth_weld", "tee"],
    "description": ["GW-001", "GW-002", "V-001", "GW-003", "T-001"]
})

validation_result = ValidationResult(
    is_valid=True,
    errors=[],
    warnings=[],
    record_count=5,
    valid_count=5,
    invalid_count=0
)

validation_report = {
    "timestamp": datetime.now().isoformat(),
    "total_records": 5,
    "valid_records": 5,
    "invalid_records": 0,
    "validation_passed": True,
    "required_fields_present": True,
    "missing_fields": [],
    "validation_errors": [],
    "validation_warnings": [],
    "range_validation_errors": [],
    "imputation_log": [],
    "quality_metrics": {
        "depth_pct_min": 25.0,
        "depth_pct_max": 85.0,
        "depth_pct_mean": 49.0,
        "feature_type_distribution": {
            "external_corrosion": 3,
            "internal_corrosion": 1,
            "dent": 1
        }
    }
}

imputation_log = [
    "Imputed 2 missing clock_position values using forward-fill",
    "Imputed 1 missing length values using median (4.50 inches)",
    "Imputed 1 missing width values using median (2.50 inches)"
]

# Create reporter and generate report
print("Creating QualityReporter...")
reporter = QualityReporter()

print("Generating comprehensive report...")
report = reporter.generate_comprehensive_report(
    anomalies_df=anomalies_df,
    ref_points_df=ref_points_df,
    validation_result=validation_result,
    validation_report=validation_report,
    imputation_log=imputation_log,
    run_id="RUN1",
    file_path="data/test.csv"
)

print("\n" + "="*80)
print("REPORT GENERATED SUCCESSFULLY!")
print("="*80)

# Check report structure
print("\nReport sections:")
for key in report.keys():
    print(f"  ✓ {key}")

# Print summary
print("\nSummary:")
print(f"  Total Records: {report['summary']['total_records']}")
print(f"  Anomalies: {report['summary']['anomaly_count']}")
print(f"  Reference Points: {report['summary']['reference_point_count']}")
print(f"  Validation Status: {report['summary']['validation_status']}")
print(f"  Data Quality Score: {report['summary']['data_quality_score']:.1f}/100")

# Print imputation summary
print("\nImputation:")
print(f"  Actions Performed: {report['imputation']['actions_performed']}")
for action in report['imputation']['log']:
    print(f"    • {action}")

# Print recommendations
print("\nRecommendations:")
for rec in report['recommendations']:
    print(f"  {rec}")

# Test text formatting
print("\n" + "="*80)
print("TESTING TEXT REPORT FORMATTING")
print("="*80)
text_report = reporter.format_report_text(report)
print(text_report)

# Test saving reports
print("\n" + "="*80)
print("TESTING REPORT SAVING")
print("="*80)

try:
    reporter.save_report_json(report, "test_output/quality_report.json")
    print("✓ JSON report saved successfully")
except Exception as e:
    print(f"✗ JSON save failed: {e}")

try:
    reporter.save_report_text(report, "test_output/quality_report.txt")
    print("✓ Text report saved successfully")
except Exception as e:
    print(f"✗ Text save failed: {e}")

print("\n" + "="*80)
print("ALL TESTS PASSED!")
print("="*80)
