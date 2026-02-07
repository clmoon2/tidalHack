"""
Alignment page for DTW results.
"""

import streamlit as st


def show():
    """Display the alignment page."""
    st.markdown('<div class="main-header">🔗 DTW Alignment</div>', unsafe_allow_html=True)
    st.markdown("Reference point alignment and distance correction")
    st.markdown("---")
    
    if not st.session_state.data_loaded:
        st.warning("⚠ Please upload data first")
        return
    
    st.info("📝 DTW Alignment feature coming soon!")
    st.markdown("""
    This page will display:
    - Reference point matching results
    - Alignment quality metrics (match rate, RMSE)
    - Distance correction function visualization
    - Pipeline schematic with matched points
    """)
    
    # Placeholder metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Match Rate", "96.5%", "1.5%")
    with col2:
        st.metric("RMSE", "8.2 ft", "-1.8 ft")
    with col3:
        st.metric("Matched Points", "45/47", "2")
