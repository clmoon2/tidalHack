# Agentic Match Explanation System

## Overview

The ILI Data Alignment System now includes a sophisticated multi-agent system for explaining anomaly matches. This system uses AutoGen with Google Gemini to coordinate specialized AI agents that analyze and explain why two anomalies were matched.

## Architecture

### Multi-Agent System

The system consists of four specialized agents that collaborate to provide comprehensive match explanations:

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
│                  (GroupChatManager)                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Alignment   │    │   Matching   │    │  Validator   │
│    Agent     │    │    Agent     │    │    Agent     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  Explainer   │
                    │    Agent     │
                    └──────────────┘
                            │
                            ▼
                    Human-Readable
                     Explanation
```

### Agent Roles

#### 1. AlignmentAgent
**Specialty:** Distance correction and alignment verification

**Responsibilities:**
- Verify distance correction quality between inspection runs
- Check reference point alignment accuracy
- Assess if distance drift is within acceptable limits
- Flag alignment concerns

**Analysis Focus:**
- Corrected distance difference (should be < 5 feet for good match)
- Reference point alignment quality
- Distance drift patterns
- Alignment confidence

#### 2. MatchingAgent
**Specialty:** Similarity score analysis

**Responsibilities:**
- Explain similarity score components (distance, clock, type, dimensions)
- Identify which factors contribute most to the match
- Highlight exact matches vs. changes
- Explain dimensional changes (depth, length, width)

**Analysis Focus:**
- Distance similarity (exponential decay, sigma=5ft)
- Clock position similarity (circular distance, sigma=1.0)
- Feature type match (exact or different)
- Depth change (percentage points)
- Dimensional changes (length, width in inches)

#### 3. ValidatorAgent
**Specialty:** Match quality assessment

**Responsibilities:**
- Assess overall match confidence (HIGH >= 0.8, MEDIUM >= 0.6, LOW < 0.6)
- Identify conflicting evidence
- Check for anomalies in growth patterns
- Validate consistency across all factors

**Analysis Focus:**
- Is similarity score above threshold (0.6)?
- Are all components consistent?
- Is growth rate reasonable for the time interval?
- Are there any red flags or concerns?

#### 4. ExplainerAgent
**Specialty:** Synthesis and communication

**Responsibilities:**
- Synthesize inputs from all other agents
- Create coherent, human-readable explanation
- Highlight key findings and confidence level
- Provide actionable insights

**Output Format:**
- Overall match quality (Strong/Good/Weak/Poor)
- Key evidence supporting the match
- Concerns or conflicting evidence
- Confidence level and recommendation
- 3-5 paragraph professional explanation

## Task 6.3: Alignment Validation

### Overview

Validates DTW alignment quality against strict requirements:
- Match rate >= 95%
- RMSE <= 10 feet
- Flags unmatched reference points with diagnostics

### Implementation

```python
from src.alignment.validator import AlignmentValidator

# Initialize validator
validator = AlignmentValidator(
    min_match_rate=0.95,  # 95% minimum
    max_rmse=10.0         # 10 feet maximum
)

# Validate alignment
validation_result = validator.validate_alignment(
    alignment_result,
    ref_points_run1,
    ref_points_run2
)

# Generate report
report = validator.generate_report(validation_result)
print(report)
```

### Validation Result Structure

```python
{
    'is_valid': bool,                    # Overall pass/fail
    'match_rate': float,                 # Actual match rate
    'match_rate_passed': bool,           # Match rate >= threshold
    'match_rate_threshold': float,       # Threshold used
    'rmse': float,                       # Actual RMSE
    'rmse_passed': bool,                 # RMSE <= threshold
    'rmse_threshold': float,             # Threshold used
    'unmatched_run1': List[Dict],        # Unmatched points in run 1
    'unmatched_run2': List[Dict],        # Unmatched points in run 2
    'warnings': List[str],               # Warning messages
    'diagnostics': Dict                  # Detailed diagnostics
}
```

### Unmatched Point Diagnostics

For each unmatched reference point, the validator provides:

```python
{
    'index': int,                        # Point index
    'distance_ft': float,                # Distance location
    'feature_type': str,                 # Feature type
    'reason': str                        # Diagnostic reason
}
```

**Diagnostic Reasons:**
- "Point at beginning/end of run - may be outside alignment window"
- "Isolated point (gaps: X ft before, Y ft after)"
- "Close to matched point (X ft) but not selected by DTW"
- "Could not be aligned - possible data quality issue"

### Example Output

```
================================================================================
ALIGNMENT VALIDATION REPORT
================================================================================

Overall Status: ✅ PASSED

