# Agentic vs Standard Workflows - Comparison

## Overview

The ILI Data Alignment System has **two modes of operation**:

1. **Standard (Rule-Based)** - Fast, deterministic, no API key needed
2. **Agentic (AI-Powered)** - Intelligent, explainable, requires Google API key

---

## Standard Workflow (Rule-Based)

### What It Uses:
- ✅ Hungarian algorithm for matching
- ✅ Mathematical similarity calculations
- ✅ DTW alignment
- ✅ Deterministic risk scoring
- ✅ XGBoost ML predictions

### Examples:
- `complete_system_demo_working.py`
- `three_way_analysis.py`
- `matching_example.py`
- `ml_prediction_example.py`

### Pros:
- ⚡ **Fast** - Processes 5,000+ anomalies in <30 seconds
- 🎯 **Accurate** - 96.5% match rate on real data
- 🔒 **Deterministic** - Same input = same output
- 💰 **Free** - No API costs
- 🚀 **Production-ready** - Proven algorithms

### Cons:
- ❌ No natural language explanations
- ❌ Limited interpretability
- ❌ Can't answer "why" questions

### When to Use:
- Production pipelines
- Batch processing
- Cost-sensitive applications
- When speed is critical
- When determinism is required

---

## Agentic Workflow (AI-Powered)

### What It Uses:
- 🤖 **Multi-agent system** with AutoGen
- 🧠 **Google Gemini** for natural language understanding
- 👥 **4 specialized AI agents**:
  1. **AlignmentAgent** - Verifies distance correction quality
  2. **MatchingAgent** - Explains similarity score components
  3. **ValidatorAgent** - Assesses match quality and confidence
  4. **ExplainerAgent** - Synthesizes human-readable explanations

### Examples:
- `complete_system_demo_with_agents.py` ⭐
- `agentic_explanation_example.py`
- `nl_query_example.py` (natural language queries)

### Pros:
- 💬 **Explainable** - Natural language explanations
- 🎓 **Intelligent** - Understands context and nuance
- 🔍 **Insightful** - Identifies concerns and recommendations
- 📊 **Interactive** - Can answer follow-up questions
- 🌐 **Natural language queries** - "Show me high-risk anomalies"

### Cons:
- 💰 **Costs money** - Google API usage fees (~$0.01-0.10 per explanation)
- 🐌 **Slower** - 2-5 seconds per explanation
- 🔑 **Requires API key** - Must set GOOGLE_API_KEY
- 🌐 **Needs internet** - API calls to Google
- 🎲 **Non-deterministic** - Slight variations in output

### When to Use:
- Customer demos and presentations
- Regulatory compliance reporting
- Training and education
- Investigating specific anomalies
- When human understanding is critical

---

## Feature Comparison

| Feature | Standard | Agentic |
|---------|----------|---------|
| **Anomaly Matching** | ✅ Hungarian algorithm | ✅ Same + AI explanation |
| **Match Rate** | ✅ 96.5% | ✅ 96.5% (same) |
| **Speed** | ✅ <30s for 5K | ⚠️ +2-5s per explanation |
| **Cost** | ✅ Free | ⚠️ ~$0.01-0.10 per explanation |
| **Explanations** | ❌ None | ✅ Natural language |
| **Natural Language Queries** | ❌ No | ✅ Yes |
| **Confidence Assessment** | ✅ Numeric score | ✅ Detailed reasoning |
| **Recommendations** | ❌ No | ✅ Yes |
| **Concern Identification** | ❌ No | ✅ Yes |
| **API Key Required** | ❌ No | ✅ Yes (Google) |
| **Internet Required** | ❌ No | ✅ Yes |
| **Deterministic** | ✅ Yes | ❌ No |
| **Production Ready** | ✅ Yes | ⚠️ Hybrid recommended |

---

## Example Outputs

### Standard Output:
```
Match: RUN_2020_0 → RUN_2022_1
Similarity: 0.87
Confidence: HIGH
Distance similarity: 0.95
Clock similarity: 1.00
Depth similarity: 0.82
```

### Agentic Output:
```
Match: RUN_2020_0 → RUN_2022_1
Confidence: HIGH (0.87)

Explanation:
This is a strong match with excellent alignment. The distance 
similarity is outstanding (0.95), indicating precise spatial 
correlation. Clock position is an exact match (6.0 → 6.0), 
confirming the same circumferential location. The depth has 
increased from 45% to 52% over 2 years, representing a growth 
rate of 3.5 pp/year, which is within expected corrosion rates 
for this environment.

Recommendation:
Accept this match with high confidence. Schedule follow-up 
inspection in 18-24 months to monitor continued growth.

Concerns:
- None identified. All similarity components are above threshold.
```

---

## Hybrid Approach (Recommended for Production)

### Best Practice:
1. **Use standard workflow** for all matching and analysis
2. **Use agentic workflow** selectively for:
   - High-risk anomalies requiring explanation
   - Regulatory compliance documentation
   - Customer presentations
   - Training materials
   - Disputed matches

### Example:
```python
# Standard matching (fast, free)
matches = matcher.match_anomalies(anom_2020, anom_2022, "RUN_2020", "RUN_2022")

# Filter high-risk matches
high_risk_matches = [m for m in matches['matches'] if m.similarity_score < 0.7]

# Get AI explanations only for high-risk (selective, cost-effective)
if high_risk_matches and os.getenv('GOOGLE_API_KEY'):
    explainer = MatchExplainerSystem()
    for match in high_risk_matches:
        explanation = explainer.explain_match(anom1, anom2, match)
        print(explanation['explanation'])
```

---

## Cost Analysis

### Standard Workflow:
- **Cost per run**: $0 (free)
- **Cost per 1,000 anomalies**: $0
- **Annual cost (100 runs)**: $0

### Agentic Workflow (Full):
- **Cost per explanation**: ~$0.05 (Google Gemini API)
- **Cost per 1,000 anomalies**: ~$50 (if explaining all)
- **Annual cost (100 runs)**: ~$5,000

### Hybrid Approach (Recommended):
- **Explain only high-risk (10%)**: ~$5 per 1,000 anomalies
- **Annual cost (100 runs)**: ~$500
- **Savings vs full agentic**: 90%

---

## How to Enable Agentic Features

### 1. Set Google API Key:
```bash
# In .env file
GOOGLE_API_KEY=your_actual_key_here
```

### 2. Run Agentic Demo:
```bash
python examples/complete_system_demo_with_agents.py
```

### 3. Or Use Selectively:
```python
from src.agents.match_explainer import MatchExplainerSystem

explainer = MatchExplainerSystem()
explanation = explainer.explain_match(anom1, anom2, match)
print(explanation['explanation'])
```

---

## Summary

| Use Case | Recommended Approach |
|----------|---------------------|
| **Production pipeline** | Standard |
| **Batch processing** | Standard |
| **Real-time analysis** | Standard |
| **Customer demos** | Agentic |
| **Regulatory reports** | Hybrid (standard + selective agentic) |
| **Training** | Agentic |
| **Investigating anomalies** | Agentic |
| **Cost-sensitive** | Standard |
| **Explainability required** | Agentic |

**Bottom Line**: Use **standard for speed and cost**, use **agentic for understanding and communication**. The hybrid approach gives you the best of both worlds! 🚀
