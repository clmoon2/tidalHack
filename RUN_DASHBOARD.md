# Running the ILI Data Alignment Dashboard

## Quick Start (Local)

### 1. Make sure dependencies are installed
```bash
pip install -r requirements.txt
```

### 2. Run the dashboard
```bash
streamlit run src/dashboard/app.py
```

### 3. Open in browser
The dashboard will automatically open at:
```
http://localhost:8501
```

If it doesn't open automatically, just copy that URL into your browser.

## What You'll See

The dashboard has multiple pages:

1. **📤 Upload** - Upload CSV files for analysis
2. **🔗 Matching** - View anomaly matches between runs
3. **📈 Growth** - Analyze growth rates and risk scores
4. **🎯 Alignment** - View reference point alignment (if implemented)

## Using the Dashboard

### Upload Page
1. Click "Browse files" or drag-and-drop CSV files
2. Upload two inspection runs (e.g., 2020 and 2022)
3. View data quality reports
4. Proceed to matching

### Matching Page
1. View matched anomalies side-by-side
2. Filter by confidence level
3. Sort by similarity score
4. Export results to CSV

### Growth Page
1. View growth rate distributions
2. See risk score breakdowns
3. Identify rapid growth anomalies
4. Interactive charts with Plotly

## Stopping the Dashboard

Press `Ctrl+C` in the terminal where it's running.

## Troubleshooting

### Port already in use
If port 8501 is busy, specify a different port:
```bash
streamlit run src/dashboard/app.py --server.port 8502
```

### Module not found errors
Make sure you're in the project root directory:
```bash
cd /path/to/ili-data-alignment-system
streamlit run src/dashboard/app.py
```

### Data not loading
Make sure your CSV files are in the correct format (see DASHBOARD_QUICKSTART.md)