Match Rate: ✅ 96.5% (threshold: 95.0%)
RMSE: ✅ 8.23 ft (threshold: 10.00 ft)

Alignment Statistics:
  Total aligned pairs: 112
  Average distance error: 3.45 ft
  Max distance error: 8.23 ft
  Std dev distance error: 2.11 ft
  DTW distance: 387.56

Unmatched Reference Points: 4
  Run 1: 2
  Run 2: 2

Unmatched Categories:
  Boundary Points: 3
  Isolated Points: 1

Unmatched Points in Run 1:
  Distance 0.0 ft: Point at beginning of run - may be outside alignment window
  Distance 5234.5 ft: Point at end of run - may be outside alignment window

================================================================================
```

## Task 17: Agentic Match Explanation

### Overview

Multi-agent system that provides comprehensive, human-readable explanations for why two anomalies were matched.

### Implementation

```python
from src.agents.match_explainer import MatchExplainerSystem

# Initialize system (requires GOOGLE_API_KEY)
explainer = MatchExplainerSystem()

# Explain a single match
explanation = explainer.explain_match(
    anomaly1=anom1_data,
    anomaly2=anom2_data,
    match_result=match,
    alignment_info={
        'match_rate': 0.965,
        'rmse': 8.23
    }
)

# Explain multiple matches
explanations = explainer.explain_batch(
    matches=matches,
    anomalies_run1=anom1_df,
    anomalies_run2=anom2_df,
    top_n=5
)
```

### Explanation Result Structure

```python
{
    'explanation': str,              # Human-readable explanation (3-5 paragraphs)
    'confidence': str,               # HIGH, MEDIUM, or LOW
    'similarity_score': float,       # Overall similarity score
    'alignment_analysis': str,       # AlignmentAgent's analysis
    'similarity_analysis': str,      # MatchingAgent's analysis
    'validation_analysis': str,      # ValidatorAgent's analysis
    'concerns': List[str],           # Identified concerns
    'recommendation': str            # Action recommendation
}
```

### Example Explanation

```
Strong Match (Confidence: HIGH)

This is a high-confidence match between two metal loss anomalies with excellent 
alignment and similarity across all key factors. The overall similarity score 
of 0.873 indicates strong correspondence.

Distance Analysis: The anomalies are located at nearly identical positions 
(1234.5 ft vs 1235.2 ft after correction), with only 0.7 feet of drift. This 
is well within the expected alignment tolerance and indicates excellent 
reference point alignment. The distance correction function performed well 
with an RMSE of 8.23 feet across all reference points.

Similarity Breakdown: All similarity components are strong. Distance similarity 
is 0.95 (excellent), clock position is an exact match at 6.0, and the feature 
type is identical (metal_loss). The depth increased from 45% to 52%, representing 
7 percentage points of growth over 7 years, which equals 1.0 pp/year - consistent 
with typical corrosion growth rates. Dimensional changes are also consistent, 
with length increasing from 10.2" to 10.8" and width from 5.1" to 5.3".

Validation: All factors are consistent and support this match. The growth rate 
is reasonable for the time interval, and there are no conflicting indicators. 
The match confidence is HIGH, and no concerns were identified.

Recommendation: Accept this match with high confidence. This is a clear case 
of the same anomaly tracked across two inspection runs with expected corrosion 
growth.
```

### Confidence Levels

| Confidence | Similarity Score | Recommendation |
|-----------|------------------|----------------|
| HIGH      | >= 0.8          | Accept with high confidence |
| MEDIUM    | 0.6 - 0.8       | Accept but review if critical |
| LOW       | < 0.6           | Review manually - low confidence |

## Usage Examples

### Example 1: Validate Alignment

```python
from src.alignment.validator import AlignmentValidator

validator = AlignmentValidator()
validation = validator.validate_alignment(
    alignment_result,
    ref_points_run1,
    ref_points_run2
)

if validation['is_valid']:
    print("✅ Alignment passed validation")
else:
    print("❌ Alignment failed:")
    for warning in validation['warnings']:
        print(f"  - {warning}")
```

### Example 2: Explain Top Matches

```python
from src.agents.match_explainer import MatchExplainerSystem

explainer = MatchExplainerSystem()

# Get top 5 matches
top_matches = sorted(matches, key=lambda x: x['similarity_score'], reverse=True)[:5]

for match in top_matches:
    anom1 = get_anomaly_data(match['anomaly_id_run1'])
    anom2 = get_anomaly_data(match['anomaly_id_run2'])
    
    explanation = explainer.explain_match(anom1, anom2, match)
    
    print(f"\nMatch: {match['anomaly_id_run1']} → {match['anomaly_id_run2']}")
    print(f"Confidence: {explanation['confidence']}")
    print(f"\n{explanation['explanation']}")
    print(f"\nRecommendation: {explanation['recommendation']}")
