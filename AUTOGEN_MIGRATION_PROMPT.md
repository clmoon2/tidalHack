# AutoGen Migration Prompt for Claude Sonnet 4.6

## Context
The ILI Data Alignment System has a multi-agent match explanation system in `src/agents/match_explainer.py` that was written for AutoGen 0.2 API but we have AutoGen 0.7.5 installed which has a completely different API.

## Current Situation
- **Installed**: `autogen-agentchat==0.7.5` and `autogen-core==0.7.5`
- **Code written for**: Old AutoGen 0.2 API (AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager)
- **New API uses**: Different imports and patterns from `autogen_agentchat` and `autogen_core`

## Task
Rewrite `src/agents/match_explainer.py` to use the **AutoGen 0.7.5 API** while maintaining the same functionality.

## Requirements

### 1. Keep the Same External Interface
The `MatchExplainerSystem` class must maintain this interface:
```python
class MatchExplainerSystem:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Google API key"""
        
    def explain_match(
        self,
        anomaly1: AnomalyRecord,  # First anomaly object
        anomaly2: AnomalyRecord,  # Second anomaly object
        match_result: Match,      # Match object with similarity scores
        alignment_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            'match_id': str,
            'explanation': str,      # Human-readable explanation
            'confidence': str,       # HIGH, MEDIUM, or LOW
            'concerns': List[str],   # List of concerns
            'recommendation': str    # Actionable recommendation
        }
        """
```

### 2. Use AutoGen 0.7.5 API
- Import from `autogen_agentchat` and `autogen_core`
- Use the new agent patterns (no more AssistantAgent/UserProxyAgent)
- Reference: https://microsoft.github.io/autogen/0.4/user-guide/agentchat-user-guide/index.html

### 3. Use Google Gemini as LLM
- Configure to use Google Gemini API (not OpenAI)
- Use the `GOOGLE_API_KEY` from environment
- Model: `gemini-pro` or `gemini-1.5-pro`

### 4. Maintain 4 Specialized Agents
Keep the same agent roles:
1. **AlignmentAgent** - Verifies distance correction quality
2. **MatchingAgent** - Explains similarity score components  
3. **ValidatorAgent** - Assesses match quality and confidence
4. **ExplainerAgent** - Synthesizes human-readable explanation

### 5. Agent Collaboration Pattern
Agents should collaborate to analyze the match:
- AlignmentAgent analyzes distance/spatial alignment
- MatchingAgent explains similarity components
- ValidatorAgent assesses overall quality
- ExplainerAgent synthesizes into final explanation

### 6. Input Data Format
The agents receive AnomalyRecord objects with these attributes:
```python
anomaly1.id              # str
anomaly1.distance        # float (feet)
anomaly1.clock_position  # float (1-12)
anomaly1.depth_pct       # float (0-100)
anomaly1.length          # float (inches)
anomaly1.width           # float (inches)
anomaly1.feature_type    # str (e.g., 'metal_loss')
```

Match object has:
```python
match.similarity_score      # float (0-1)
match.distance_similarity   # float (0-1)
match.clock_similarity      # float (0-1)
match.depth_similarity      # float (0-1)
match.confidence           # str (HIGH/MEDIUM/LOW)
```

### 7. Error Handling
- Gracefully handle API failures
- Provide fallback explanations if agents fail
- Log errors but don't crash

## Example Usage
```python
from src.agents.match_explainer import MatchExplainerSystem

explainer = MatchExplainerSystem()  # Uses GOOGLE_API_KEY from env

explanation = explainer.explain_match(
    anomaly1=anom_2020,
    anomaly2=anom_2022,
    match_result=match
)

print(explanation['explanation'])
print(f"Confidence: {explanation['confidence']}")
print(f"Recommendation: {explanation['recommendation']}")
```

## Files to Update
1. **src/agents/match_explainer.py** - Main file to rewrite
2. **examples/agentic_explanation_example.py** - May need minor updates if API changes
3. **examples/complete_system_demo_with_agents.py** - Already calls it correctly

## Testing
After migration, test with:
```bash
python examples/complete_system_demo_with_agents.py
```

Should see:
- ✓ Google API key found
- ✓ 4 agents initialized
- ✓ AI explanations generated
- ✓ Natural language output

## Additional Notes
- Keep the code clean and well-documented
- Use type hints throughout
- Follow the existing code style in the project
- The system should work with the Google API key already set in `.env`
- Don't change the data models or other parts of the system

## Success Criteria
✅ Code uses AutoGen 0.7.5 API correctly
✅ Works with Google Gemini (not OpenAI)
✅ Maintains same external interface
✅ 4 agents collaborate to generate explanations
✅ Returns properly formatted explanation dictionary
✅ Handles errors gracefully
✅ Example scripts run successfully
