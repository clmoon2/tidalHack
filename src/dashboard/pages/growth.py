"""
Growth analysis page.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.growth.analyzer import GrowthAnalyzer
from src.growth.risk_scorer import RiskScorer


def show():
    """Display the growth analysis page."""
    st.markdown('<div class="main-header">📈 Growth Analysis</div>', unsafe_allow_html=True)
    st.markdown("Growth rate analysis and risk scoring")
    st.markdown("---")
    
    if not st.session_state.data_loaded:
        st.warning("⚠ Please upload data first")
        return
    
    if not st.session_state.matching_results:
        st.warning("⚠ Please perform matching first")
        return
    
    # Growth analysis parameters
    with st.expander("⚙️ Analysis Parameters", expanded=False):
        rapid_growth_threshold = st.slider(
            "Rapid Growth Threshold (% per year)",
            1.0, 10.0, 5.0, 0.5
        )
        risk_threshold = st.slider(
            "High Risk Threshold",
            0.3, 0.9, 0.5, 0.05
        )
    
    # Perform growth analysis
    if st.button("🚀 Analyze Growth", type="primary", use_container_width=True):
        with st.spinner("Analyzing growth rates..."):
            try:
                # Calculate time interval
                time_interval = (st.session_state.run2_date - st.session_state.run1_date).days / 365.25
                
                # Initialize analyzer
                analyzer = GrowthAnalyzer(rapid_growth_threshold=rapid_growth_threshold)
                
                # Analyze growth
                growth_result = analyzer.analyze_matches(
                    st.session_state.matching_results['matches'],
                    st.session_state.anomalies_run1,
                    st.session_state.anomalies_run2,
                    time_interval_years=time_interval
                )
                
                # Calculate risk scores
                scorer = RiskScorer()
                risk_scores = scorer.rank_by_risk(
                    st.session_state.anomalies_run2,
                    growth_result['growth_metrics']
                )
                
                # Store results
                st.session_state.growth_results = growth_result
                st.session_state.risk_scores = risk_scores
                
                st.success("✅ Growth analysis complete!")
                
            except Exception as e:
                st.error(f"Error during growth analysis: {e}")
                st.exception(e)
                return
    
    # Display results
    if st.session_state.growth_results:
        growth_result = st.session_state.growth_results
        stats = growth_result['statistics']
        
        st.markdown("### 📊 Growth Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Analyzed Matches", stats['total_matches'])
        with col2:
            st.metric("Rapid Growth", stats['rapid_growth_count'])
        with col3:
            st.metric("Mean Depth Growth", f"{stats['depth_growth']['mean']:.2f}%/yr")
        with col4:
            st.metric("Max Depth Growth", f"{stats['depth_growth']['max']:.2f}%/yr")
        
        st.markdown("---")
        
        # Rapid growth alerts
        if growth_result['rapid_growth_anomalies']:
            st.markdown("### ⚠️ Rapid Growth Anomalies")
            st.markdown(f"**{len(growth_result['rapid_growth_anomalies'])} anomalies** exceeding {rapid_growth_threshold}% per year threshold")
            
            rapid_data = []
            for anom in growth_result['rapid_growth_anomalies']:
                rapid_data.append({
                    'Anomaly ID': anom['anomaly_id'],
                    'Growth Rate (%/yr)': f"{anom['depth_growth_rate']:.2f}",
                    'Current Depth (%)': f"{anom['current_depth']:.1f}",
                    'Distance (ft)': f"{anom['distance']:.0f}",
                    'Clock Position': anom['clock_position']
                })
            
            df_rapid = pd.DataFrame(rapid_data)
            st.dataframe(df_rapid, use_container_width=True)
        else:
            st.success("✅ No rapid growth anomalies detected")
        
        st.markdown("---")
        
        # Growth distribution chart
        st.markdown("### 📊 Growth Rate Distribution")
        
        growth_rates = [gm.depth_growth_rate for gm in growth_result['growth_metrics']]
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=growth_rates,
            nbinsx=20,
            name='Depth Growth Rate',
            marker_color='#1f77b4'
        ))
        fig.add_vline(
            x=rapid_growth_threshold,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Rapid Growth Threshold ({rapid_growth_threshold}%/yr)"
        )
        fig.update_layout(
            xaxis_title="Growth Rate (% per year)",
            yaxis_title="Count",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Risk scores
        if st.session_state.risk_scores:
            st.markdown("### 🎯 Risk Score Rankings")
            
            risk_data = []
            for score in st.session_state.risk_scores[:10]:  # Top 10
                risk_data.append({
                    'Anomaly ID': score['anomaly_id'],
                    'Risk Score': f"{score['risk_score']:.3f}",
                    'Depth (%)': f"{score['depth_pct']:.1f}",
                    'Growth (%/yr)': f"{score['growth_rate']:.2f}",
                    'Location Factor': f"{score['location_factor']:.2f}"
                })
            
            df_risk = pd.DataFrame(risk_data)
            st.dataframe(df_risk, use_container_width=True)
            
            # High risk anomalies
            high_risk = [s for s in st.session_state.risk_scores if s['risk_score'] >= risk_threshold]
            
            if high_risk:
                st.error(f"🚨 {len(high_risk)} HIGH RISK anomalies (score ≥ {risk_threshold})")
            else:
                st.success(f"✅ No high risk anomalies (all below {risk_threshold} threshold)")
            
            # Download button
            csv = df_risk.to_csv(index=False)
            st.download_button(
                "📥 Download Risk Scores CSV",
                csv,
                "risk_scores.csv",
                "text/csv",
                key='download-risk'
            )
