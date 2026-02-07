"""
Streamlit dashboard for ILI Data Alignment System.

Main entry point for the multi-page Streamlit application.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="ILI Data Alignment System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'anomalies_run1' not in st.session_state:
    st.session_state.anomalies_run1 = None
if 'anomalies_run2' not in st.session_state:
    st.session_state.anomalies_run2 = None
if 'reference_points_run1' not in st.session_state:
    st.session_state.reference_points_run1 = None
if 'reference_points_run2' not in st.session_state:
    st.session_state.reference_points_run2 = None
if 'matching_results' not in st.session_state:
    st.session_state.matching_results = None
if 'growth_results' not in st.session_state:
    st.session_state.growth_results = None
if 'risk_scores' not in st.session_state:
    st.session_state.risk_scores = None

# Sidebar navigation
st.sidebar.title("🔧 ILI Data Alignment")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Upload Data", "Alignment", "Matching", "Growth Analysis"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### System Status")
if st.session_state.data_loaded:
    st.sidebar.success("✓ Data Loaded")
    if st.session_state.anomalies_run1:
        st.sidebar.info(f"Run 1: {len(st.session_state.anomalies_run1)} anomalies")
    if st.session_state.anomalies_run2:
        st.sidebar.info(f"Run 2: {len(st.session_state.anomalies_run2)} anomalies")
else:
    st.sidebar.warning("⚠ No Data Loaded")

# Main content area
if page == "Home":
    st.markdown('<div class="main-header">ILI Data Alignment System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pipeline Integrity Management & Corrosion Growth Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Data Ingestion")
        st.markdown("""
        - Load ILI data from CSV files
        - Validate data quality
        - Standardize units
        - Extract reference points
        """)
    
    with col2:
        st.markdown("### 🔗 Alignment & Matching")
        st.markdown("""
        - DTW alignment of reference points
        - Distance correction
        - Hungarian algorithm matching
        - Confidence scoring
        """)
    
    with col3:
        st.markdown("### 📈 Growth Analysis")
        st.markdown("""
        - Calculate growth rates
        - Identify rapid growth
        - Risk scoring
        - Prioritization
        """)
    
    st.markdown("---")
    
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. **Upload Data**: Navigate to the Upload Data page to load your ILI inspection data
    2. **Alignment**: View DTW alignment results and distance correction
    3. **Matching**: See matched anomaly pairs with confidence scores
    4. **Growth Analysis**: Analyze growth rates and identify high-risk anomalies
    """)
    
    st.markdown("---")
    
    st.markdown("### 📋 System Features")
    
    with st.expander("Data Validation & Quality"):
        st.markdown("""
        - Pydantic-based schema validation
        - Missing value imputation
        - Unit standardization (miles→feet, mm→inches)
        - Comprehensive quality reporting
        """)
    
    with st.expander("DTW Alignment"):
        st.markdown("""
        - Dynamic Time Warping with 10% drift constraint
        - Match rate ≥95% target
        - RMSE ≤10 feet target
        - Piecewise linear distance correction
        """)
    
    with st.expander("Anomaly Matching"):
        st.markdown("""
        - Multi-criteria similarity (distance, clock, type, dimensions)
        - Hungarian algorithm for optimal assignment
        - Confidence levels: HIGH (≥0.8), MEDIUM (≥0.6), LOW (<0.6)
        - Unmatched classification (new vs repaired/removed)
        """)
    
    with st.expander("Growth Analysis"):
        st.markdown("""
        - Growth rate calculation for depth, length, width
        - Rapid growth identification (>5% per year)
        - Statistical summaries by feature type
        - Composite risk scoring (depth 60%, growth 30%, location 10%)
        """)
    
    st.markdown("---")
    
    st.info("👈 Use the sidebar to navigate between pages")

elif page == "Upload Data":
    from src.dashboard.pages import upload
    upload.show()

elif page == "Alignment":
    from src.dashboard.pages import alignment
    alignment.show()

elif page == "Matching":
    from src.dashboard.pages import matching
    matching.show()

elif page == "Growth Analysis":
    from src.dashboard.pages import growth
    growth.show()
