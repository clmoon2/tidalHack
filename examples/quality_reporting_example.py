"""
Example demonstrating comprehensive data quality reporting.

This example shows how to use the QualityReporter to generate
comprehensive quality reports that combine validation results,
summary statistics, and imputation logs.
"""

from src.ingestion.loader import ILIDataLoader
from src.ingestion.validator import DataValidator
from src.ingestion.quality_reporter import QualityReporter
from datetime import datetime
from pathlib import Path


def generate_quality_report_for_file(file_path: str, run_id: str, inspection_date: datetime):
    """
    Generate comprehensive quality report for an ILI data file.
    
    Args:
        file_path: Path to CSV file
        run_id: Inspection run identifier
        inspection_date: Date of inspection
    """
    print(f"\n{'='*80}")
    print(f"Processing: {file_path}")
    print(f"Run ID: {run_id}")
    print(f"{'='*80}\n")
    
    # Step 1: Load and process data
    print("Step 1: Loading and processing data...")
    loader = ILIDataLoader()
    anomalies_df, ref_points_df = loader.load_and_process(
        file_path, run_id, inspection_date
    )
    print(f"  ✓ Loaded {len(anomalies_df)} anomalies and {len(ref_points_df)} reference points")
    
    # Step 2: Validate data
    print("\nStep 2: Validating data...")
    validator = DataValidator()
    
    # Impute missing values (this populates the imputation log)
    anomalies_df = validator.impute_missing_values(anomalies_df)
    
    # Validate schema
    validation_result, validation_report = validator.validate_and_report(anomalies_df)
    
    if validation_result.is_valid:
        print(f"  ✓ Validation passed: {validation_result.valid_count}/{validation_result.record_count} records valid")
    else:
        print(f"  ⚠ Validation issues: {validation_result.invalid_count} invalid records")
    
    # Step 3: Generate comprehensive quality report
    print("\nStep 3: Generating comprehensive quality report...")
    reporter = QualityReporter()
    
    report = reporter.generate_comprehensive_report(
        anomalies_df=anomalies_df,
        ref_points_df=ref_points_df,
        validation_result=validation_result,
        validation_report=validation_report,
        imputation_log=validator.imputation_log,
        run_id=run_id,
        file_path=file_path
    )
    
    print("  ✓ Report generated successfully")
    
    # Step 4: Display report summary
    print("\n" + "="*80)
    print("QUALITY REPORT SUMMARY")
    print("="*80)
    
    summary = report["summary"]
    print(f"\nTotal Records: {summary['total_records']}")
    print(f"  • Anomalies: {summary['anomaly_count']}")
    print(f"  • Reference Points: {summary['reference_point_count']}")
    print(f"  • Validation Status: {summary['validation_status']}")
    print(f"  • Data Quality Score: {summary['data_quality_score']:.1f}/100")
    
    # Display imputation summary
    imputation = report["imputation"]
    if imputation["actions_performed"] > 0:
        print(f"\nImputation Actions: {imputation['actions_performed']}")
        for action in imputation["log"]:
            print(f"  • {action}")
    
    # Display anomaly statistics
    anomalies = report["anomalies"]
    if "depth_statistics" in anomalies and anomalies["depth_statistics"]:
        print("\nDepth Statistics:")
        depth = anomalies["depth_statistics"]
        print(f"  • Range: {depth['min']:.1f}% - {depth['max']:.1f}%")
        print(f"  • Mean: {depth['mean']:.1f}%")
        print(f"  • Critical (>80%): {depth['critical_count']}")
        print(f"  • High (50-80%): {depth['high_count']}")
    
    # Display recommendations
    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  {rec}")
    
    # Step 5: Save reports
    print("\n" + "="*80)
    print("SAVING REPORTS")
    print("="*80)
    
    output_dir = Path("output/quality_reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON report
    json_path = output_dir / f"{run_id}_quality_report.json"
    reporter.save_report_json(report, str(json_path))
    print(f"  ✓ JSON report saved: {json_path}")
    
    # Save text report
    text_path = output_dir / f"{run_id}_quality_report.txt"
    reporter.save_report_text(report, str(text_path))
    print(f"  ✓ Text report saved: {text_path}")
    
    # Display full text report
    print("\n" + "="*80)
    print("FULL TEXT REPORT")
    print("="*80)
    print(reporter.format_report_text(report))
    
    return report


def main():
    """Main function to demonstrate quality reporting."""
    print("="*80)
    print("ILI DATA QUALITY REPORTING EXAMPLE")
    print("="*80)
    
    # Example files to process
    files = [
        ("data/ILIDataV2_2007.csv", "RUN_2007", datetime(2007, 1, 1)),
        ("data/ILIDataV2_2015.csv", "RUN_2015", datetime(2015, 1, 1)),
        ("data/ILIDataV2_2022.csv", "RUN_2022", datetime(2022, 1, 1)),
    ]
    
    reports = []
    
    for file_path, run_id, inspection_date in files:
        try:
            report = generate_quality_report_for_file(file_path, run_id, inspection_date)
            reports.append(report)
        except FileNotFoundError:
            print(f"\n⚠ File not found: {file_path}")
            print("  Skipping this file...")
        except Exception as e:
            print(f"\n❌ Error processing {file_path}:")
            print(f"  {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary of all reports
    if reports:
        print("\n" + "="*80)
        print("SUMMARY OF ALL REPORTS")
        print("="*80)
        
        for i, report in enumerate(reports, 1):
            metadata = report["metadata"]
            summary = report["summary"]
            print(f"\n{i}. {metadata['run_id']}")
            print(f"   Quality Score: {summary['data_quality_score']:.1f}/100")
            print(f"   Anomalies: {summary['anomaly_count']}")
            print(f"   Reference Points: {summary['reference_point_count']}")
            print(f"   Status: {summary['validation_status']}")
    
    print("\n" + "="*80)
    print("QUALITY REPORTING COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
