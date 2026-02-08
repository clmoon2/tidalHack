"""Debug the complete system demo"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("DEBUGGING COMPLETE SYSTEM DEMO")
print("=" * 80)

# Test each import individually
imports_to_test = [
    ("ILIDataLoader", "from src.ingestion.loader import ILIDataLoader"),
    ("DataValidator", "from src.ingestion.validator import DataValidator"),
    ("QualityReporter", "from src.ingestion.quality_reporter import QualityReporter"),
    ("DTWAligner", "from src.alignment.dtw_aligner import DTWAligner"),
    ("DistanceCorrectionFunction", "from src.alignment.correction import DistanceCorrectionFunction"),
    ("HungarianMatcher", "from src.matching.matcher import HungarianMatcher"),
    ("GrowthAnalyzer", "from src.growth.analyzer import GrowthAnalyzer"),
    ("RiskScorer", "from src.growth.risk_scorer import RiskScorer"),
    ("RegulatoryRiskScorer", "from src.compliance.regulatory_risk_scorer import RegulatoryRiskScorer"),
    ("InspectionIntervalCalculator", "from src.compliance.inspection_interval_calculator import InspectionIntervalCalculator"),
    ("FeatureEngineer", "from src.prediction.feature_engineer import FeatureEngineer"),
    ("GrowthPredictor", "from src.prediction.growth_predictor import GrowthPredictor"),
    ("ComplianceReportGenerator", "from src.reporting.compliance_report_generator import ComplianceReportGenerator"),
    ("DatabaseManager", "from src.database.connection import DatabaseManager"),
    ("ErrorHandler", "from src.utils.error_handler import ErrorHandler"),
]

failed_imports = []

for name, import_stmt in imports_to_test:
    try:
        exec(import_stmt)
        print(f"OK {name}")
    except Exception as e:
        print(f"FAIL {name}: {e}")
        failed_imports.append((name, str(e)))

print("\n" + "=" * 80)
if failed_imports:
    print(f"FAILED IMPORTS: {len(failed_imports)}")
    for name, error in failed_imports:
        print(f"\n{name}:")
        print(f"  {error}")
else:
    print("ALL IMPORTS SUCCESSFUL!")
    print("\nNow testing initialization...")
    
    try:
        from src.ingestion.loader import ILIDataLoader
        from src.utils.error_handler import ErrorHandler
        
        print("\nCreating ErrorHandler...")
        error_handler = ErrorHandler()
        print("OK ErrorHandler created")
        
        print("\nCreating ILIDataLoader...")
        loader = ILIDataLoader()
        print("OK ILIDataLoader created")
        
        print("\nLoading test data...")
        run1 = loader.load_csv("data/sample_run_2020.csv", "RUN_2020")
        print(f"OK Loaded {len(run1)} rows")
        print(f"Columns: {list(run1.columns)}")
        
    except Exception as e:
        print(f"\nFAIL Initialization failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
