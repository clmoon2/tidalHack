"""
Agentic Match Explanation Example
==================================

Demonstrates the multi-agent system for explaining anomaly matches.

Features:
1. Alignment validation (Task 6.3)
2. Multi-agent match explanation (Task 17)

Author: ILI Data Alignment System
Date: 2024
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.loader import ILIDataLoader
from src.alignment.dtw_aligner import DTWAligner
from src.alignment.correction import DistanceCorrection
from src.alignment.validator import AlignmentValidator
from src.matching.matcher import AnomalyMatcher
from src.agents.match_explainer import MatchExplainerSystem


def main():
    """Run agentic explanation example."""
    
    print("=" * 80)
    print("AGENTIC MATCH EXPLANATION SYSTEM DEMO")
    print("=" * 80)
    print()
    
    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY not found in environment")
        print("Please set your Google API key in .env file")
        return
    
    # Step 1: Load data
    print("Step 1: Loading inspection data...")
    loader = ILIDataLoader()
    
    run1 = loader.load_csv("data/sample_run_2020.csv", "RUN_2020")
    run2 = loader.load_csv("data/sample_run_2022.csv", "RUN_2022")
    
    print(f"✅ Loaded {len(run1)} anomalies from Run 2020")
    print(f"✅ Loaded {len(run2)} anomalies from Run 2022")
    print()
    
    # Step 2: Perform alignment
    print("Step 2: Performing DTW alignment...")
    
    ref1 = run1[run1['feature_type'] == 'reference'].copy()
    ref2 = run2[run2['feature_type'] == 'reference'].copy()
    
    aligner = DTWAligner()
    alignment_result = aligner.align(ref1, ref2)
    
    print(f"✅ Alignment complete")
    print(f"  DTW distance: {alignment_result['dtw_distance']:.2f}")
    print(f"  Match rate: {alignment_result['match_rate']:.1%}")
    print(f"  RMSE: {alignment_result['rmse']:.2f} feet")
    print()
    
    # Step 3: Validate alignment (Task 6.3)
    print("Step 3: Validating alignment quality (Task 6.3)...")
    print("-" * 80)
    
    validator = AlignmentValidator(min_match_rate=0.95, max_rmse=10.0)
    validation_result = validator.validate_alignment(
        alignment_result, ref1, ref2
    )
    
    # Print validation report
    report = validator.generate_report(validation_result)
    print(report)
    
    # Step 4: Apply distance correction
    print("\nStep 4: Applying distance correction...")
    corrector = DistanceCorrection()
    corrected_run2 = corrector.correct_distances(run2, ref1, ref2, alignment_result)
    
    avg_correction = abs(corrected_run2['distance_ft'] - run2['distance_ft']).mean()
    print(f"✅ Distance correction applied (avg: {avg_correction:.2f} ft)")
    print()
    
    # Step 5: Perform matching
    print("Step 5: Matching anomalies...")
    
    anom1 = run1[run1['feature_type'] != 'reference'].copy()
    anom2 = corrected_run2[corrected_run2['feature_type'] != 'reference'].copy()
    
    matcher = AnomalyMatcher()
    matches = matcher.match(anom1, anom2, ref1)
    
    matched_count = len([m for m in matches if m['match_type'] == 'matched'])
    match_rate = matched_count / len(anom1) if len(anom1) > 0 else 0
    
    print(f"✅ Matching complete")
    print(f"  Matched: {matched_count}")
    print(f"  Match rate: {match_rate:.1%}")
    print()
    
    # Step 6: Initialize agentic explanation system (Task 17)
    print("Step 6: Initializing multi-agent explanation system (Task 17)...")
    print("-" * 80)
    
    try:
        explainer = MatchExplainerSystem()
        print("✅ Agent system initialized")
        print("  Agents: AlignmentAgent, MatchingAgent, ValidatorAgent, ExplainerAgent")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize agent system: {e}")
        print("\nMake sure you have:")
        print("  1. pip install pyautogen")
        print("  2. GOOGLE_API_KEY set in .env")
        return
    
    # Step 7: Explain top matches
    print("Step 7: Generating agentic explanations for top matches...")
    print("-" * 80)
    print()
    
    # Get top 3 matches
    matched_only = [m for m in matches if m['match_type'] == 'matched']
    top_matches = sorted(matched_only, key=lambda x: x['similarity_score'], reverse=True)[:3]
    
    for i, match in enumerate(top_matches, 1):
        print(f"\n{'=' * 80}")
        print(f"MATCH {i}: {match['anomaly_id_run1']} → {match['anomaly_id_run2']}")
        print(f"Similarity: {match['similarity_score']:.3f}")
        print(f"{'=' * 80}\n")
        
        # Get anomaly data
        anom1_data = anom1[anom1['anomaly_id'] == match['anomaly_id_run1']].iloc[0].to_dict()
        anom2_data = anom2[anom2['anomaly_id'] == match['anomaly_id_run2']].iloc[0].to_dict()
        
        # Generate explanation using multi-agent system
        print("🤖 Agents analyzing match...")
        print()
        
        try:
            explanation = explainer.explain_match(
                anom1_data,
                anom2_data,
                match,
                alignment_info={
                    'match_rate': alignment_result['match_rate'],
                    'rmse': alignment_result['rmse']
                }
            )
            
            # Display explanation
            print("MULTI-AGENT EXPLANATION:")
            print("-" * 80)
            print(explanation['explanation'])
            print()
            
            print(f"Confidence: {explanation['confidence']}")
            print(f"Recommendation: {explanation['recommendation']}")
            
            if explanation['concerns']:
                print("\n⚠️  Concerns:")
                for concern in explanation['concerns']:
                    print(f"  - {concern}")
            
            print()
            print("AGENT ANALYSES:")
            print("-" * 80)
            
            if explanation['alignment_analysis']:
                print("\n🔧 AlignmentAgent:")
                print(explanation['alignment_analysis'][:300] + "..." if len(explanation['alignment_analysis']) > 300 else explanation['alignment_analysis'])
            
            if explanation['similarity_analysis']:
                print("\n📊 MatchingAgent:")
                print(explanation['similarity_analysis'][:300] + "..." if len(explanation['similarity_analysis']) > 300 else explanation['similarity_analysis'])
            
            if explanation['validation_analysis']:
                print("\n✓ ValidatorAgent:")
                print(explanation['validation_analysis'][:300] + "..." if len(explanation['validation_analysis']) > 300 else explanation['validation_analysis'])
            
        except Exception as e:
            print(f"❌ Explanation failed: {e}")
            print("Using fallback explanation...")
            
            # Fallback explanation
            print(f"\nMatch Quality: {'Strong' if match['similarity_score'] >= 0.8 else 'Good' if match['similarity_score'] >= 0.6 else 'Weak'}")
            print(f"Similarity Score: {match['similarity_score']:.3f}")
            print(f"\nKey Factors:")
            print(f"  Distance similarity: {match.get('distance_similarity', 0):.3f}")
            print(f"  Clock similarity: {match.get('clock_similarity', 0):.3f}")
            print(f"  Type match: {match.get('type_similarity', 0):.3f}")
        
        if i < len(top_matches):
            input("\nPress Enter to continue to next match...")
    
    # Summary
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("✅ Task 6.3: Alignment validation implemented and tested")
    print("✅ Task 17: Multi-agent match explanation system implemented")
    print()
    print("Key Features Demonstrated:")
    print("  1. Alignment validation with match rate and RMSE thresholds")
    print("  2. Unmatched reference point diagnostics")
    print("  3. Multi-agent collaboration (AlignmentAgent, MatchingAgent, ValidatorAgent, ExplainerAgent)")
    print("  4. Human-readable match explanations with confidence levels")
    print("  5. Automated concern identification and recommendations")
    print()
    print("The system now provides:")
    print("  - Rigorous alignment quality validation")
    print("  - Intelligent, explainable match reasoning")
    print("  - Confidence-based recommendations")
    print("  - Comprehensive diagnostic information")
    print()


if __name__ == "__main__":
    main()
