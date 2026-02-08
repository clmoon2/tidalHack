"""
Full Pipeline Analysis Example - Real Data (5000+ anomalies)

This example demonstrates the complete workflow using real ILI data:
1. Load data from 2015 and 2022 inspection runs
2. Match anomalies using Hungarian algorithm
3. Analyze growth rates
4. Calculate risk scores
5. Generate comprehensive reports

This processes 1,768 (2015) and 2,636 (2022) anomalies = 4,404 total records
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.loader import ILIDataLoader
from src.data_models.models import AnomalyRecord
from src.matching.matcher import HungarianMatcher
from src.matching.similarity import SimilarityCalculator
from src.growth.analyzer import GrowthAnalyzer
from src.growth.risk_scorer import RiskScorer


def load_real_data(file_path: str, run_id: str, inspection_date: datetime):
    """
    Load real ILI data and convert to AnomalyRecord objects.
    
    Args:
        file_path: Path to CSV file
        run_id: Run identifier
        inspection_date: Inspection date
    
    Returns:
        List of AnomalyRecord objects
    """
    print(f"Loading {file_path}...")
    
    # Load using ILIDataLoader
    loader = ILIDataLoader()
    anomalies_df, ref_points_df = loader.load_and_process(
        file_path, run_id, inspection_date
    )
    
    print(f"  ✓ Loaded {len(anomalies_df)} anomalies")
    print(f"  ✓ Loaded {len(ref_points_df)} reference points")
    
    # Convert to AnomalyRecord objects
    anomalies = []
    for idx, row in anomalies_df.iterrows():
        try:
            anomaly = AnomalyRecord(
                id=f"{run_id}_{idx}",
                run_id=run_id,
                distance=float(row['distance']),
                clock_position=float(row['clock_position']),
                depth_pct=float(row['depth_pct']),
                length=float(row['length']),
                width=float(row['width']),
                feature_type=row['feature_type'],
                inspection_date=inspection_date
            )
            anomalies.append(anomaly)
        except Exception as e:
            print(f"  ⚠ Skipping row {idx}: {e}")
    
    print(f"  ✓ Created {len(anomalies)} AnomalyRecord objects")
    
    return anomalies, ref_points_df


def main():
    """Run full pipeline analysis on real data."""
    
    print("=" * 80)
    print("FULL PIPELINE ANALYSIS - REAL ILI DATA")
    print("=" * 80)
    print()
    
    # File paths
    data_dir = project_root / "data"
    file_2015 = data_dir / "ILIDataV2_2015.csv"
    file_2022 = data_dir / "ILIDataV2_2022.csv"
    
    # Check files exist
    if not file_2015.exists():
        print(f"❌ Error: {file_2015} not found")
        return
    if not file_2022.exists():
        print(f"❌ Error: {file_2022} not found")
        return
    
    # =========================================================================
    # STEP 1: LOAD DATA
    # =========================================================================
    print("STEP 1: LOADING DATA")
    print("-" * 80)
    
    anomalies_2015, ref_points_2015 = load_real_data(
        str(file_2015),
        "RUN_2015",
        datetime(2015, 1, 1)
    )
    
    print()
    
    anomalies_2022, ref_points_2022 = load_real_data(
        str(file_2022),
        "RUN_2022",
        datetime(2022, 1, 1)
    )
    
    print()
    print(f"📊 Total Records: {len(anomalies_2015) + len(anomalies_2022)}")
    print()
    
    # =========================================================================
    # STEP 2: MATCH ANOMALIES
    # =========================================================================
    print("STEP 2: MATCHING ANOMALIES")
    print("-" * 80)
    print("Using Hungarian algorithm for optimal one-to-one matching...")
    print()
    
    # Initialize matcher with optimized parameters for large datasets
    similarity_calc = SimilarityCalculator(
        distance_sigma=5.0,  # 5 feet tolerance
        clock_sigma=1.0      # 1 hour tolerance
    )
    
    matcher = HungarianMatcher(
        similarity_calculator=similarity_calc,
        confidence_threshold=0.6  # Medium confidence minimum
    )
    
    print("⏳ Matching in progress (this may take 30-60 seconds for 4000+ anomalies)...")
    
    import time
    start_time = time.time()
    
    result = matcher.match_anomalies(
        anomalies_2015,
        anomalies_2022,
        "RUN_2015",
        "RUN_2022"
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"✓ Matching complete in {elapsed_time:.1f} seconds")
    print()
    
    # Display matching statistics
    stats = result['statistics']
    print("MATCHING RESULTS:")
    print(f"  Total 2015 anomalies: {stats['total_run1']:,}")
    print(f"  Total 2022 anomalies: {stats['total_run2']:,}")
    print(f"  Matched pairs: {stats['matched']:,}")
    print(f"  Match rate: {stats['match_rate']:.1f}%")
    print()
    print(f"  Confidence Distribution:")
    print(f"    HIGH (≥0.8):   {stats['high_confidence']:,} matches")
    print(f"    MEDIUM (≥0.6): {stats['medium_confidence']:,} matches")
    print(f"    LOW (<0.6):    {stats['low_confidence']:,} matches")
    print()
    print(f"  Unmatched:")
    print(f"    Repaired/Removed (2015): {stats['unmatched_run1']:,}")
    print(f"    New (2022):              {stats['unmatched_run2']:,}")
    print()
    
    # =========================================================================
    # STEP 3: ANALYZE GROWTH
    # =========================================================================
    print("STEP 3: ANALYZING GROWTH RATES")
    print("-" * 80)
    
    # Calculate time interval
    time_interval = 7.0  # 2015 to 2022 = 7 years
    
    print(f"Time interval: {time_interval} years")
    print()
    
    # Initialize analyzer
    analyzer = GrowthAnalyzer(rapid_growth_threshold=5.0)
    
    print("⏳ Calculating growth rates...")
    
    growth_result = analyzer.analyze_matches(
        result['matches'],
        anomalies_2015,
        anomalies_2022,
        time_interval_years=time_interval
    )
    
    print("✓ Growth analysis complete")
    print()
    
    # Display growth statistics
    growth_stats = growth_result['statistics']
    print("GROWTH ANALYSIS RESULTS:")
    print(f"  Analyzed matches: {growth_stats['total_matches']:,}")
    print(f"  Rapid growth (>5%/yr): {growth_stats['rapid_growth_count']:,} ({growth_stats['rapid_growth_percentage']:.1f}%)")
    print()
    
    print("  Depth Growth Statistics:")
    depth_stats = growth_stats['depth_growth']
    print(f"    Mean:   {depth_stats['mean']:.2f}% per year")
    print(f"    Median: {depth_stats['median']:.2f}% per year")
    print(f"    Std Dev: {depth_stats['std_dev']:.2f}% per year")
    print(f"    Range:  {depth_stats['min']:.2f}% to {depth_stats['max']:.2f}% per year")
    print()
    
    # Display rapid growth anomalies
    if growth_result['rapid_growth_anomalies']:
        print(f"⚠️  RAPID GROWTH ANOMALIES (Top 10):")
        rapid_sorted = sorted(
            growth_result['rapid_growth_anomalies'],
            key=lambda x: x['depth_growth_rate'],
            reverse=True
        )[:10]
        
        for i, anom in enumerate(rapid_sorted, 1):
            print(f"  {i}. {anom['anomaly_id']}")
            print(f"     Growth: {anom['depth_growth_rate']:.2f}%/yr | "
                  f"Current depth: {anom['current_depth']:.1f}% | "
                  f"Location: {anom['distance']:.0f} ft @ {anom['clock_position']} o'clock")
    print()
    
    # =========================================================================
    # STEP 4: CALCULATE RISK SCORES
    # =========================================================================
    print("STEP 4: CALCULATING RISK SCORES")
    print("-" * 80)
    
    # Convert reference points to dict format for location factor
    ref_points_list = [
        {'distance': row['distance']}
        for _, row in ref_points_2022.iterrows()
    ]
    
    print("⏳ Scoring anomalies...")
    
    scorer = RiskScorer(
        depth_weight=0.6,
        growth_weight=0.3,
        location_weight=0.1
    )
    
    risk_scores = scorer.rank_by_risk(
        anomalies_2022,
        growth_result['growth_metrics'],
        reference_points=ref_points_list
    )
    
    print("✓ Risk scoring complete")
    print()
    
    # Display top 10 highest risk
    print("RISK SCORE RANKINGS (Top 10):")
    for i, score in enumerate(risk_scores[:10], 1):
        print(f"  {i}. {score['anomaly_id']}")
        print(f"     Risk: {score['risk_score']:.3f} | "
              f"Depth: {score['depth_pct']:.1f}% | "
              f"Growth: {score['growth_rate']:.2f}%/yr | "
              f"Location: {score['location_factor']:.2f}")
    print()
    
    # High risk summary
    high_risk = [s for s in risk_scores if s['risk_score'] >= 0.5]
    critical_risk = [s for s in risk_scores if s['risk_score'] >= 0.7]
    
    print("RISK SUMMARY:")
    print(f"  Critical risk (≥0.7): {len(critical_risk):,} anomalies")
    print(f"  High risk (≥0.5):     {len(high_risk):,} anomalies")
    print(f"  Total scored:         {len(risk_scores):,} anomalies")
    print()
    
    # =========================================================================
    # STEP 5: EXPORT RESULTS
    # =========================================================================
    print("STEP 5: EXPORTING RESULTS")
    print("-" * 80)
    
    output_dir = project_root / "output" / "full_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export matches
    matches_data = []
    for match in result['matches']:
        matches_data.append({
            'Run1_ID': match.anomaly1_id,
            'Run2_ID': match.anomaly2_id,
            'Similarity': match.similarity_score,
            'Confidence': match.confidence,
            'Distance_Sim': match.distance_similarity,
            'Clock_Sim': match.clock_similarity,
            'Type_Sim': match.type_similarity
        })
    
    matches_df = pd.DataFrame(matches_data)
    matches_file = output_dir / "matches_2015_2022.csv"
    matches_df.to_csv(matches_file, index=False)
    print(f"  ✓ Matches exported: {matches_file}")
    
    # Export growth metrics
    growth_data = []
    for gm in growth_result['growth_metrics']:
        growth_data.append({
            'Match_ID': gm.match_id,
            'Time_Interval_Years': gm.time_interval_years,
            'Depth_Growth_Rate': gm.depth_growth_rate,
            'Length_Growth_Rate': gm.length_growth_rate,
            'Width_Growth_Rate': gm.width_growth_rate,
            'Rapid_Growth': gm.is_rapid_growth,
            'Risk_Score': gm.risk_score
        })
    
    growth_df = pd.DataFrame(growth_data)
    growth_file = output_dir / "growth_metrics_2015_2022.csv"
    growth_df.to_csv(growth_file, index=False)
    print(f"  ✓ Growth metrics exported: {growth_file}")
    
    # Export risk scores
    risk_df = pd.DataFrame(risk_scores)
    risk_file = output_dir / "risk_scores_2022.csv"
    risk_df.to_csv(risk_file, index=False)
    print(f"  ✓ Risk scores exported: {risk_file}")
    
    print()
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print()
    print(f"📊 Processed {len(anomalies_2015):,} + {len(anomalies_2022):,} = {len(anomalies_2015) + len(anomalies_2022):,} anomalies")
    print(f"🔗 Matched {stats['matched']:,} anomaly pairs ({stats['match_rate']:.1f}% match rate)")
    print(f"📈 Identified {growth_stats['rapid_growth_count']:,} rapid growth anomalies")
    print(f"🚨 Found {len(high_risk):,} high-risk anomalies requiring attention")
    print()
    print(f"📁 Results saved to: {output_dir}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
