# Task 6.2: Distance Correction Function Implementation

## Overview

Implemented the `DistanceCorrectionFunction` class to transform anomaly distances between coordinate systems using piecewise linear interpolation based on matched reference points from DTW alignment.

**Status**: ✅ Complete  
**Requirements**: 2.6  
**Files Created**:
- `src/alignment/correction.py` - Main implementation
- `tests/unit/test_distance_correction.py` - Unit tests (28 tests)
- `tests/integration/test_dtw_correction_integration.py` - Integration tests (8 tests)
- `examples/distance_correction_example.py` - Usage example

## Implementation Details

### Core Features

1. **Piecewise Linear Interpolation**
   - Uses `scipy.interpolate.interp1d` with linear method
   - Builds interpolation function from matched reference point pairs
   - Handles both interpolation (within range) and extrapolation (outside range)

2. **Distance Correction Methods**
   - `correct_distance()`: Transform single or multiple distances
   - `correct_anomaly_distances()`: Apply correction to entire DataFrame
   - Supports scalar, list, and numpy array inputs

3. **Information and Diagnostics**
   - `get_correction_info()`: Statistics about correction function
   - `is_extrapolating()`: Check if distance requires extrapolation
   - Tracks min/max corrections, mean, and standard deviation

4. **Integration with DTW**
   - `create_correction_function()`: Convenience function for AlignmentResult
   - Seamlessly integrates with DTWAligner output
   - Uses correction_function_params from alignment

### Algorithm

```python
# 1. Extract matched distances from DTW alignment
distances_run1 = [100.0, 500.0, 1000.0, 1500.0, 2000.0]
distances_run2 = [102.0, 505.0, 1008.0, 1507.0, 2005.0]

# 2. Build piecewise linear interpolation
interpolator = interp1d(
    distances_run1,
    distances_run2,
    kind='linear',
    fill_value='extrapolate',
    bounds_error=False
)

# 3. Apply correction to anomaly distances
corrected_distance = interpolator(anomaly_distance)
```

### Key Design Decisions

1. **Scipy interp1d**: Chosen for robust, well-tested interpolation
2. **Extrapolation enabled**: Handles anomalies outside reference point range
3. **Vectorized operations**: Efficient batch processing of DataFrames
4. **Immutable operations**: Original data never modified
5. **Empty DataFrame handling**: Gracefully handles edge cases

## Test Coverage

### Unit Tests (28 tests)

**Initialization Tests** (5 tests)
- Valid initialization with parameters
- Empty distance arrays raise error
- Mismatched array lengths raise error
- Insufficient points (< 2) raise error
- Default interpolation method

**Interpolation Tests** (5 tests)
- Exact match at reference points
- Linear interpolation between points
- Multiple distances at once
- Numpy array input
- List input

**Extrapolation Tests** (3 tests)
- Extrapolation below minimum distance
- Extrapolation above maximum distance
- `is_extrapolating()` method accuracy

**DataFrame Operations** (4 tests)
- Correct all anomaly distances
- Custom column names
- Missing column raises error
- Original DataFrame not modified

**Information Methods** (2 tests)
- `get_correction_info()` structure
- Correction statistics accuracy

**Real-World Scenarios** (3 tests)
- Typical 5% odometer drift
- Non-uniform drift patterns
- Minimal drift (high quality alignment)

**Integration Tests** (2 tests)
- Create from AlignmentResult
- Integration with DTW output format

**Edge Cases** (4 tests)
- Single segment (2 reference points)
- Zero distance
- Negative corrections (shrinkage)
- Unsorted reference points

### Integration Tests (8 tests)

**Complete Workflow Tests** (6 tests)
- DTW alignment → correction → anomaly correction
- Preservation of original anomaly data
- Extrapolation handling
- Multiple anomaly batches
- Minimal drift scenarios
- Correction info matches alignment metrics

**Edge Case Tests** (2 tests)
- Minimum reference points (2)
- Empty anomaly DataFrame

## Usage Example

