"""
Example demonstrating anomaly matching workflow.

This example shows how to:
1. Load anomalies from two inspection runs
2. Calculate similarity scores
3. Perform optimal matching using Hungarian algorithm
4. Analyze growth rates
5. Calculate risk scores
"""

from datetime import datetime
from src.data_models.models import AnomalyRecord
from src.matching.matcher import HungarianMatcher
from src.matching.similarity import SimilarityCalculator
from src.growth.analyzer import GrowthAnalyzer
from src.growth.risk_scorer import RiskScorer


def create_sample_data():
    """Create sample anomaly data for demonstration."""
    
    # Anomalies from 2020 inspection
    anomalies_2020 = [
        AnomalyRecord(
            id="2020_A1",
            run_id="RUN_2020",
            distance=1000.0,
            clock_position=3.0,
            feature_type="external_corrosion",
            depth_pct=40.0,
            length=10.0,
            width=5.0,
            inspection_date=datetime(2020, 1, 1)
        ),
        AnomalyRecord(
            id="2020_A2",
            run_id="RUN_2020",
            distance=2000.0,
            clock_position=6.0,
            feature_type="external_corrosion",
            depth_pct=30.0,
            length=8.0,
            width=4.0,
            inspection_date=datetime(2020, 1, 1)
        ),
        AnomalyRecord(
            id="2020_A3",
            run_id="RUN_2020",
            distance=3000.0,
            clock_position=9.0,
            feature_type="dent",
            depth_pct=20.0,
            length=12.0,
            width=6.0,
            inspection_date=datetime(2020, 1, 1)
        )
    ]
    
    # Anomalies from 2022 inspection (with growth)
    anomalies_2022 = [
        AnomalyRecord(
            id="2022_A1",
            run_id="RUN_2022",
            distance=1001.0,  # Close to 2020_A1
            clock_position=3.0,
            feature_type="external_corrosion",
            depth_pct=50.0,  # Grown from 40% (rapid growth!)
            length=11.0,
            width=5.5,
            inspection_date=datetime(2022, 1, 1)
        ),
        AnomalyRecord(
            id="2022_A2",
            run_id="RUN_2022",
            distance=2001.0,  # Close to 2020_A2
            clock_position=6.0,
            feature_type="external_corrosion",
            depth_pct=32.0,  # Grown from 30% (slow growth)
            length=8.2,
            width=4.1,
            inspection_date=datetime(2022, 1, 1)
        ),
        AnomalyRecord(
            id="2022_A4",
            run_id="RUN_2022",
            distance=4000.0,  # New anomaly
            clock_position=12.0,
            feature_type="external_corrosion",
            depth_pct=25.0,
            length=7.0,
            width=3.0,
            inspection_date=datetime(2022, 1, 1)
        )
    ]
    
    return anomalies_2020, anomalies_2022


