# ILI Data Alignment System - Dashboard Quick Start

## 🚀 Running the Dashboard

### Prerequisites
- Python 3.9 or higher
- All dependencies installed (see requirements.txt)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Starting the Dashboard

```bash
# From the project root directory
streamlit run src/dashboard/app.py
```

The dashboard will open automatically in your default web browser at `http://localhost:8501`

## 📋 Using the Dashboard

### 1. Home Page
- Overview of system features
- Getting started guide
- System status in sidebar

### 2. Upload Data
- Upload CSV files for two inspection runs
- Specify inspection dates and run IDs
- View data summary and preview
- Data is validated and loaded into memory

### 3. Alignment (Coming Soon)
- DTW alignment visualization
- Reference point matching
- Distance correction function
- Alignment quality metrics

### 4. Matching
- Configure matching parameters:
  - Distance sigma (default: 5.0 feet)
  - Clock sigma (default: 1.0 hour)
  - Confidence threshold (default: 0.6)
- Run Hungarian algorithm matching
- View matched pairs with confidence scores
- See unmatched anomalies (new vs repaired/removed)
- Download results as CSV

### 5. Growth Analysis
- Configure analysis parameters:
  - Rapid growth threshold (default: 5% per year)
  - High risk threshold (default: 0.5)
- Analyze growth rates for matched pairs
- View rapid growth alerts
- See growth rate distribution chart
- Review risk score rankings
- Download risk scores as CSV

## 📊 CSV File Format

Your CSV files should contain the following columns (case-insensitive):

### Required Columns
- `distance` or `Distance` - Odometer reading in feet
- `clock_position` or `Clock` - Circumferential position (1-12)
- `depth_pct` or `Depth%` - Depth as percentage (0-100)
- `length` or `Length` - Axial length in inches
- `width` or `Width` - Circumferential width in inches

### Optional Columns
- `feature_type` or `Type` - Anomaly type (default: "external_corrosion")
  - Valid values: external_corrosion, internal_corrosion, dent, crack, other

### Example CSV

```csv
Distance,Clock,Depth%,Length,Width,Type
1000.0,3.0,45.0,12.0,6.0,external_corrosion
2000.0,6.0,30.0,8.0,4.0,external_corrosion
3000.0,9.0,20.0,10.0,5.0,dent
```

## 🎯 Workflow Example

1. **Upload Data**
   - Upload Run 1 CSV (e.g., 2020 inspection)
   - Upload Run 2 CSV (e.g., 2022 inspection)
   - Set inspection dates
   - Click "Load and Process Data"

2. **Perform Matching**
   - Navigate to Matching page
   - Adjust parameters if needed
   - Click "Run Matching"
   - Review matched pairs and unmatched anomalies
   - Download results

3. **Analyze Growth**
   - Navigate to Growth Analysis page
   - Adjust thresholds if needed
   - Click "Analyze Growth"
   - Review rapid growth alerts
   - Check risk score rankings
   - Download risk scores

## 📈 Key Metrics

### Matching Metrics
- **Match Rate**: Percentage of anomalies successfully matched
- **High Confidence**: Matches with similarity ≥ 0.8
- **Medium Confidence**: Matches with similarity 0.6-0.8
- **New Anomalies**: Unmatched anomalies in newer run
- **Repaired/Removed**: Unmatched anomalies in older run

### Growth Metrics
- **Rapid Growth**: Anomalies exceeding threshold (default 5% per year)
- **Mean Depth Growth**: Average growth rate across all matches
- **Max Depth Growth**: Highest growth rate observed

### Risk Metrics
- **Risk Score**: Composite score (0-1) based on:
  - Depth contribution (60%)
  - Growth rate contribution (30%)
  - Location factor contribution (10%)
- **High Risk**: Anomalies exceeding risk threshold

## 🔧 Troubleshooting

### Dashboard won't start
```bash
# Make sure streamlit is installed
pip install streamlit

# Try running with full path
python -m streamlit run src/dashboard/app.py
```

### CSV loading errors
- Check that column names match expected format
- Ensure numeric values are valid (no text in numeric columns)
- Verify clock positions are between 1 and 12
- Check that depth percentages are between 0 and 100

### Matching errors
- Ensure both datasets are loaded
- Check that anomalies have valid coordinates
- Try adjusting sigma parameters if no matches found

### Growth analysis errors
- Ensure matching has been performed first
- Check that inspection dates are set correctly
- Verify time interval is positive

## 💡 Tips

- **Start with default parameters** and adjust based on results
- **Download results** after each step for record keeping
- **Use the sidebar** to check system status and navigate
- **Review unmatched anomalies** carefully - they may indicate repairs or new defects
- **Focus on rapid growth anomalies** for immediate attention
- **Sort by risk score** to prioritize inspection and maintenance

## 📞 Support

For issues or questions, refer to:
- `IMPLEMENTATION_GUIDE.md` - Detailed implementation documentation
- `MVP_COMPLETION_SUMMARY.md` - Feature summary and status
- `examples/matching_example.py` - Code examples

## 🎉 Next Steps

After using the dashboard:
1. Review high-risk anomalies with engineering team
2. Plan inspection intervals based on growth rates
3. Schedule repairs for rapid growth anomalies
4. Update maintenance records with matched anomaly data
5. Export results for regulatory compliance reporting