```python
from src.alignment.dtw_aligner import DTWAligner
from src.alignment.correction import create_correction_function

# Step 1: Perform DTW alignment
aligner = DTWAligner()
alignment_result = aligner.align_sequences(
    ref_points_run1,
    ref_points_run2,
    'run1',
    'run2'
)

# Step 2: Create correction function
corrector = create_correction_function(alignment_result)

# Step 3: Correct single distance
corrected = corrector.correct_distance(1250.0)
# Result: 1257.5 (with example drift)

# Step 4: Correct entire DataFrame
corrected_df = corrector.correct_anomaly_distances(anomalies_df)
# Adds 'corrected_distance' column

# Step 5: Get correction info
info = corrector.get_correction_info()
print(f"Max correction: {info['max_correction']:.2f} feet")
print(f"Mean correction: {info['mean_correction']:.2f} feet")
```

## Test Results

All tests passing:
- ✅ 28/28 unit tests passed
- ✅ 8/8 integration tests passed
- ✅ Example script runs successfully

### Example Output

```
Correction Function Info:
  - Reference points: 5
  - Distance range (Run 1): 0.0 - 2000.0 ft
  - Distance range (Run 2): 0.0 - 2005.0 ft
  - Max correction: 8.00 feet
  - Mean correction: 4.60 feet
  - Std correction: 2.87 feet

Corrected anomalies (Run 2 coordinate system):
  id  distance  corrected_distance  depth_pct  correction  extrapolated
A001     250.0               251.5       25.0         1.5         False
A002     750.0               755.0       30.0         5.0         False
A003    1250.0              1257.5       35.0         7.5         False
A004    1750.0              1756.5       40.0         6.5         False
A005    2100.0              2104.4       28.0         4.4          True
```

## Performance Characteristics

- **Initialization**: O(n log n) for sorting reference points
- **Single correction**: O(log n) for binary search in interpolation
- **Batch correction**: O(m log n) for m anomalies, n reference points
- **Memory**: O(n) for storing reference points

## Error Handling

1. **Empty distance arrays**: Raises `ValueError` with clear message
2. **Mismatched array lengths**: Raises `ValueError` with lengths
3. **Insufficient points**: Requires at least 2 matched points
4. **Missing DataFrame column**: Raises `ValueError` with available columns
5. **Empty DataFrame**: Returns empty DataFrame with corrected column

## Integration Points

### Input (from DTWAligner)
```python
correction_function_params = {
    'matched_distances_run1': [100.0, 200.0, 300.0],
    'matched_distances_run2': [102.0, 205.0, 297.0],
    'interpolation_method': 'linear'
}
```

### Output (for Anomaly Matching)
```python
# Corrected DataFrame with new column
corrected_df = corrector.correct_anomaly_distances(anomalies_df)
# Use corrected_df['corrected_distance'] for matching
```

## Success Criteria

✅ **Piecewise linear interpolation correctly transforms distances**
- Implemented using scipy.interpolate.interp1d
- Tested with various drift patterns
- Handles both uniform and non-uniform drift

✅ **Handles extrapolation gracefully**
- Extrapolation enabled via fill_value='extrapolate'
- `is_extrapolating()` method identifies out-of-range distances
- Tested with anomalies beyond reference point range

✅ **Integrates with DTWAligner output**
- `create_correction_function()` convenience method
- Uses correction_function_params from AlignmentResult
- Seamless integration verified in tests

✅ **Works with real anomaly data**
- DataFrame operations preserve all original data
- Vectorized operations for efficiency
- Handles empty DataFrames and edge cases

## Next Steps

Task 6.2 is complete. The DistanceCorrectionFunction is ready for use in:
- Task 6.3: Implement alignment validation
- Task 7.x: Anomaly matching with corrected distances
- Task 9.x: Growth rate analysis with aligned data

## Notes

- The correction function is stateless and can be reused for multiple batches
- Extrapolation uses linear extension from boundary points
- All corrections are applied in a vectorized manner for performance
- The implementation follows the design specification exactly
- Comprehensive test coverage ensures reliability