def main():
    """Run the matching example."""
    
    print("=" * 80)
    print("ILI Data Alignment System - Anomaly Matching Example")
    print("=" * 80)
    print()
    
    # Step 1: Create sample data
    print("Step 1: Loading sample anomaly data...")
    anomalies_2020, anomalies_2022 = create_sample_data()
    print(f"  - 2020 inspection: {len(anomalies_2020)} anomalies")
    print(f"  - 2022 inspection: {len(anomalies_2022)} anomalies")
    print()
    
    # Step 2: Initialize matcher
    print("Step 2: Initializing Hungarian matcher...")
    similarity_calc = SimilarityCalculator(
        distance_sigma=5.0,
        clock_sigma=1.0
    )
    matcher = HungarianMatcher(
        similarity_calculator=similarity_calc,
        confidence_threshold=0.6
    )
    print("  - Distance sigma: 5.0 feet")
    print("  - Clock sigma: 1.0 hour")
    print("  - Confidence threshold: 0.6")
    print()
    
    # Step 3: Perform matching
    print("Step 3: Performing optimal matching...")
    result = matcher.match_anomalies(
        anomalies_2020,
        anomalies_2022,
        run1_id="RUN_2020",
        run2_id="RUN_2022"
    )
    print()
    
    # Step 4: Display matching results
    print("Step 4: Matching Results")
    print("-" * 80)
    stats = result['statistics']
    print(f"Total anomalies (2020): {stats['total_run1']}")
    print(f"Total anomalies (2022): {stats['total_run2']}")
    print(f"Matched pairs: {stats['matched']}")
    print(f"Match rate: {stats['match_rate']:.1f}%")
    print(f"  - High confidence: {stats['high_confidence']}")
    print(f"  - Medium confidence: {stats['medium_confidence']}")
    print(f"  - Low confidence: {stats['low_confidence']}")
    print(f"Unmatched (2020): {stats['unmatched_run1']} (repaired or removed)")
    print(f"Unmatched (2022): {stats['unmatched_run2']} (new anomalies)")
    print()
    
    # Display matched pairs
    print("Matched Pairs:")
    for match in result['matches']:
        print(f"  {match.anomaly1_id} <-> {match.anomaly2_id}")
        print(f"    Similarity: {match.similarity_score:.3f} ({match.confidence})")
        print(f"    Components: dist={match.distance_similarity:.3f}, "
              f"clock={match.clock_similarity:.3f}, "
              f"type={match.type_similarity:.3f}")
    print()
    
    # Display unmatched anomalies
    if result['unmatched']['repaired_or_removed']:
        print("Repaired or Removed Anomalies (from 2020):")
        for anom in result['unmatched']['repaired_or_removed']:
            print(f"  {anom.id} at {anom.distance:.0f} ft, {anom.clock_position} o'clock")
        print()
    
    if result['unmatched']['new']:
        print("New Anomalies (in 2022):")
        for anom in result['unmatched']['new']:
            print(f"  {anom.id} at {anom.distance:.0f} ft, {anom.clock_position} o'clock, "
                  f"depth={anom.depth_pct:.1f}%")
        print()
    
    # Step 5: Analyze growth rates
    print("Step 5: Analyzing growth rates...")
    analyzer = GrowthAnalyzer(rapid_growth_threshold=5.0)
    growth_result = analyzer.analyze_matches(
        result['matches'],
        anomalies_2020,
        anomalies_2022,
        time_interval_years=2.0
    )
    print()
    
    # Display growth statistics
    print("Growth Analysis Results")
    print("-" * 80)
    growth_stats = growth_result['statistics']
    print(f"Analyzed matches: {growth_stats['total_matches']}")
    print(f"Rapid growth (>5%/yr): {growth_stats['rapid_growth_count']} "
          f"({growth_stats['rapid_growth_percentage']:.1f}%)")
    print()
    
    print("Depth Growth Statistics:")
    depth_stats = growth_stats['depth_growth']
    print(f"  Mean: {depth_stats['mean']:.2f}% per year")
    print(f"  Median: {depth_stats['median']:.2f}% per year")
    print(f"  Range: {depth_stats['min']:.2f}% to {depth_stats['max']:.2f}% per year")
    print()
    
    # Display rapid growth anomalies
    if growth_result['rapid_growth_anomalies']:
        print("⚠️  RAPID GROWTH ANOMALIES (>5% per year):")
        for anom in growth_result['rapid_growth_anomalies']:
            print(f"  {anom['anomaly_id']}: {anom['depth_growth_rate']:.2f}% per year")
            print(f"    Current depth: {anom['current_depth']:.1f}%")
            print(f"    Location: {anom['distance']:.0f} ft, {anom['clock_position']} o'clock")
        print()
    
    # Step 6: Calculate risk scores
    print("Step 6: Calculating risk scores...")
    risk_scorer = RiskScorer(
        depth_weight=0.6,
        growth_weight=0.3,
        location_weight=0.1
    )
    
    # Score 2022 anomalies
    risk_scores = risk_scorer.rank_by_risk(
        anomalies_2022,
        growth_result['growth_metrics']
    )
    print()
    
    # Display risk rankings
    print("Risk Score Rankings (2022 Anomalies)")
    print("-" * 80)
    for i, score in enumerate(risk_scores, 1):
        print(f"{i}. {score['anomaly_id']}: Risk Score = {score['risk_score']:.3f}")
        print(f"   Depth: {score['depth_pct']:.1f}% (contrib: {score['depth_contribution']:.3f})")
        print(f"   Growth: {score['growth_rate']:.2f}%/yr (contrib: {score['growth_contribution']:.3f})")
        print(f"   Location: factor={score['location_factor']:.2f} (contrib: {score['location_contribution']:.3f})")
    print()
    
    # Identify high-risk anomalies
    high_risk = risk_scorer.get_high_risk_anomalies(
        anomalies_2022,
        growth_result['growth_metrics'],
        threshold=0.5
    )
    
    if high_risk:
        print(f"🚨 HIGH RISK ANOMALIES (risk score ≥ 0.5): {len(high_risk)}")
        for score in high_risk:
            print(f"  {score['anomaly_id']}: {score['risk_score']:.3f}")
    else:
        print("✓ No high-risk anomalies identified (all below 0.5 threshold)")
    print()
    
    print("=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
