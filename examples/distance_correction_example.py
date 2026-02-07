"""
Example: Distance Correction for ILI Data Alignment

This example demonstrates how to use the DistanceCorrectionFunction
to transform anomaly distances between coordinate systems after DTW alignment.

Requirements: 2.6
"""

import pandas as pd
from src.data_models.models import ReferencePoint
from src.alignment.dtw_aligner import DTWAligner
from src.alignment.correction import create_correction_function


def main():
    """Demonstrate distance correction workflow."""
    
    print("=" * 70)
    print("ILI Data Distance Correction Example")
    print("=" * 70)
    print()
    
    # Step 1: Create reference points from two inspection runs
    print("Step 1: Creating reference points from two inspection runs...")
    print()
    
    # Run 1 reference points (girth welds)
    ref_points_run1 = [
        ReferencePoint(
            id='rp1_1',
            run_id='run1_2020',
            distance=0.0,
            point_type='girth_weld',
            description='Start of segment'
        ),
        ReferencePoint(
            id='rp1_2',
            run_id='run1_2020',
            distance=500.0,
            point_type='girth_weld',
            description='Weld at 500ft'
        ),
        ReferencePoint(
            id='rp1_3',
            run_id='run1_2020',
            distance=1000.0,
            point_type='valve',
            description='Main valve'
        ),
        ReferencePoint(
            id='rp1_4',
            run_id='run1_2020',
            distance=1500.0,
            point_type='girth_weld',
            description='Weld at 1500ft'
        ),
        ReferencePoint(
            id='rp1_5',
            run_id='run1_2020',
            distance=2000.0,
            point_type='girth_weld',
            description='End of segment'
        )
    ]
    
    # Run 2 reference points (with odometer drift)
    ref_points_run2 = [
        ReferencePoint(
            id='rp2_1',
            run_id='run2_2023',
            distance=0.0,
            point_type='girth_weld',
            description='Start of segment'
        ),
        ReferencePoint(
            id='rp2_2',
            run_id='run2_2023',
            distance=503.0,  # +3 feet drift
            point_type='girth_weld',
            description='Weld at 500ft'
        ),
        ReferencePoint(
            id='rp2_3',
            run_id='run2_2023',
            distance=1007.0,  # +7 feet drift
            point_type='valve',
            description='Main valve'
        ),
        ReferencePoint(
            id='rp2_4',
            run_id='run2_2023',
            distance=1508.0,  # +8 feet drift
            point_type='girth_weld',
            description='Weld at 1500ft'
        ),
        ReferencePoint(
            id='rp2_5',
            run_id='run2_2023',
            distance=2005.0,  # +5 feet drift
            point_type='girth_weld',
            description='End of segment'
        )
    ]
    
    print(f"Run 1 (2020): {len(ref_points_run1)} reference points")
    print(f"Run 2 (2023): {len(ref_points_run2)} reference points")
    print()
    
    # Step 2: Perform DTW alignment
    print("Step 2: Performing DTW alignment...")
    print()
    
    aligner = DTWAligner(drift_constraint=0.10)
    alignment_result = aligner.align_sequences(
        ref_points_run1,
        ref_points_run2,
        'run1_2020',
        'run2_2023'
    )
    
    print(f"Alignment Results:")
    print(f"  - Matched points: {len(alignment_result.matched_points)}")
    print(f"  - Match rate: {alignment_result.match_rate:.1f}%")
    print(f"  - RMSE: {alignment_result.rmse:.2f} feet")
    print()
    
    # Step 3: Create distance correction function
    print("Step 3: Creating distance correction function...")
    print()
    
    corrector = create_correction_function(alignment_result)
    
    # Display correction function info
    info = corrector.get_correction_info()
    print(f"Correction Function Info:")
    print(f"  - Reference points: {info['num_reference_points']}")
    print(f"  - Distance range (Run 1): {info['distance_range_run1'][0]:.1f} - {info['distance_range_run1'][1]:.1f} ft")
    print(f"  - Distance range (Run 2): {info['distance_range_run2'][0]:.1f} - {info['distance_range_run2'][1]:.1f} ft")
    print(f"  - Max correction: {info['max_correction']:.2f} feet")
    print(f"  - Mean correction: {info['mean_correction']:.2f} feet")
    print(f"  - Std correction: {info['std_correction']:.2f} feet")
    print()
    
    # Step 4: Create sample anomalies from Run 1
    print("Step 4: Creating sample anomalies from Run 1...")
    print()
    
    anomalies_run1 = pd.DataFrame({
        'id': ['A001', 'A002', 'A003', 'A004', 'A005'],
        'run_id': ['run1_2020'] * 5,
        'distance': [250.0, 750.0, 1250.0, 1750.0, 2100.0],  # Last one is extrapolated
        'clock_position': [3.0, 6.0, 9.0, 12.0, 3.0],
        'depth_pct': [25.0, 30.0, 35.0, 40.0, 28.0],
        'length': [4.0, 5.0, 6.0, 7.0, 4.5],
        'width': [2.0, 2.5, 3.0, 3.5, 2.2],
        'feature_type': ['external_corrosion'] * 5
    })
    
    print("Original anomalies (Run 1 coordinate system):")
    print(anomalies_run1[['id', 'distance', 'depth_pct', 'feature_type']].to_string(index=False))
    print()
    
    # Step 5: Apply distance correction
    print("Step 5: Applying distance correction to transform to Run 2 coordinates...")
    print()
    
    corrected_anomalies = corrector.correct_anomaly_distances(anomalies_run1)
    
    # Display results
    print("Corrected anomalies (Run 2 coordinate system):")
    result_df = corrected_anomalies[['id', 'distance', 'corrected_distance', 'depth_pct']].copy()
    result_df['correction'] = result_df['corrected_distance'] - result_df['distance']
    result_df['extrapolated'] = result_df['distance'].apply(corrector.is_extrapolating)
    
    print(result_df.to_string(index=False))
    print()
    
    # Step 6: Demonstrate single distance correction
    print("Step 6: Correcting individual distances...")
    print()
    
    test_distances = [100.0, 500.0, 1000.0, 1500.0, 2000.0]
    print(f"{'Original (ft)':<15} {'Corrected (ft)':<15} {'Correction (ft)':<15}")
    print("-" * 45)
    
    for dist in test_distances:
        corrected = corrector.correct_distance(dist)
        correction = corrected - dist
        print(f"{dist:<15.1f} {corrected:<15.2f} {correction:<15.2f}")
    
    print()
    
    # Step 7: Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("The distance correction function successfully transformed anomaly")
    print("distances from Run 1 (2020) coordinate system to Run 2 (2023)")
    print("coordinate system, accounting for odometer drift.")
    print()
    print("Key points:")
    print("  - Piecewise linear interpolation handles varying drift patterns")
    print("  - Extrapolation works for anomalies outside reference point range")
    print("  - All original anomaly data is preserved")
    print("  - Corrections are applied efficiently to entire DataFrames")
    print()


if __name__ == '__main__':
    main()
