"""
Matching page for anomaly matching results.
"""

import streamlit as st
import pandas as pd
from src.matching.matcher import HungarianMatcher
from src.matching.similarity import SimilarityCalculator


def show():
    """Display the matching page."""
    st.markdown('<div class="main-header">🎯 Anomaly Matching</div>', unsafe_allow_html=True)
    st.markdown("Hungarian algorithm-based optimal matching")
    st.markdown("---")
    
    if not st.session_state.data_loaded:
        st.warning("⚠ Please upload data first")
        return
    
    # Matching parameters
    with st.expander("⚙️ Matching Parameters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            distance_sigma = st.slider("Distance Sigma (feet)", 1.0, 20.0, 5.0, 0.5)
            clock_sigma = st.slider("Clock Sigma (hours)", 0.5, 3.0, 1.0, 0.1)
        with col2:
            confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.6, 0.05)
    
    # Perform matching
    if st.button("🚀 Run Matching", type="primary", use_container_width=True):
        with st.spinner("Performing optimal matching..."):
            try:
                # Initialize matcher
                similarity_calc = SimilarityCalculator(
                    distance_sigma=distance_sigma,
                    clock_sigma=clock_sigma
                )
                matcher = HungarianMatcher(
                    similarity_calculator=similarity_calc,
                    confidence_threshold=confidence_threshold
                )
                
                # Perform matching
                result = matcher.match_anomalies(
                    st.session_state.anomalies_run1,
                    st.session_state.anomalies_run2,
                    st.session_state.run1_id,
                    st.session_state.run2_id
                )
                
                # Store results
                st.session_state.matching_results = result
                
                st.success("✅ Matching complete!")
                
            except Exception as e:
                st.error(f"Error during matching: {e}")
                st.exception(e)
                return
    
    # Display results
    if st.session_state.matching_results:
        result = st.session_state.matching_results
        stats = result['statistics']
        
        st.markdown("### 📊 Matching Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Matched Pairs", stats['matched'])
        with col2:
            st.metric("Match Rate", f"{stats['match_rate']:.1f}%")
        with col3:
            st.metric("High Confidence", stats['high_confidence'])
        with col4:
            st.metric("New Anomalies", stats['unmatched_run2'])
        
        st.markdown("---")
        
        # Matched pairs table
        st.markdown("### ✅ Matched Anomaly Pairs")
        
        if result['matches']:
            matches_data = []
            for match in result['matches']:
                matches_data.append({
                    'Run 1 ID': match.anomaly1_id,
                    'Run 2 ID': match.anomaly2_id,
                    'Similarity': f"{match.similarity_score:.3f}",
                    'Confidence': match.confidence,
                    'Distance Sim': f"{match.distance_similarity:.3f}",
                    'Clock Sim': f"{match.clock_similarity:.3f}",
                    'Type Sim': f"{match.type_similarity:.3f}"
                })
            
            df_matches = pd.DataFrame(matches_data)
            st.dataframe(df_matches, use_container_width=True)
            
            # Download button
            csv = df_matches.to_csv(index=False)
            st.download_button(
                "📥 Download Matches CSV",
                csv,
                "matched_anomalies.csv",
                "text/csv",
                key='download-matches'
            )
        else:
            st.info("No matches found above confidence threshold")
        
        st.markdown("---")
        
        # Unmatched anomalies
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 Repaired/Removed")
            if result['unmatched']['repaired_or_removed']:
                for anom in result['unmatched']['repaired_or_removed']:
                    st.markdown(f"- {anom.id} ({anom.distance:.0f} ft, {anom.clock_position} o'clock)")
            else:
                st.info("No repaired/removed anomalies")
        
        with col2:
            st.markdown("### ⚠️ New Anomalies")
            if result['unmatched']['new']:
                for anom in result['unmatched']['new']:
                    st.markdown(f"- {anom.id} ({anom.distance:.0f} ft, {anom.depth_pct:.1f}%)")
            else:
                st.info("No new anomalies")
        
        st.info("👉 Navigate to Growth Analysis to analyze growth rates")
