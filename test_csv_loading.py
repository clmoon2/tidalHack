"""
Quick test script to verify CSV loading works with the provided data.
"""

from src.ingestion.loader import ILIDataLoader
from datetime import datetime
import json

def test_load_csv_files():
    """Test loading all three CSV files"""
    
    loader = ILIDataLoader()
    
    # Test files
    files = [
        ("data/ILIDataV2_2007.csv", "RUN_2007", datetime(2007, 1, 1)),
        ("data/ILIDataV2_2015.csv", "RUN_2015", datetime(2015, 1, 1)),
        ("data/ILIDataV2_2022.csv", "RUN_2022", datetime(2022, 1, 1)),
    ]
    
    for file_path, run_id, inspection_date in files:
        print(f"\n{'='*60}")
        print(f"Loading: {file_path}")
        print(f"Run ID: {run_id}")
        print(f"{'='*60}")
        
        try:
            # Load and process
            anomalies_df, ref_points_df = loader.load_and_process(
                file_path, run_id, inspection_date
            )
            
            # Generate summary
            summary = loader.generate_summary_report(anomalies_df, ref_points_df)
            
            # Print summary
            print(f"\n📊 Summary Report:")
            print(f"  Total Records: {summary['total_records']}")
            print(f"  Anomalies: {summary['anomaly_count']}")
            print(f"  Reference Points: {summary['reference_point_count']}")
            
            print(f"\n🔍 Anomalies by Type:")
            for anom_type, count in summary['anomalies_by_type'].items():
                print(f"    {anom_type}: {count}")
            
            print(f"\n📍 Reference Points by Type:")
            for ref_type, count in summary['reference_points_by_type'].items():
                print(f"    {ref_type}: {count}")
            
            print(f"\n📏 Depth Statistics:")
            print(f"    Min: {summary['depth_range']['min']:.2f}%")
            print(f"    Max: {summary['depth_range']['max']:.2f}%")
            print(f"    Mean: {summary['depth_range']['mean']:.2f}%")
            
            print(f"\n⚠️  Missing Data:")
            print(f"    Clock Position: {summary['missing_clock_position']}")
            print(f"    Length: {summary['missing_length']}")
            print(f"    Width: {summary['missing_width']}")
            
            # Show sample anomalies
            print(f"\n📋 Sample Anomalies (first 3):")
            sample_cols = ['id', 'distance', 'depth_pct', 'length', 'width', 'clock_position', 'feature_type']
            available_cols = [col for col in sample_cols if col in anomalies_df.columns]
            print(anomalies_df[available_cols].head(3).to_string(index=False))
            
            # Show sample reference points
            print(f"\n📍 Sample Reference Points (first 3):")
            ref_cols = ['id', 'distance', 'point_type']
            available_ref_cols = [col for col in ref_cols if col in ref_points_df.columns]
            if len(ref_points_df) > 0:
                print(ref_points_df[available_ref_cols].head(3).to_string(index=False))
            else:
                print("  No reference points found")
            
            print(f"\n✅ Successfully loaded {file_path}")
            
        except Exception as e:
            print(f"\n❌ Error loading {file_path}:")
            print(f"  {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing CSV Loading with ILI Data")
    print("="*60)
    test_load_csv_files()
    print(f"\n{'='*60}")
    print("✅ Testing Complete!")
