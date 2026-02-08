#!/usr/bin/env python
"""
Complete System Demo - WITH AGENTIC WORKFLOW

This demonstrates ALL capabilities including the multi-agent system:
1. Data loading
2. Anomaly matching (rule-based)
3. Growth analysis
4. Agentic match explanations (AI-powered) ✨
5. Results saving

Requires: GOOGLE_API_KEY in .env file
"""

if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    
    # Check for --three-way flag
    if "--three-way" in sys.argv:
        run_three_way_mode()
        sys.exit(0)
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 80)
    print("ILI DATA ALIGNMENT SYSTEM - COMPLETE DEMO WITH AGENTIC AI")
    print("=" * 80)
    
    from datetime import datetime
    import pandas as pd
    
    # Check for API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("\n[!] WARNING: GOOGLE_API_KEY not set in .env file")
        print("    Agentic explanations will be skipped.")
        print("    Set your API key to enable AI-powered match explanations.\n")
        use_agents = False
    else:
        print(f"\n[OK] Google API key found - Agentic AI enabled!")
        print(f"     Key: {api_key[:20]}...{api_key[-4:]}\n")
        use_agents = True
    
    # ========================================================================
    # STEP 1: LOAD DATA
    # ========================================================================
    print("-" * 80)
    print("STEP 1: Loading Data")
    print("-" * 80)
    
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
    
    print(f"  [OK] Loaded {len(anomalies_2020)} anomalies from 2020")
    
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
    
    print(f"  [OK] Loaded {len(anomalies_2022)} anomalies from 2022")
    
    # ========================================================================
    # STEP 2: RULE-BASED MATCHING
    # ========================================================================
    print("\n" + "-" * 80)
    print("STEP 2: Rule-Based Anomaly Matching (Hungarian Algorithm)")
    print("-" * 80)
    
    from src.matching.matcher import HungarianMatcher
    
    matcher = HungarianMatcher()
    result = matcher.match_anomalies(anomalies_2020, anomalies_2022, "RUN_2020", "RUN_2022")
    
    matches = result['matches']
    stats = result['statistics']
    
    print(f"\n  [OK] Matched {stats['matched']} anomalies ({stats['match_rate']*100:.1f}% match rate)")
    print(f"  - High confidence: {stats['high_confidence']}")
    print(f"  - Medium confidence: {stats['medium_confidence']}")
    print(f"  - Low confidence: {stats['low_confidence']}")
    
    # ========================================================================
    # STEP 3: AGENTIC MATCH EXPLANATIONS (AI-POWERED)
    # ========================================================================
    if use_agents and len(matches) > 0:
        print("\n" + "-" * 80)
        print("STEP 3: Agentic Match Explanations (Multi-Agent AI System)")
        print("-" * 80)
        print("\nUsing 4 specialized AI agents:")
        print("  1. AlignmentAgent - Verifies distance correction")
        print("  2. MatchingAgent - Explains similarity scores")
        print("  3. ValidatorAgent - Assesses match quality")
        print("  4. ExplainerAgent - Synthesizes explanations")
        
        try:
            from src.agents.match_explainer import MatchExplainerSystem
            
            explainer = MatchExplainerSystem()
            
            # Get explanations for top 3 matches
            print(f"\nGenerating AI explanations for top {min(3, len(matches))} matches...")
            
            explanations = []
            for i, match in enumerate(matches[:3]):
                print(f"\n  [{i+1}] Analyzing match: {match.anomaly1_id} -> {match.anomaly2_id}")
                
                # Find the anomaly objects
                anom1 = next((a for a in anomalies_2020 if a.id == match.anomaly1_id), None)
                anom2 = next((a for a in anomalies_2022 if a.id == match.anomaly2_id), None)
                
                if anom1 and anom2:
                    # Get AI explanation
                    explanation = explainer.explain_match(anom1, anom2, match)
                    explanations.append(explanation)
                    
                    print(f"      Confidence: {explanation['confidence']}")
                    print(f"      Summary: {explanation['explanation'][:100]}...")
            
            print(f"\n  [OK] Generated {len(explanations)} AI-powered explanations")
            
            # Show detailed explanation for first match
            if explanations:
                print("\n" + "-" * 80)
                print("DETAILED AI EXPLANATION - Match #1")
                print("-" * 80)
                exp = explanations[0]
                print(f"\nConfidence Level: {exp['confidence']}")
                print(f"\nExplanation:\n{exp['explanation']}")
                print(f"\nRecommendation:\n{exp['recommendation']}")
                if exp['concerns']:
                    print(f"\nConcerns:\n" + "\n".join(f"  - {c}" for c in exp['concerns']))
                print("-" * 80)
        
        except Exception as e:
            print(f"\n  [!]  Agentic explanations failed: {str(e)}")
            print("     Continuing with standard analysis...")
    
    elif not use_agents:
        print("\n" + "-" * 80)
        print("STEP 3: Agentic Match Explanations - SKIPPED")
        print("-" * 80)
        print("  Set GOOGLE_API_KEY in .env to enable AI-powered explanations")
    
    # ========================================================================
    # STEP 4: GROWTH ANALYSIS
    # ========================================================================
    print("\n" + "-" * 80)
    print("STEP 4: Growth Analysis & Risk Scoring")
    print("-" * 80)
    
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
                    location_factor=0.5
                ) * 100
                
                growth_results.append({
                    'anomaly_id': anom_2022.id,
                    'depth_2020': anom_2020.depth_pct,
                    'depth_2022': anom_2022.depth_pct,
                    'growth_rate': growth_rate,
                    'risk_score': risk_score,
                    'match_confidence': match.confidence
                })
    
    print(f"\n  [OK] Analyzed {len(growth_results)} anomalies")
    
    if growth_results:
        high_risk = len([r for r in growth_results if r['risk_score'] >= 70])
        medium_risk = len([r for r in growth_results if 40 <= r['risk_score'] < 70])
        low_risk = len([r for r in growth_results if r['risk_score'] < 40])
        
        print(f"\n  Risk Distribution:")
        print(f"    - High risk (>=70): {high_risk}")
        print(f"    - Medium risk (40-69): {medium_risk}")
        print(f"    - Low risk (<40): {low_risk}")
        
        avg_growth = sum(r['growth_rate'] for r in growth_results) / len(growth_results)
        max_growth = max(r['growth_rate'] for r in growth_results)
        
        print(f"\n  Growth Statistics:")
        print(f"    - Average: {avg_growth:.2f} pp/year")
        print(f"    - Maximum: {max_growth:.2f} pp/year")
    
    # ========================================================================
    # STEP 5: SAVE RESULTS
    # ========================================================================
    print("\n" + "-" * 80)
    print("STEP 5: Saving Results")
    print("-" * 80)
    
    output_dir = Path("output/complete_demo_with_agents")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if growth_results:
        results_df = pd.DataFrame(growth_results)
        csv_path = output_dir / "growth_analysis.csv"
        results_df.to_csv(csv_path, index=False)
        print(f"\n  [OK] Growth analysis: {csv_path}")
    
    # Save match details
    if matches:
        match_data = []
        for match in matches:
            match_data.append({
                'match_id': match.id,
                'anomaly_2020': match.anomaly1_id,
                'anomaly_2022': match.anomaly2_id,
                'similarity_score': match.similarity_score,
                'confidence': match.confidence,
                'distance_similarity': match.distance_similarity,
                'clock_similarity': match.clock_similarity,
                'depth_similarity': match.depth_similarity
            })
        
        matches_df = pd.DataFrame(match_data)
        matches_path = output_dir / "matches.csv"
        matches_df.to_csv(matches_path, index=False)
        print(f"  [OK] Match details: {matches_path}")
    
    # Save AI explanations if available
    if use_agents and 'explanations' in locals() and explanations:
        exp_data = []
        for exp in explanations:
            exp_data.append({
                'match_id': exp['match_id'],
                'confidence': exp['confidence'],
                'explanation': exp['explanation'],
                'recommendation': exp['recommendation'],
                'concerns': '; '.join(exp['concerns']) if exp['concerns'] else 'None'
            })
        
        exp_df = pd.DataFrame(exp_data)
        exp_path = output_dir / "ai_explanations.csv"
        exp_df.to_csv(exp_path, index=False)
        print(f"  [OK] AI explanations: {exp_path}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("[DONE] DEMONSTRATION COMPLETE!")
    print("=" * 80)
    
    print(f"\n[STATS] Summary:")
    print(f"  - Total anomalies: {len(anomalies_2020) + len(anomalies_2022)}")
    print(f"  - Matches found: {stats['matched']}")
    print(f"  - Match rate: {stats['match_rate']*100:.1f}%")
    if growth_results:
        print(f"  - Average growth: {avg_growth:.2f} pp/year")
        print(f"  - High risk anomalies: {high_risk}")
    
    if use_agents and 'explanations' in locals():
        print(f"\n[AI] Agentic AI:")
        print(f"  - AI explanations generated: {len(explanations)}")
        print(f"  - Multi-agent system: 4 specialized agents")
    
    print(f"\n[FILES] Output:")
    print(f"  {output_dir.absolute()}")
    
    print("\n[NEXT] Next Steps:")
    print("  1. Review AI explanations in output/complete_demo_with_agents/")
    print("  2. Run: python examples/agentic_explanation_example.py")
    print("  3. Run dashboard: streamlit run src/dashboard/app.py")
    print("  4. Run three-way mode: python examples/complete_system_demo_with_agents.py --three-way")
    
    print("\n" + "=" * 80 + "\n")


def run_three_way_mode():
    """
    Run the full three-way analysis mode (2007 -> 2015 -> 2022).
    
    Uses the ThreeWayAnalyzer to:
    - Load all 3 datasets
    - Match anomalies across runs
    - Build 3-way chains
    - Compute growth and acceleration
    - Generate AI-powered lifecycle narratives
    """
    import sys
    import os
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 80)
    print("ILI DATA ALIGNMENT SYSTEM - THREE-WAY ANALYSIS WITH AGENTIC AI")
    print("=" * 80)
    print("\n15-Year Growth Tracking: 2007 -> 2015 -> 2022")
    print("6 AI Agents: Alignment, Matching, Validator, Explainer, Trend, Projection\n")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    use_agents = bool(api_key)
    
    if use_agents:
        print(f"[OK] Google API key found - Agentic AI enabled!")
    else:
        print("[!] No GOOGLE_API_KEY - using rule-based explanations")
    
    from src.analysis.three_way_analyzer import ThreeWayAnalyzer
    
    data_dir = Path(__file__).parent.parent / "data"
    output_dir = Path(__file__).parent.parent / "output" / "three_way_with_agents"
    
    analyzer = ThreeWayAnalyzer(
        distance_sigma=5.0,
        clock_sigma=1.0,
        confidence_threshold=0.6,
        rapid_growth_threshold=5.0,
        use_agents=use_agents,
        api_key=api_key,
    )
    
    result = analyzer.run_full_analysis(
        data_2007_path=str(data_dir / "ILIDataV2_2007.csv"),
        data_2015_path=str(data_dir / "ILIDataV2_2015.csv"),
        data_2022_path=str(data_dir / "ILIDataV2_2022.csv"),
        top_n_explain=10,
        output_dir=str(output_dir),
    )
    
    # Print executive summary
    print("\n" + "=" * 80)
    print("EXECUTIVE SUMMARY")
    print("=" * 80)
    
    print(f"\n  Analysis ID: {result.analysis_id}")
    print(f"  Status: {result.status}")
    print(f"\n  Datasets:")
    print(f"    2007: {result.total_anomalies_2007:,} anomalies")
    print(f"    2015: {result.total_anomalies_2015:,} anomalies")
    print(f"    2022: {result.total_anomalies_2022:,} anomalies")
    
    print(f"\n  Matching:")
    print(f"    2007->2015: {result.matched_07_15:,} pairs")
    print(f"    2015->2022: {result.matched_15_22:,} pairs")
    print(f"    3-way chains: {result.total_chains:,}")
    
    print(f"\n  Trends:")
    print(f"    Accelerating: {result.accelerating_count:,}")
    print(f"    Stable: {result.stable_count:,}")
    print(f"    Decelerating: {result.decelerating_count:,}")
    
    print(f"\n  Risk:")
    print(f"    Immediate action: {result.immediate_action_count:,}")
    print(f"    Avg growth 07-15: {result.avg_growth_rate_07_15:.3f} pp/yr")
    print(f"    Avg growth 15-22: {result.avg_growth_rate_15_22:.3f} pp/yr")
    
    # Print top 5 chains
    if result.chains:
        print("\n  Top 5 Risk Chains:")
        for i, chain in enumerate(result.chains[:5], 1):
            accel_mark = "^" if chain.is_accelerating else "-" if chain.acceleration < -0.1 else "="
            print(
                f"    {i}. {chain.chain_id} | "
                f"Risk: {chain.risk_score:.3f} | "
                f"Depth: {chain.depth_2007:.0f}% -> {chain.depth_2015:.0f}% -> {chain.depth_2022:.0f}% | "
                f"Trend: {accel_mark}"
            )
    
    # Print top explanations
    if result.explanations:
        print(f"\n  AI Explanations ({len(result.explanations)} generated):")
        for exp in result.explanations[:3]:
            print(f"\n    Chain: {exp.chain_id}")
            print(f"    Trend: {exp.trend_classification} | Urgency: {exp.urgency_level}")
            # Truncate narrative for display
            narrative_short = exp.lifecycle_narrative[:200].replace('\n', ' ')
            print(f"    Narrative: {narrative_short}...")
            print(f"    Recommendation: {exp.recommendation[:100]}...")
    
    print(f"\n  Output files: {output_dir}")
    print("\n" + "=" * 80 + "\n")
