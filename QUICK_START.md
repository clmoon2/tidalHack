# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install (1 minute)

```bash
pip install -r requirements.txt
```

## 2. Configure (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_key_here
```

## 3. Test (3 minutes)

```bash
# Quick test all features
python test_new_features.py
```

## 4. Run Examples

### Compliance Reporting
```bash
python examples/compliance_reporting_example.py
```
**Output:** PDF report, CSV export, interactive charts

### ML Prediction
```bash
python examples/ml_prediction_example.py
```
**Output:** XGBoost model, SHAP explanations, predictions

### Natural Language Queries
```bash
python examples/nl_query_example.py
```
**Output:** Query results with natural language summaries

### 3-Way Analysis
```bash
python examples/three_way_analysis.py
```
**Output:** 15-year trend analysis, business impact

### Dashboard
```bash
streamlit run src/dashboard/app.py
```
**Output:** Interactive web UI at http://localhost:8501

## What You Get

### Regulatory Compliance ✨
- 49 CFR Parts 192 & 195 compliance
- ASME B31.8S growth classifications
- Risk level classifications
- Inspection interval calculations
- PDF reports with disclaimers
- CSV exports with regulatory fields

### ML Prediction ✨
- XGBoost regression model
- SHAP explanations
- Confidence intervals
- Feature importance
- Model persistence

### Natural Language Queries ✨
- Ask questions in plain English
- Automatic query parsing
- Natural language summaries
- Conversation context

### Core Features
- Data ingestion & validation
- DTW alignment
- Hungarian algorithm matching (96%+ match rate)
- Growth rate analysis
- Risk scoring
- 3-way analysis (15-year tracking)
- Interactive dashboard

## Database

**No setup needed!** SQLite database is created automatically at:
- `data/ili_system.db`

No Docker, no server, no configuration required.

## File Locations

### Input Data
- `data/ILIDataV2_2015.csv`
- `data/ILIDataV2_2022.csv`
- `data/ILIDataV2_2007.csv`

### Output Files
- `output/compliance_reports/` - PDF reports, CSV exports, charts
- `output/three_way_analysis/` - 3-way analysis results
- `models/` - Trained ML models

### Examples
- `examples/compliance_reporting_example.py`
- `examples/ml_prediction_example.py`
- `examples/nl_query_example.py`
- `examples/three_way_analysis.py`

### Documentation
- `README.md` - Project overview
- `TESTING_GUIDE.md` - Detailed testing instructions
- `FINAL_COMPLETION.md` - Complete project summary
- `docs/ADVANCED_FEATURES.md` - ML & NL query guide

## Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Google API key not found"
```bash
# Edit .env file
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### "Not enough training data"
This is normal if you have <100 matched pairs. Use more inspection runs or lower the confidence threshold.

### "PDF generation failed"
```bash
pip install reportlab
```

## Next Steps

1. ✅ Run `python test_new_features.py`
2. ✅ Run compliance example
3. ✅ Check generated PDF report
4. ✅ Try ML prediction
5. ✅ Test NL queries (if API key set)
6. ✅ Run dashboard
7. ✅ Review documentation

## Support

- `TESTING_GUIDE.md` - Detailed testing instructions
- `FINAL_COMPLETION.md` - Complete feature list
- `docs/ADVANCED_FEATURES.md` - Advanced features guide
- `README.md` - Project overview

---

**Ready to go! 🚀**

Run `python test_new_features.py` to get started.
