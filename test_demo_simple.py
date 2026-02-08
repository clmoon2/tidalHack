"""Simple test of the demo"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("Starting test...")

try:
    from src.ingestion.loader import ILIDataLoader
    print("✅ ILIDataLoader imported")
    
    loader = ILIDataLoader()
    print("✅ Loader created")
    
    run1 = loader.load_csv("data/sample_run_2020.csv", "RUN_2020")
    print(f"✅ Loaded {len(run1)} rows")
    print(f"Columns: {list(run1.columns)[:5]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
