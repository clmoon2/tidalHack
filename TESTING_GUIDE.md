# Testing Guide - New Features

This guide shows you how to test all the new features step by step.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   # Make sure .env file exists with your Google API key
   cat .env
   ```

## Quick Test (5 minutes)

Run the automated test script:

```bash
python test_new_features.py
```

This will test:
- ✅ Regulatory compliance scoring
- ✅ Inspection interval calculation
- ✅ Report generation
- ✅ ML feature engineering
- ✅ Natural language queries (if API key set)
- ✅ Error handling

## Detailed Testing

### 1. Regulatory Compliance (10 minutes)

**Test the compliance reporting example:**

```bash
python examples/compliance_reporting_example.py
```

**What it does:**
- Loads real data (2015 & 2022 inspections)
- Matches anomalies and calculates growth
- Scores anomalies per 49 CFR & ASME B31.8S
- Calculates inspection intervals
- Generates PDF report, CSV export, and charts

**Expected output:**
```
Step 1: Loading inspection data...
  2015: 1,768 anomalies
  2022: 2,636 anomalies

Step 2: Matching anomalies and calculating growth...
  Matched: 1,640 pairs
  Growth rates calculated: 1,165

Step 3: Calculating regulatory risk scores...
  Assessed: 100 anomalies

Step 4: Generating executive summary...
  Total anomalies: 100
  Immediate action required: X
  Critical + High risk: X
  Mean risk score: XX.X

...

✅ COMPLIANCE REPORTING COMPLETE!

Generated Files:
  • output/compliance_reports/risk_distribution.html
  • output/compliance_reports/growth_analysis.html
  • output/compliance_reports/compliance_export.csv
  • output/compliance_reports/compliance_report.pdf
```

**Check the outputs:**
```bash
# Open the HTML charts in your browser
start output/compliance_reports/risk_distribution.html  # Windows
# or
open output/compliance_reports/risk_distribution.html   # Mac/Linux

# Check the CSV
head output/compliance_reports/compliance_export.csv

# Open the PDF
start output/compliance_reports/compliance_report.pdf   # Windows
```

### 2. ML Prediction (10 minutes)

**Test ML growth prediction:**

```bash
python examples/ml_prediction_example.py
```

**What it does:**
- Loads inspection data
- Matches anomalies to get historical growth
- Engineers features (10+ features)
- Trains XGBoost model
- Makes predictions with confidence intervals
- Generates SHAP explanations

**Expected output:**
```
Step 1: Loading inspection data...
  2015: 1,768 anomalies
  2022: 2,636 anomalies

Step 2: Matching anomalies to calculate historical growth...
  Matched: 1,640 pairs
  Growth rates calculated: 1,165

Step 3: Engineering features for ML...
  Features extracted: 10+ features
  Training samples: 1,165

Step 4: Training XGBoost model...
  Model trained successfully!
  R² score: 0.XXX
  MAE: X.XXX pp/year
  RMSE: X.XXX pp/year

Step 5: Feature importance...
  Top 5 most important features:
    depth_pct: 0.XXX
    historical_growth_rate: 0.XXX
    ...

Step 6: Making predictions...
  Predictions made: 100
  Mean predicted growth: X.XXX pp/year

Step 7: SHAP explanations...
  Anomaly #1: RUN_2022_XXXX
  Predicted growth: X.XXX pp/year
  Top contributing features:
    depth_pct: +X.XXX
    ...

✅ ML PREDICTION EXAMPLE COMPLETE!
```

**Note:** If you see "Not enough training data", that's okay - it means you need more matched pairs. The system will still show you how it works.

### 3. Natural Language Queries (5 minutes)

**Prerequisites:** Make sure your Google API key is set in `.env`

```bash
# Check API key
grep GOOGLE_API_KEY .env
```

**Test NL queries:**

```bash
python examples/nl_query_example.py
```

**What it does:**
- Loads 2022 inspection data
- Parses natural language queries using Google Gemini
- Executes queries on the data
- Generates natural language summaries

**Expected output:**
```
Step 1: Loading inspection data...
  Loaded: 2,636 anomalies

Step 2: Initializing natural language query system...
  ✓ Query system ready

Step 3: Running example queries...

Query #1: Show me all metal loss anomalies deeper than 50%
Parsed structure:
  Filters: [{'column': 'depth_pct', 'operator': '>', 'value': 50}, ...]
  
Results: XX rows
Summary: Found XX metal loss anomalies with depth greater than 50%...

Sample results:
[Table of results]

...