```

### Example 3: Batch Explanation

```python
from src.agents.match_explainer import MatchExplainerSystem

explainer = MatchExplainerSystem()

# Explain top 10 matches
explanations = explainer.explain_batch(
    matches=all_matches,
    anomalies_run1=anom1_df,
    anomalies_run2=anom2_df,
    top_n=10
)

# Filter by confidence
high_confidence = [e for e in explanations if e['confidence'] == 'HIGH']
needs_review = [e for e in explanations if e['confidence'] == 'LOW']

print(f"High confidence matches: {len(high_confidence)}")
print(f"Matches needing review: {len(needs_review)}")
```

## Configuration

### Environment Variables

```bash
# Required for agentic system
GOOGLE_API_KEY=your_google_api_key_here
```

### LLM Configuration

The system uses Google Gemini Pro by default. You can customize:

```python
explainer = MatchExplainerSystem(api_key="your_key")

# Access LLM config
explainer.llm_config = {
    "config_list": [{
        "model": "gemini-pro",
        "api_key": api_key,
        "api_type": "google"
    }],
    "temperature": 0.7,  # Adjust for more/less creative explanations
    "timeout": 120,      # Timeout in seconds
}
```

### Validation Thresholds

```python
validator = AlignmentValidator(
    min_match_rate=0.95,  # Minimum 95% match rate
    max_rmse=10.0         # Maximum 10 feet RMSE
)
```

## Performance

### Alignment Validation
- **Speed:** < 1 second for typical datasets
- **Memory:** Minimal (processes reference points only)
- **Accuracy:** 100% (deterministic validation)

### Agentic Explanation
- **Speed:** 10-30 seconds per match (LLM calls)
- **Cost:** ~$0.001 per explanation (Gemini Pro pricing)
- **Quality:** High-quality, human-readable explanations
- **Fallback:** Rule-based explanation if agents fail

## Best Practices

### 1. Validate Alignment First

Always validate alignment before matching:

```python
validation = validator.validate_alignment(alignment_result, ref1, ref2)
if not validation['is_valid']:
    print("⚠️  Alignment quality issues detected")
    # Review warnings before proceeding
```

### 2. Explain Critical Matches

Focus agent explanations on:
- Low confidence matches (< 0.7 similarity)
- High-risk anomalies (> 80% depth)
- Rapid growth anomalies (> 5 pp/year)
- Matches near critical infrastructure

### 3. Batch Processing

For efficiency, explain matches in batches:

```python
# Explain top 10 instead of all matches
explanations = explainer.explain_batch(matches, anom1, anom2, top_n=10)
```

### 4. Cache Explanations

Store explanations in database to avoid re-generating:

```python
# Check if explanation exists
if not explanation_in_db(match_id):
    explanation = explainer.explain_match(anom1, anom2, match)
    save_explanation_to_db(match_id, explanation)
```

## Troubleshooting

### Issue: "AutoGen not available"

**Solution:**
```bash
pip install pyautogen
```

### Issue: "Google API key required"

**Solution:**
```bash
# Add to .env file
GOOGLE_API_KEY=your_actual_key_here
```

### Issue: Agent timeout

**Solution:**
```python
# Increase timeout
explainer.llm_config['timeout'] = 300  # 5 minutes
```

### Issue: Explanation quality poor

**Solution:**
```python
# Adjust temperature for more focused responses
explainer.llm_config['temperature'] = 0.3  # More deterministic
```

## Future Enhancements

### Planned Features

1. **Custom Agent Prompts**
   - Allow customization of agent system messages
   - Domain-specific terminology

2. **Multi-Language Support**
   - Generate explanations in multiple languages
   - Localized terminology

3. **Explanation Templates**
   - Pre-defined explanation formats
   - Regulatory compliance templates

4. **Agent Memory**
   - Agents remember previous matches
   - Learn from user feedback

5. **Visualization Integration**
   - Generate visual explanations
   - Interactive match comparison

## References

- **AutoGen Documentation:** https://microsoft.github.io/autogen/
- **Google Gemini API:** https://ai.google.dev/
- **Task 6.3:** Alignment Validation Requirements
- **Task 17:** Agentic Match Explanation Requirements

## Support

For issues or questions:
1. Check TESTING_GUIDE.md for examples
2. Review ADVANCED_FEATURES.md for ML/NLP features
3. See examples/agentic_explanation_example.py for full demo
