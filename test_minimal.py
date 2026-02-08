"""Minimal test"""
print("Starting...")

try:
    print("Importing...")
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    print("Importing loader...")
    from src.ingestion.loader import ILIDataLoader
    
    print("Creating loader...")
    loader = ILIDataLoader()
    
    print("Loading data...")
    run1 = loader.load_csv("data/sample_run_2020.csv", "RUN_2020")
    
    print(f"Success! Loaded {len(run1)} rows")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Done!")
