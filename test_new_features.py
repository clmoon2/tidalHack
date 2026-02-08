"""
Quick test script for new features.

Tests:
1. Regulatory compliance scoring
2. Inspection interval calculation
3. Compliance report generation
4. ML prediction (if enough data)
5. Natural language queries (if API key set)
6. Error handling
"""

import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("TESTING NEW FEATURES")
print("=" * 80)
print()

# Test 1: Regulatory Compliance
print("Test 1: Regulatory Compliance Scoring")
print("-" * 80)
try:
    from src.compliance.regulatory_risk_scorer import RegulatoryRiskScorer
    from src.data_models.models import Anomaly
    from datetime import datetime
    
    scorer = RegulatoryRiskScorer()
    
    # Create test anomaly
    test_anomaly = Anomaly(
        id="TEST_001",
        run_id="TEST_RUN",
        distance=1000.0,
        corrected_distance=1000.0,
        clock_position=6.0,
        feature_type="metal_loss",
        depth_pct=65.0,
        length_in=10.0,
        width_in=5.0,
        inspection_date=datetime.now()
    )
    
    # Score it
    assessment = scorer.score_anomaly(
        anomaly=test_anomaly,
        growth_rate=3.5,
        reference_points=[],
        is_hca=True
    )
    
    print(f"✅ Regulatory scoring works!")
    print(f"   Anomaly: {assessment['anomaly_id']}")
    print(f"   Risk Score: {assessment['total_risk_score']:.1f}")
    print(f"   Risk Level: {assessment['risk_level']}")
    print(f"   CFR Classification: {assessment['cfr_classification']}")
    print(f"   ASME Classification: {assessment['asme_growth_classification']}")
    print()
    
except Exception as e:
    print(f"❌ Regulatory scoring failed: {e}")
    print()

# Test 2: Inspection Intervals
print("Test 2: Inspection Interval Calculation")
print("-" * 80)
try:
    from src.compliance.inspection_interval_calculator import InspectionIntervalCalculator
    
    calc = InspectionIntervalCalculator()
    
    # Test cases
    test_cases = [
        {"depth": 50.0, "growth": 3.0, "hca": True, "desc": "Moderate depth, moderate growth, HCA"},
        {"depth": 75.0, "growth": 6.0, "hca": False, "desc": "High depth, rapid growth, non-HCA"},
        {"depth": 30.0, "growth": 0.5, "hca": True, "desc": "Low depth, slow growth, HCA"},
    ]
    
    for case in test_cases:
        interval = calc.calculate_inspection_interval(
            current_depth=case["depth"],
            growth_rate=case["growth"],
            is_hca=case["hca"]
        )
        print(f"✅ {case['desc']}")
        print(f"   Interval: {interval['interval_years']:.1f} years")
        print(f"   Basis: {interval['basis']}")
        print()
    
except Exception as e:
    print(f"❌ Interval calculation failed: {e}")
    print()

# Test 3: Report Generation
print("Test 3: Compliance Report Generation")
print("-" * 80)
try:
    from src.reporting.compliance_report_generator import ComplianceReportGenerator
    
    gen = ComplianceReportGenerator()
    
    # Create test assessments
    test_assessments = [
        {
            'anomaly_id': 'TEST_001',
            'depth_pct': 65.0,
            'growth_rate': 3.5,
            'depth_points': 35.0,
            'growth_points': 20.0,
            'location_points': 10.0,
            'total_risk_score': 65.0,
            'risk_level': 'MODERATE',
            'cfr_classification': 'SCHEDULED_ACTION',
            'asme_growth_classification': 'MODERATE_RISK',
            'is_hca': True,
            'coating_condition': 'good'
        },
        {
            'anomaly_id': 'TEST_002',
            'depth_pct': 85.0,
            'growth_rate': 6.5,
            'depth_points': 50.0,
            'growth_points': 30.0,
            'location_points': 10.0,
            'total_risk_score': 90.0,
            'risk_level': 'CRITICAL',
            'cfr_classification': 'IMMEDIATE_ACTION',
            'asme_growth_classification': 'HIGH_RISK',
            'is_hca': True,
            'coating_condition': 'poor'
        }
    ]
    
    # Generate summary
    summary = gen.generate_executive_summary(test_assessments)
    print(f"✅ Report generation works!")
    print(f"   Total anomalies: {summary['total_anomalies']}")
    print(f"   Immediate action: {summary['immediate_action_count']}")
    print(f"   Mean risk score: {summary['mean_risk_score']:.1f}")
    print()
    
    # Generate chart (HTML)
    output_dir = project_root / "output" / "test_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig = gen.generate_risk_distribution_chart(
        test_assessments,
        output_path=str(output_dir / "test_risk_chart.html")
    )
    print(f"✅ Chart generated: {output_dir / 'test_risk_chart.html'}")
    print()
    
