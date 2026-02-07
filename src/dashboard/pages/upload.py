"""
Upload page for loading ILI data.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.ingestion.loader import ILIDataLoader
from src.ingestion.validator import DataValidator
from src.ingestion.quality_reporter import QualityReporter
from src.data_models.models import AnomalyRecord


def show():
    """Display the upload page."""
    st.markdown('<div class="main-header">📤 Upload ILI Data</div>', unsafe_allow_html=True)
    st.markdown("Load inspection data from CSV files")
    st.markdown("---")
    
    # File uploaders
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Run 1 (Older Inspection)")
        file1 = st.file_uploader(
            "Upload CSV file for Run 1",
            type=['csv'],
            key='file1',
            help="Select the CSV file from the older inspection run"
        )
        
        if file1:
            run1_date = st.date_input(
                "Inspection Date (Run 1)",
                value=datetime(2020, 1, 1),
                key='run1_date'
            )
            run1_id = st.text_input(
                "Run ID",
                value="RUN_2020",
                key='run1_id'
            )
    
    with col2:
        st.markdown("### Run 2 (Newer Inspection)")
        file2 = st.file_uploader(
            "Upload CSV file for Run 2",
            type=['csv'],
            key='file2',
            help="Select the CSV file from the newer inspection run"
        )
        
        if file2:
            run2_date = st.date_input(
                "Inspection Date (Run 2)",
                value=datetime(2022, 1, 1),
                key='run2_date'
            )
            run2_id = st.text_input(
                "Run ID",
                value="RUN_2022",
                key='run2_id'
            )
    
    st.markdown("---")
    
    # Load button
    if st.button("🚀 Load and Process Data", type="primary", use_container_width=True):
        if not file1 or not file2:
            st.error("Please upload both CSV files before processing")
            return
        
        with st.spinner("Loading and processing data..."):
            try:
                # Load Run 1
                st.info("Loading Run 1...")
                loader1 = ILIDataLoader()
                df1 = pd.read_csv(file1)
                
                # Convert to anomaly records
                anomalies1 = []
                for idx, row in df1.iterrows():
                    try:
                        anomaly = AnomalyRecord(
                            id=f"{run1_id}_{idx}",
                            run_id=run1_id,
                            distance=float(row.get('distance', row.get('Distance', 0))),
                            clock_position=float(row.get('clock_position', row.get('Clock', 3))),
                            depth_pct=float(row.get('depth_pct', row.get('Depth%', 0))),
                            length=float(row.get('length', row.get('Length', 1))),
                            width=float(row.get('width', row.get('Width', 1))),
                            feature_type=row.get('feature_type', row.get('Type', 'external_corrosion')),
                            inspection_date=run1_date
                        )
                        anomalies1.append(anomaly)
                    except Exception as e:
                        st.warning(f"Skipping row {idx} in Run 1: {e}")
                
                # Load Run 2
                st.info("Loading Run 2...")
                df2 = pd.read_csv(file2)
                
                anomalies2 = []
                for idx, row in df2.iterrows():
                    try:
                        anomaly = AnomalyRecord(
                            id=f"{run2_id}_{idx}",
                            run_id=run2_id,
                            distance=float(row.get('distance', row.get('Distance', 0))),
                            clock_position=float(row.get('clock_position', row.get('Clock', 3))),
                            depth_pct=float(row.get('depth_pct', row.get('Depth%', 0))),
                            length=float(row.get('length', row.get('Length', 1))),
                            width=float(row.get('width', row.get('Width', 1))),
                            feature_type=row.get('feature_type', row.get('Type', 'external_corrosion')),
                            inspection_date=run2_date
                        )
                        anomalies2.append(anomaly)
                    except Exception as e:
                        st.warning(f"Skipping row {idx} in Run 2: {e}")
                
                # Store in session state
                st.session_state.anomalies_run1 = anomalies1
                st.session_state.anomalies_run2 = anomalies2
                st.session_state.run1_id = run1_id
                st.session_state.run2_id = run2_id
                st.session_state.run1_date = run1_date
                st.session_state.run2_date = run2_date
                st.session_state.data_loaded = True
                
                st.success("✅ Data loaded successfully!")
                
                # Display summary
                st.markdown("### 📊 Data Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Run 1 Anomalies", len(anomalies1))
                with col2:
                    st.metric("Run 2 Anomalies", len(anomalies2))
                with col3:
                    time_diff = (run2_date - run1_date).days / 365.25
                    st.metric("Time Interval", f"{time_diff:.1f} years")
                
                # Display data preview
                st.markdown("### 👀 Data Preview")
                
                tab1, tab2 = st.tabs(["Run 1", "Run 2"])
                
                with tab1:
                    st.dataframe(df1.head(10), use_container_width=True)
                
                with tab2:
                    st.dataframe(df2.head(10), use_container_width=True)
                
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.exception(e)
    
    # Show current data status
    if st.session_state.data_loaded:
        st.markdown("---")
        st.markdown("### ✅ Current Data Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Run 1:** {st.session_state.run1_id}")
            st.markdown(f"- Anomalies: {len(st.session_state.anomalies_run1)}")
            st.markdown(f"- Date: {st.session_state.run1_date}")
        
        with col2:
            st.markdown(f"**Run 2:** {st.session_state.run2_id}")
            st.markdown(f"- Anomalies: {len(st.session_state.anomalies_run2)}")
            st.markdown(f"- Date: {st.session_state.run2_date}")
        
        st.info("👉 Navigate to the Matching page to perform anomaly matching")
