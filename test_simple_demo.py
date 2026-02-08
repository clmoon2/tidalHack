"""Simple test to verify the demo can run."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("STARTING SIMPLE DEMO TEST")
print("=" * 80)

try:
    print("\n1. Testing imports...")
    from src.ingestion.loader import ILIDataLoader
    print("   ✓ ILIDataLoader imported")
    
    from src.ingestion.validator import DataValidator
    print("   ✓ DataValidator imported")
    
    from src.alignment.dtw_aligner import DTWAligner
    print("   ✓ DTWAligner imported")
    
    from src.matching.matcher import HungarianMatcher
    print("   ✓ HungarianMatcher imported")
    
    print("\n2. Loading data...")
    loader = ILIDataLoader()
    df1 = loader.load_csv("data/sample_run_2020.csv", run_id="RUN_2020")
    print(f"   ✓ Loaded {len(df1)} anomalies from 2020")
    
    df2 = loader.load_csv("data/sample_run_2022.csv", run_id="RUN_2022")
    print(f"   ✓ Loaded {len(df2)} anomalies from 2022")
    
    print("\n3. Running DTW alignment...")
    aligner = DTWAligner()
    result = aligner.align(df1, df2)
    print(f"   ✓ Alignment complete - Match rate: {result['match_rate']:.1f}%")
    
    print("\n4. Running matching...")
    matcher = HungarianMatcher()
    matches = matcher.match(df1, df2)
    matched = len([m for m in matches if m['match_id'] is not None])
    print(f"   ✓ Matching complete - {matched} matches found")
    
    print("\n" + "=" * 80)
    print("✅ SIMPLE DEMO TEST PASSED!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
