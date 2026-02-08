"""
Example: Natural language queries using Google Gemini.

This script demonstrates:
1. Parsing natural language queries
2. Executing queries against anomaly data
3. Generating natural language summaries

IMPORTANT: Set GOOGLE_API_KEY environment variable before running!
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import pandas as pd
from src.ingestion.loader import ILIDataLoader
from src.query.nl_query_parser import NLQueryParser
from src.query.query_executor import QueryExecutor

print("=" * 80)
print("NATURAL LANGUAGE QUERY EXAMPLE")
print("=" * 80)
print()

# Check for API key
if not os.getenv('GOOGLE_API_KEY'):
    print("⚠️  WARNING: GOOGLE_API_KEY environment variable not set!")
    print("   Please set it in your .env file or environment.")
    print("   Example: export GOOGLE_API_KEY='your-key-here'")
    print()
    sys.exit(1)

# Step 1: Load data
print("Step 1: Loading inspection data...")
loader = ILIDataLoader()

data_dir = project_root / "data"
run_2022 = loader.load_csv(str(data_dir / "ILIDataV2_2022.csv"), "RUN_2022")

anomalies_2022 = run_2022['anomalies']

# Convert to DataFrame for querying
df = pd.DataFrame([
    {
        'id': a.id,
        'run_id': a.run_id,
        'feature_type': a.feature_type,
        'depth_pct': a.depth_pct,
        'length_in': a.length_in,
        'width_in': a.width_in,
        'clock_position': a.clock_position,
        'corrected_distance': a.corrected_distance,
        'original_distance': a.original_distance
    }
    for a in anomalies_2022
])

print(f"  Loaded: {len(df)} anomalies")
print()

# Step 2: Initialize query system
print("Step 2: Initializing natural language query system...")
parser = NLQueryParser()
executor = QueryExecutor()
print("  ✓ Query system ready")
print()

# Step 3: Example queries
print("Step 3: Running example queries...")
print()

example_queries = [
    "Show me all metal loss anomalies deeper than 50%",
    "What's the average depth by feature type?",
    "Top 10 deepest anomalies",
    "How many anomalies are at the 12 o'clock position?",
    "Find anomalies between 1000 and 2000 feet with depth over 60%"
]

for i, query in enumerate(example_queries, 1):
    print("-" * 80)
    print(f"Query #{i}: {query}")
    print("-" * 80)
    
    try:
        # Parse query
        parsed = parser.parse_query(query)
        print(f"Parsed structure:")
        print(f"  Filters: {parsed.get('filters', [])}")
        print(f"  Aggregations: {parsed.get('aggregations', [])}")
        print(f"  Sort: {parsed.get('sort', [])}")
        print(f"  Group by: {parsed.get('group_by', [])}")
        print(f"  Limit: {parsed.get('limit', 'None')}")
        print()
        
        # Execute query
        result = executor.execute(df, parsed)
        
        print(f"Results: {result['row_count']} rows")
        print(f"Summary: {result['summary']}")
        print()
        
        # Show sample results
        if result['row_count'] > 0:
            print("Sample results:")
            print(result['results'].head(5).to_string(index=False))
        else:
            print("No results found.")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

print("=" * 80)
print("✅ NATURAL LANGUAGE QUERY EXAMPLE COMPLETE!")
print("=" * 80)
print()
print("Key Features:")
print("  • Natural language understanding using Google Gemini")
print("  • Automatic query parsing and execution")
print("  • Natural language result summaries")
print("  • Conversation context for follow-up questions")
print()
print("Try your own queries by modifying the example_queries list!")
print()
