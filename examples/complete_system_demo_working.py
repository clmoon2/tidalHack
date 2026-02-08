#!/usr/bin/env python
"""
Complete System Demo - Working Version

Demonstrates the core functionality that's actually implemented and working.
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    print("=" * 80)
    print("ILI DATA ALIGNMENT SYSTEM - COMPLETE DEMONSTRATION")
    print("=" * 80)
    
    from datetime import datetime
    import pandas as pd
    
    print("\nStep 1: Loading data...")
    from src.ingestion.loader import ILIDataLoader
    from src.data_models.models import AnomalyRecord
    
    loader = ILIDataLoader()
    
    anomalies_df_2020, ref_2020 = loader.load_and_process(
        "data/sample_run_2020.csv",
        "RUN_2020",
        datetime(2020, 1, 1)
    )
    
    # Convert to AnomalyRecord objects
    anomalies_2020 = []
    for idx, row in anomalies_df_2020.iterrows():
        anomalies_2020.append(AnomalyRecord(
            id=row['id'],
            run_id=row['run_id'],
            distance=float(row['distance']),
            clock_position=float(row['clock_position']),
            depth_pct=float(row['depth_pct']),
            length=float(row['length']),
            width=float(row['width']),
            feature_type=row['feature_type'],
            inspection_date=datetime(2020, 1, 1)
        ))
    
    print(f"  ✓ Loaded {len(anomalies_2020)} anomalies from 2020")
    
    anomalies_df_2022, ref_2022 = loader.load_and_process(
        "data/sample_run_2022.csv",
        "RUN_2022",
        datetime(2022, 1, 1)
    )
    
    # Convert to AnomalyRecord objects
    anomalies_2022 = []
    for idx, row in anomalies_df_2022.iterrows():
        anomalies_2022.append(AnomalyRecord(
            id=row['id'],
            run_id=row['run_id'],
            distance=float(row['distance']),
            clock_position=float(row['clock_position']),
            depth_pct=float(row['depth_pct']),
            length=float(row['length']),
            width=float(row['width']),
            feature_type=row['feature_type'],
            inspection_date=datetime(2022, 1, 1)
        ))
    
    print(f"  ✓ Loaded {len(anomalies_2022)} anomalies from 2022")
    
    print("\nStep 2: Matching anomalies...")
    from src.matching.matcher import HungarianMatcher
    
    matcher = HungarianMatcher()
    result = matcher.match_anomalies(anomalies_2020, anomalies_2022, "RUN_2020", "RUN_2022")
    
    matches = result['matches']
    stats = result['statistics']
    
    print(f"  ✓ Matched {stats['matched']} anomalies ({stats['match_rate']*100:.1f}% match rate)")
    
    print("\nStep 3: Calculating growth rates...")
    from src.growth.risk_scorer import RiskScorer
    
    risk_scorer = RiskScorer()
    growth_results = []
    
    for match in matches:
        # Find the matched anomalies
        anom_2020 = next((a for a in anomalies_2020 if a.id == match.anomaly1_id), None)
        anom_2022 = next((a for a in anomalies_2022 if a.id == match.anomaly2_id), None)
        
        if anom_2020 and anom_2022:
            time_diff = (anom_2022.inspection_date - anom_2020.inspection_date).days / 365.25
            if time_diff > 0:
                depth_change = anom_2022.depth_pct - anom_2020.depth_pct
                growth_rate = depth_change / time_diff
                
                risk_score = risk_scorer.composite_risk(
                    depth_pct=anom_2022.depth_pct,
                    growth_rate=growth_rate,
                    location_factor=0.5  # Default mid-range location factor
                ) * 100  # Convert to 0-100 scale
                
                growth_results.append({
                    'anomaly_id': anom_2022.id,
                    'depth_2020': anom_2020.depth_pct,
                    'depth_2022': anom_2022.depth_pct,
                    'growth_rate': growth_rate,
                    'risk_score': risk_score
                })
    
    print(f"  ✓ Analyzed {len(growth_results)} anomalies")
    
    if growth_results:
        high_risk = len([r for r in growth_results if r['risk_score'] >= 70])
        medium_risk = len([r for r in growth_results if 40 <= r['risk_score'] < 70])
        low_risk = len([r for r in growth_results if r['risk_score'] < 40])
        
        print(f"\n  Risk Distribution:")
        print(f"    - High risk: {high_risk}")
        print(f"    - Medium risk: {medium_risk}")
        print(f"    - Low risk: {low_risk}")
        
        avg_growth = sum(r['growth_rate'] for r in growth_results) / len(growth_results)
        print(f"\n  Average growth rate: {avg_growth:.2f} pp/year")
    
    print("\nStep 4: Saving results...")
    from pathlib import Path
    
    output_dir = Path("output/complete_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if growth_results:
        results_df = pd.DataFrame(growth_results)
        csv_path = output_dir / "growth_analysis.csv"
        results_df.to_csv(csv_path, index=False)
        print(f"  ✓ Results saved to: {csv_path}")
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print(f"\nProcessed {len(anomalies_2020) + len(anomalies_2022)} anomalies")
    print(f"Match rate: {stats['match_rate']*100:.1f}%")
    print(f"Output: {output_dir.absolute()}")
    print("\n")
