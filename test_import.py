"""Test if imports work"""
import sys
print("Python version:", sys.version)
print("Python path:", sys.path[:3])

try:
    print("\n1. Testing basic imports...")
    import pandas as pd
    print("✅ pandas imported")
    
    import numpy as np
    print("✅ numpy imported")
    
    print("\n2. Testing src imports...")
    from src.ingestion.loader import DataLoader
    print("✅ DataLoader imported")
    
    from src.alignment.dtw_aligner import DTWAligner
    print("✅ DTWAligner imported")
    
    from src.matching.matcher import AnomalyMatcher
    print("✅ AnomalyMatcher imported")
    
    print("\n3. Testing data loading...")
    loader = DataLoader()
    run1 = loader.load_csv("data/sample_run_2020.csv")
    print(f"✅ Loaded {len(run1)} rows from sample_run_2020.csv")
    
    print("\n✅ All imports and basic functionality working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
