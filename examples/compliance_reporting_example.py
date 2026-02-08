"""
Example: Regulatory compliance reporting.

This script demonstrates:
1. Regulatory risk scoring (49 CFR, ASME B31.8S)
2. Inspection interval calculation
3. PDF compliance report generation
4. CSV export with regulatory fields
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.ingestion.loader import ILIDataLoader
from src.matching.matcher import HungarianMatcher
from src.matching.similarity import SimilarityCalculator
from src.growth.analyzer import GrowthAnalyzer
from src.compliance.regulatory_risk_scorer import RegulatoryRiskScorer
from src.compliance.inspection_interval_calculator import InspectionIntervalCalculator
from src.reporting.compliance_report_generator import ComplianceReportGenerator

print("=" * 80)
print("REGULATORY COMPLIANCE REPORTING EXAMPLE")
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
ref_points_2022 = run_2022['reference_points']

print(f"  2015: {len(anomalies_2015)} anomalies")
print(f"  2022: {len(anomalies_2022)} anomalies")
print()

# Step 2: Match and calculate growth
print("Step 2: Matching anomalies and calculating growth...")
similarity_calc = SimilarityCalculator()
matcher = HungarianMatcher(confidence_threshold=0.6)

match_result = matcher.match_anomalies(
    anomalies_2015,
    anomalies_2022,
    "RUN_2015",
    "RUN_2022",
    similarity_calc
)

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
    match_id = metric.match_id
    parts = match_id.split('_')
    if len(parts) >= 6:
        anomaly_2022_id = f"{parts[3]}_{parts[4]}_{parts[5]}"
        growth_rates[anomaly_2022_id] = metric.depth_growth_rate

print(f"  Matched: {len(match_result['matches'])} pairs")
print(f"  Growth rates calculated: {len(growth_rates)}")
print()

# Step 3: Regulatory risk scoring
print("Step 3: Calculating regulatory risk scores...")
reg_scorer = RegulatoryRiskScorer()

assessments = []
for anomaly in anomalies_2022[:100]:  # Limit to first 100 for demo
    growth_rate = growth_rates.get(anomaly.id, 0.0)
    
    # Simulate HCA status (10% of anomalies in HCA)
    is_hca = (hash(anomaly.id) % 10) == 0
    
    assessment = reg_scorer.score_anomaly(
        anomaly=anomaly,
        growth_rate=growth_rate,
        reference_points=ref_points_2022,
        is_hca=is_hca,
        coating_condition="good"
    )
    
    assessments.append(assessment)

print(f"  Assessed: {len(assessments)} anomalies")
print()

# Step 4: Generate summary
print("Step 4: Generating executive summary...")
report_gen = ComplianceReportGenerator()
summary = report_gen.generate_executive_summary(assessments)

print(f"  Total anomalies: {summary['total_anomalies']}")
print(f"  Immediate action required: {summary['immediate_action_count']}")
print(f"  Critical + High risk: {summary['critical_high_count']}")
print(f"  Mean risk score: {summary['mean_risk_score']:.1f}")
print()

print("  Risk Level Distribution:")
for level, count in summary['risk_level_counts'].items():
    print(f"    {level}: {count}")
print()

print("  CFR Classification:")
for classification, count in summary['cfr_classification_counts'].items():
    print(f"    {classification}: {count}")
print()

print("  ASME Growth Classification:")
for classification, count in summary['asme_growth_counts'].items():
    print(f"    {classification}: {count}")
print()

# Step 5: Immediate action items
print("Step 5: Identifying immediate action items...")
immediate_items = reg_scorer.get_immediate_action_items(assessments)

if immediate_items:
    print(f"  🚨 {len(immediate_items)} anomalies require immediate action:")
    for item in immediate_items[:5]:  # Show first 5
        print(f"    • {item['anomaly_id']}: {item['depth_pct']:.1f}% depth, "
              f"risk score {item['total_risk_score']:.1f}")
else:
    print("  ✅ No immediate action items identified")
print()

# Step 6: Calculate inspection intervals
print("Step 6: Calculating inspection intervals...")
interval_calc = InspectionIntervalCalculator(
    safety_factor=0.5,
    hca_max_years=5.0,
    non_hca_max_years=7.0
)

interval_data = [
    {
        'anomaly_id': a['anomaly_id'],
        'current_depth': a['depth_pct'],
        'growth_rate': a['growth_rate'],
        'is_hca': a['is_hca']
    }
    for a in assessments
]

intervals = interval_calc.batch_calculate(interval_data)

print(f"  Calculated intervals for {len(intervals)} anomalies")
print()

# Show sample intervals
print("  Sample Inspection Intervals:")
for interval in intervals[:5]:
    print(f"    {interval['anomaly_id']}: {interval['interval_years']:.1f} years")
    print(f"      Basis: {interval['basis']}")
    print(f"      Note: {interval['note']}")
print()

# Step 7: Generate charts
print("Step 7: Generating compliance charts...")
output_dir = project_root / "output" / "compliance_reports"
output_dir.mkdir(parents=True, exist_ok=True)

# Risk distribution chart
risk_chart = report_gen.generate_risk_distribution_chart(
    assessments,
    output_path=str(output_dir / "risk_distribution.html")
)
print(f"  ✓ Risk distribution chart: {output_dir / 'risk_distribution.html'}")

# Growth rate analysis chart
growth_chart = report_gen.generate_growth_rate_analysis(
    assessments,
    output_path=str(output_dir / "growth_analysis.html")
)
print(f"  ✓ Growth rate analysis: {output_dir / 'growth_analysis.html'}")
print()

# Step 8: Export CSV
print("Step 8: Exporting compliance data to CSV...")
csv_path = output_dir / "compliance_export.csv"
report_gen.export_csv(assessments, intervals, str(csv_path))
print(f"  ✓ CSV export: {csv_path}")
print()

# Step 9: Generate PDF report
print("Step 9: Generating PDF compliance report...")
pdf_path = output_dir / "compliance_report.pdf"
report_gen.generate_pdf_report(
    assessments=assessments,
    intervals=intervals,
    output_path=str(pdf_path),
    pipeline_name="Sample Pipeline Segment"
)
print(f"  ✓ PDF report: {pdf_path}")
print()

print("=" * 80)
print("✅ COMPLIANCE REPORTING COMPLETE!")
print("=" * 80)
print()
print("Generated Files:")
print(f"  • {output_dir / 'risk_distribution.html'}")
print(f"  • {output_dir / 'growth_analysis.html'}")
print(f"  • {output_dir / 'compliance_export.csv'}")
print(f"  • {output_dir / 'compliance_report.pdf'}")
print()
print("Key Features:")
print("  • 49 CFR Parts 192 & 195 compliance")
print("  • ASME B31.8S growth rate classifications")
print("  • Inspection interval calculations")
print("  • Regulatory color-coded visualizations")
print("  • PDF reports with disclaimers and references")
print()