✅ NATURAL LANGUAGE QUERY EXAMPLE COMPLETE!
```

**Try your own queries:**

Edit `examples/nl_query_example.py` and add your queries to the `example_queries` list:

```python
example_queries = [
    "Show me all metal loss anomalies deeper than 50%",
    "What's the average depth by feature type?",
    "Top 10 deepest anomalies",
    # Add your own queries here!
    "How many anomalies are between 1000 and 2000 feet?",
    "Find anomalies at 6 o'clock position with depth over 70%"
]
```

### 4. Dashboard Testing (10 minutes)

**Run the dashboard:**

```bash
streamlit run src/dashboard/app.py
```

**What to test:**

1. **Upload Page:**
   - Upload `data/ILIDataV2_2015.csv` as "Run 1"
   - Upload `data/ILIDataV2_2022.csv` as "Run 2"
   - Check data quality reports

2. **Matching Page:**
   - Click "Run Matching"
   - Check match statistics
   - Review matched pairs table

3. **Growth Analysis Page:**
   - View growth rate distribution
   - Check rapid growth alerts
   - Review risk score rankings

**Expected behavior:**
- Dashboard loads without errors
- Data uploads successfully
- Matching completes in <30 seconds
- Charts display correctly
- Tables are sortable and filterable

### 5. Error Handling Testing (5 minutes)

**Test error handling:**

```python
# Create a test script: test_errors.py
from src.utils.error_handler import ErrorHandler, DataValidationError

handler = ErrorHandler()

# Test 1: Data validation error
try:
    raise DataValidationError(
        "Invalid depth value",
        details={'field': 'depth_pct', 'value': -10}
    )
except DataValidationError as e:
    print(f"User message: {e.user_message}")
    # Should show user-friendly message

# Test 2: Data quality warning
from src.utils.error_handler import DataQualityWarning

warning = DataQualityWarning.low_match_rate(0.85, 0.95)
if warning:
    print(warning)
    # Should show actionable guidance
```

Run it:
```bash
python test_errors.py
```

## Troubleshooting

### Issue: "Module not found"

**Solution:**
```bash
# Make sure you're in the project root
cd /path/to/ili-data-alignment-system

# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH (Windows)
set PYTHONPATH=%CD%

# Set PYTHONPATH (Mac/Linux)
export PYTHONPATH=$(pwd)
```

### Issue: "Google API key not found"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Check API key is set
cat .env | grep GOOGLE_API_KEY

# If not set, edit .env:
echo "GOOGLE_API_KEY=your_actual_key_here" >> .env
```

### Issue: "Not enough training data"

**Solution:**
This is expected if you have <100 matched pairs. The ML model needs more historical data. You can:
1. Use more inspection runs
2. Lower the confidence threshold for matching
3. Use the rule-based growth analysis instead

### Issue: "PDF generation failed"

**Solution:**
```bash
# Install ReportLab
pip install reportlab

# Check if it's installed
python -c "import reportlab; print('ReportLab installed')"
```

### Issue: "Charts not displaying"

**Solution:**
```bash
# Install Plotly
pip install plotly

# Check if it's installed
python -c "import plotly; print('Plotly installed')"
```

## Verification Checklist

After testing, verify:

- [ ] Compliance example runs without errors
- [ ] PDF report generated in `output/compliance_reports/`
- [ ] CSV export contains regulatory fields
- [ ] Charts display correctly in browser
- [ ] ML example runs (or shows "not enough data" message)
- [ ] NL query example works (if API key set)
- [ ] Dashboard loads and processes data
- [ ] Error messages are user-friendly
- [ ] All output files are created

## Next Steps

Once testing is complete:

1. **Review outputs:**
   - Check PDF reports for accuracy
   - Verify CSV exports have all fields
   - Review charts for correctness

2. **Customize for your data:**
   - Update HCA (High Consequence Area) flags
   - Adjust coating condition data
   - Set MAOP ratios if available

3. **Deploy to production:**
   - Set up production database
   - Configure environment variables
   - Set up automated reporting

4. **Train ML model:**
   - Collect more historical data
   - Train on your specific pipeline
   - Validate predictions

## Support

If you encounter issues:

1. Check error messages carefully
2. Review `FINAL_COMPLETION.md` for setup instructions
3. Check `docs/ADVANCED_FEATURES.md` for detailed guides
4. Review example scripts for correct usage

## Performance Benchmarks

Expected performance on test data:

- **Compliance reporting:** <30 seconds for 100 anomalies
- **ML training:** 1-5 seconds for 1000 samples
- **NL query parsing:** 1-2 seconds per query
- **PDF generation:** 2-5 seconds
- **Dashboard loading:** <5 seconds

If performance is significantly slower, check:
- CPU usage
- Available memory
- Network connection (for API calls)
- Disk space for outputs

---

**Happy Testing! 🧪**

For questions or issues, refer to:
- `FINAL_COMPLETION.md` - Complete project summary
- `docs/ADVANCED_FEATURES.md` - Detailed feature guide
- `README.md` - Project overview