except Exception as e:
    print(f"❌ Report generation failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 4: ML Prediction
print("Test 4: ML Prediction (Feature Engineering)")
print("-" * 80)
try:
    from src.prediction.feature_engineer import FeatureEngineer
    from src.data_models.models import Anomaly, ReferencePoint
    from datetime import datetime
    
    engineer = FeatureEngineer()
    
    # Create test data
    test_anomalies = [
        Anomaly(
            id=f"TEST_{i}",
            run_id="TEST_RUN",
            distance=1000.0 + i*10,
            corrected_distance=1000.0 + i*10,
            clock_position=6.0,
            feature_type="metal_loss",
            depth_pct=50.0 + i,
            length_in=10.0,
            width_in=5.0,
            inspection_date=datetime.now()
        )
        for i in range(5)
    ]
    
    test_refs = [
        ReferencePoint(
            id="REF_001",
            run_id="TEST_RUN",
            distance=1000.0,
            corrected_distance=1000.0,
            feature_type="girth_weld"
        )
    ]
    
    # Extract features
    features = engineer.extract_features(test_anomalies, test_refs)
    
    print(f"✅ Feature engineering works!")
    print(f"   Extracted {len(features)} feature sets")
    print(f"   Features: {len(engineer.get_feature_names())} columns")
    print(f"   Sample features: {engineer.get_feature_names()[:5]}")
    print()
    print("   Note: Full ML training requires more data (100+ samples)")
    print("   See examples/ml_prediction_example.py for complete demo")
    print()
    
except Exception as e:
    print(f"❌ Feature engineering failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 5: Natural Language Queries
print("Test 5: Natural Language Queries")
print("-" * 80)

# Check if API key is set
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key or api_key == 'your_api_key_here':
    print("⚠️  GOOGLE_API_KEY not set in .env file")
    print("   Set your API key to test NL queries:")
    print("   1. Edit .env file")
    print("   2. Add: GOOGLE_API_KEY=your_actual_key")
    print("   3. Run: python examples/nl_query_example.py")
    print()
else:
    try:
        from src.query.nl_query_parser import NLQueryParser
        
        parser = NLQueryParser()
        
        # Test query parsing
        test_query = "Show me all metal loss anomalies deeper than 50%"
        parsed = parser.parse_query(test_query)
        
        print(f"✅ Natural language queries work!")
        print(f"   Query: {test_query}")
        print(f"   Parsed filters: {parsed.get('filters', [])}")
        print()
        print("   Run full demo: python examples/nl_query_example.py")
        print()
        
    except Exception as e:
        print(f"❌ NL query failed: {e}")
        print("   This might be an API key issue")
        print()

# Test 6: Error Handling
print("Test 6: Error Handling")
print("-" * 80)
try:
    from src.utils.error_handler import (
        ErrorHandler,
        DataValidationError,
        DataQualityWarning
    )
    
    handler = ErrorHandler()
    
    # Test warning
    warning = DataQualityWarning.low_match_rate(0.85, 0.95)
    if warning:
        print(f"✅ Data quality warnings work!")
        print(f"   Sample warning:")
        print(f"   {warning[:100]}...")
        print()
    
    # Test error handling
    try:
        raise DataValidationError(
            "Test validation error",
            details={'field': 'depth_pct', 'value': -10}
        )
    except DataValidationError as e:
        print(f"✅ Error handling works!")
        print(f"   Error message: {e.message}")
        print(f"   User message: {e.user_message[:80]}...")
        print()
    
except Exception as e:
    print(f"❌ Error handling test failed: {e}")
    print()

# Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()
print("✅ Tests completed! Check results above.")
print()
print("Next Steps:")
print("  1. Run full examples:")
print("     python examples/compliance_reporting_example.py")
print("     python examples/ml_prediction_example.py")
print("     python examples/nl_query_example.py")
print()
print("  2. Run dashboard:")
print("     streamlit run src/dashboard/app.py")
print()
print("  3. Check generated files:")
print("     output/test_reports/test_risk_chart.html")
print()
