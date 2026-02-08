"""
Match Explainer System
======================

Multi-agent system for explaining anomaly matches using AutoGen 0.7.5 and Google Gemini.

This system uses specialized agents to provide comprehensive explanations:
1. AlignmentAgent - Verifies distance correction quality
2. MatchingAgent - Explains similarity score components
3. ValidatorAgent - Assesses overall match quality
4. ExplainerAgent - Synthesizes human-readable explanation

Author: ILI Data Alignment System
Date: 2024
Updated: 2025 - Migrated to AutoGen 0.7.5 API
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
import pandas as pd

# AutoGen 0.7.5 imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
    from autogen_agentchat.messages import TextMessage
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelInfo
    AUTOGEN_AVAILABLE = True
except ImportError as e:
    AUTOGEN_AVAILABLE = False
    _import_error = str(e)

# Fallback to direct Gemini API if AutoGen not available
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False
        genai = None

# Import data models
try:
    from src.data_models.models import AnomalyRecord, Match
except ImportError:
    AnomalyRecord = None
    Match = None


class MatchExplainerSystem:
    """
    Multi-agent system for explaining anomaly matches.

    Uses AutoGen 0.7.5 with Google Gemini to coordinate specialized agents
    that analyze and explain why two anomalies were matched.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the match explainer system.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")

        # Check if AutoGen is available
        if not AUTOGEN_AVAILABLE:
            print(f"Warning: AutoGen not available ({_import_error}), using fallback mode")
            self._use_fallback = True
            self._initialize_fallback()
        else:
            self._use_fallback = False
            self._initialize_agents()

    def _initialize_fallback(self):
        """Initialize fallback Gemini client."""
        if GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None

    def _initialize_agents(self):
        """Initialize all specialized agents using AutoGen 0.7.5 API."""

        # Configure model client for Gemini via OpenAI-compatible API
        # Gemini offers an OpenAI-compatible endpoint
        # Use gemini-2.0-flash which is the current recommended model
        self.model_client = OpenAIChatCompletionClient(
            model="gemini-2.0-flash",
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model_info=ModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                family="gemini",
                structured_output=False
            )
        )

        # AlignmentAgent - Verifies distance correction
        self.alignment_agent = AssistantAgent(
            name="AlignmentAgent",
            model_client=self.model_client,
            system_message="""You are an alignment verification specialist for pipeline inspection data.

Your role:
1. Verify distance correction quality between two inspection runs
2. Check if reference point alignment is accurate
3. Assess if distance drift is within acceptable limits
4. Flag any alignment concerns

When analyzing a match, focus on:
- Corrected distance difference (should be < 5 feet for good match)
- Reference point alignment quality
- Distance drift patterns
- Alignment confidence

Provide concise, technical analysis. Use metrics and thresholds.
Keep your response to 2-3 sentences focused on alignment quality."""
        )

        # MatchingAgent - Explains similarity scores
        self.matching_agent = AssistantAgent(
            name="MatchingAgent",
            model_client=self.model_client,
            system_message="""You are a similarity analysis specialist for pipeline anomaly matching.

Your role:
1. Explain similarity score components (distance, clock, type, dimensions)
2. Identify which factors contribute most to the match
3. Highlight exact matches vs. changes
4. Explain dimensional changes (depth, length, width)

When analyzing a match, break down:
- Distance similarity (exponential decay, sigma=5ft)
- Clock position similarity (circular distance, sigma=1.0)
- Feature type match (exact or different)
- Depth change (percentage points)
- Dimensional changes (length, width in inches)

Provide clear explanations of each component. Keep your response to 3-4 sentences."""
        )

        # ValidatorAgent - Assesses match quality
        self.validator_agent = AssistantAgent(
            name="ValidatorAgent",
            model_client=self.model_client,
            system_message="""You are a match quality validator for pipeline inspection data.

Your role:
1. Assess overall match confidence (HIGH >= 0.8, MEDIUM >= 0.6, LOW < 0.6)
2. Identify conflicting evidence
3. Check for anomalies in growth patterns
4. Validate consistency across all factors

When validating a match, consider:
- Is the similarity score above threshold (0.6)?
- Are all components consistent?
- Is growth rate reasonable for the time interval?
- Are there any red flags or concerns?

Provide confidence assessment with justification. Keep your response to 2-3 sentences."""
        )

        # ExplainerAgent - Synthesizes explanation
        self.explainer_agent = AssistantAgent(
            name="ExplainerAgent",
            model_client=self.model_client,
            system_message="""You are an explanation synthesizer for pipeline anomaly matching.

Your role:
1. Synthesize inputs from AlignmentAgent, MatchingAgent, and ValidatorAgent
2. Create a coherent, human-readable explanation
3. Highlight key findings and confidence level
4. Provide actionable insights

Your explanation should:
- Start with overall match quality (Strong/Good/Weak/Poor)
- Summarize key evidence supporting the match
- Note any concerns or conflicting evidence
- Be concise (2-3 paragraphs)

Write for pipeline engineers and integrity managers. End with "ANALYSIS COMPLETE" when done."""
        )

        print("  [OK] 4 specialized AI agents initialized (AutoGen 0.7.5)")

    def explain_match(
        self,
        anomaly1: Union[Dict[str, Any], 'AnomalyRecord'],
        anomaly2: Union[Dict[str, Any], 'AnomalyRecord'],
        match_result: Union[Dict[str, Any], 'Match'],
        alignment_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for an anomaly match.

        Args:
            anomaly1: First anomaly data (from earlier run) - Dict or AnomalyRecord
            anomaly2: Second anomaly data (from later run) - Dict or AnomalyRecord
            match_result: Match result with similarity scores - Dict or Match
            alignment_info: Optional alignment information

        Returns:
            Dictionary with:
            {
                'match_id': str,
                'explanation': str,  # Human-readable explanation
                'confidence': str,   # HIGH, MEDIUM, or LOW
                'concerns': List[str],
                'recommendation': str
            }
        """
        # Convert objects to dicts if needed
        anom1_dict = self._to_dict(anomaly1)
        anom2_dict = self._to_dict(anomaly2)
        match_dict = self._to_dict(match_result)

        if self._use_fallback:
            return self._fallback_explanation(anom1_dict, anom2_dict, match_dict, "Using fallback mode")

        try:
            # Run async agent collaboration in sync context
            return asyncio.run(self._async_explain_match(
                anom1_dict, anom2_dict, match_dict, alignment_info
            ))
        except Exception as e:
            # Fallback to rule-based explanation on error
            return self._fallback_explanation(anom1_dict, anom2_dict, match_dict, str(e))

    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary."""
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, 'model_dump'):
            # Pydantic v2
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            # Pydantic v1
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            return {}

    async def _async_explain_match(
        self,
        anomaly1: Dict[str, Any],
        anomaly2: Dict[str, Any],
        match_result: Dict[str, Any],
        alignment_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Async version of explain_match using AutoGen 0.7.5 team."""

        # Prepare match data for agents
        match_data = self._prepare_match_data(
            anomaly1, anomaly2, match_result, alignment_info
        )

        # Create termination condition
        termination = MaxMessageTermination(max_messages=8) | TextMentionTermination("ANALYSIS COMPLETE")

        # Create team with all agents in round-robin order
        team = RoundRobinGroupChat(
            participants=[
                self.alignment_agent,
                self.matching_agent,
                self.validator_agent,
                self.explainer_agent
            ],
            termination_condition=termination
        )

        # Create the analysis prompt
        prompt = f"""Analyze this anomaly match and provide a comprehensive explanation:

{match_data}

Each agent should provide their specialized analysis in order:
1. AlignmentAgent - Verify distance correction and alignment quality
2. MatchingAgent - Explain similarity score components
3. ValidatorAgent - Assess overall match quality and confidence
4. ExplainerAgent - Synthesize all analyses into a clear explanation

Provide your analyses concisely."""

        # Run the team
        result = await team.run(task=prompt)

        # Extract analyses from result messages
        analyses = self._extract_analyses_from_result(result)

        # Generate final explanation
        return self._generate_explanation(analyses, match_result, anomaly1, anomaly2)

    def _prepare_match_data(
        self,
        anomaly1: Dict[str, Any],
        anomaly2: Dict[str, Any],
        match_result: Dict[str, Any],
        alignment_info: Optional[Dict[str, Any]]
    ) -> str:
        """Prepare match data in readable format for agents."""

        lines = []
        lines.append("MATCH DATA:")
        lines.append("")

        # Anomaly 1 - handle both old and new field names
        lines.append(f"Anomaly 1 (Earlier Run):")
        lines.append(f"  ID: {anomaly1.get('id', anomaly1.get('anomaly_id', 'N/A'))}")
        lines.append(f"  Distance: {anomaly1.get('distance', anomaly1.get('distance_ft', 0)):.1f} ft")
        lines.append(f"  Clock: {anomaly1.get('clock_position', 0):.1f}")
        lines.append(f"  Depth: {anomaly1.get('depth_pct', 0):.1f}%")
        lines.append(f"  Length: {anomaly1.get('length', anomaly1.get('length_in', 0)):.1f} in")
        lines.append(f"  Width: {anomaly1.get('width', anomaly1.get('width_in', 0)):.1f} in")
        lines.append(f"  Type: {anomaly1.get('feature_type', 'N/A')}")
        lines.append("")

        # Anomaly 2
        lines.append(f"Anomaly 2 (Later Run):")
        lines.append(f"  ID: {anomaly2.get('id', anomaly2.get('anomaly_id', 'N/A'))}")
        lines.append(f"  Distance: {anomaly2.get('distance', anomaly2.get('distance_ft', 0)):.1f} ft")
        lines.append(f"  Clock: {anomaly2.get('clock_position', 0):.1f}")
        lines.append(f"  Depth: {anomaly2.get('depth_pct', 0):.1f}%")
        lines.append(f"  Length: {anomaly2.get('length', anomaly2.get('length_in', 0)):.1f} in")
        lines.append(f"  Width: {anomaly2.get('width', anomaly2.get('width_in', 0)):.1f} in")
        lines.append(f"  Type: {anomaly2.get('feature_type', 'N/A')}")
        lines.append("")

        # Match result
        lines.append(f"Match Result:")
        lines.append(f"  Overall Similarity: {match_result.get('similarity_score', 0):.3f}")
        lines.append(f"  Distance Similarity: {match_result.get('distance_similarity', 0):.3f}")
        lines.append(f"  Clock Similarity: {match_result.get('clock_similarity', 0):.3f}")
        lines.append(f"  Type Match: {match_result.get('type_similarity', 0):.3f}")
        lines.append(f"  Depth Similarity: {match_result.get('depth_similarity', 0):.3f}")
        lines.append("")

        # Changes
        depth1 = anomaly1.get('depth_pct', 0)
        depth2 = anomaly2.get('depth_pct', 0)
        length1 = anomaly1.get('length', anomaly1.get('length_in', 0))
        length2 = anomaly2.get('length', anomaly2.get('length_in', 0))
        width1 = anomaly1.get('width', anomaly1.get('width_in', 0))
        width2 = anomaly2.get('width', anomaly2.get('width_in', 0))

        depth_change = depth2 - depth1
        length_change = length2 - length1
        width_change = width2 - width1

        lines.append(f"Changes:")
        lines.append(f"  Depth: {depth_change:+.1f} percentage points")
        lines.append(f"  Length: {length_change:+.1f} inches")
        lines.append(f"  Width: {width_change:+.1f} inches")
        lines.append("")

        # Alignment info
        if alignment_info:
            lines.append(f"Alignment Info:")
            lines.append(f"  Match Rate: {alignment_info.get('match_rate', 0):.1%}")
            lines.append(f"  RMSE: {alignment_info.get('rmse', 0):.2f} ft")
            lines.append("")

        return "\n".join(lines)

    def _extract_analyses_from_result(self, result) -> Dict[str, str]:
        """Extract analyses from AutoGen team result."""
        analyses = {
            'alignment': '',
            'matching': '',
            'validation': '',
            'explanation': ''
        }

        # result.messages contains the conversation
        for msg in result.messages:
            source = getattr(msg, 'source', '')
            content = getattr(msg, 'content', '')

            if isinstance(content, str):
                if source == 'AlignmentAgent':
                    analyses['alignment'] = content
                elif source == 'MatchingAgent':
                    analyses['matching'] = content
                elif source == 'ValidatorAgent':
                    analyses['validation'] = content
                elif source == 'ExplainerAgent':
                    analyses['explanation'] = content

        return analyses

    def _generate_explanation(
        self,
        analyses: Dict[str, str],
        match_result: Dict[str, Any],
        anomaly1: Dict[str, Any],
        anomaly2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate final explanation from agent analyses."""

        similarity = match_result.get('similarity_score', 0)

        # Determine confidence
        if similarity >= 0.8:
            confidence = 'HIGH'
        elif similarity >= 0.6:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        # Extract concerns from validation
        concerns = []
        validation_text = analyses['validation'].lower()
        if 'concern' in validation_text or 'warning' in validation_text or 'issue' in validation_text:
            concerns.append("Validator identified potential concerns")
        if similarity < 0.7:
            concerns.append(f"Similarity score {similarity:.3f} is below optimal threshold")

        # Check for growth concerns
        depth1 = anomaly1.get('depth_pct', 0)
        depth2 = anomaly2.get('depth_pct', 0)
        depth_change = depth2 - depth1
        if depth_change > 5:
            concerns.append(f"Significant depth growth observed ({depth_change:+.1f}%)")

        # Generate recommendation
        if confidence == 'HIGH':
            recommendation = "Accept this match with high confidence. The anomalies show strong correlation across all metrics."
        elif confidence == 'MEDIUM':
            recommendation = "Accept this match but review if critical. Some variation exists between inspections."
        else:
            recommendation = "Review this match manually - low confidence. Consider additional verification."

        # Use explainer analysis or create combined explanation
        explanation = analyses['explanation']
        if not explanation or len(explanation) < 50:
            # Create combined explanation from all analyses
            parts = []
            if analyses['alignment']:
                parts.append(f"Alignment: {analyses['alignment']}")
            if analyses['matching']:
                parts.append(f"Matching: {analyses['matching']}")
            if analyses['validation']:
                parts.append(f"Validation: {analyses['validation']}")
            explanation = "\n\n".join(parts) if parts else self._create_basic_explanation(
                anomaly1, anomaly2, match_result, confidence
            )

        # Clean up explanation (remove ANALYSIS COMPLETE marker)
        explanation = explanation.replace("ANALYSIS COMPLETE", "").strip()

        # Create match ID
        anom1_id = anomaly1.get('id', anomaly1.get('anomaly_id', 'unknown'))
        anom2_id = anomaly2.get('id', anomaly2.get('anomaly_id', 'unknown'))
        match_id = f"{anom1_id} -> {anom2_id}"

        return {
            'match_id': match_id,
            'explanation': explanation,
            'confidence': confidence,
            'similarity_score': similarity,
            'alignment_analysis': analyses['alignment'],
            'similarity_analysis': analyses['matching'],
            'validation_analysis': analyses['validation'],
            'concerns': concerns,
            'recommendation': recommendation
        }

    def _create_basic_explanation(
        self,
        anomaly1: Dict[str, Any],
        anomaly2: Dict[str, Any],
        match_result: Dict[str, Any],
        confidence: str
    ) -> str:
        """Create basic explanation when agent responses are insufficient."""
        similarity = match_result.get('similarity_score', 0)

        quality_map = {'HIGH': 'Strong', 'MEDIUM': 'Good', 'LOW': 'Weak'}
        quality = quality_map.get(confidence, 'Moderate')

        depth_change = anomaly2.get('depth_pct', 0) - anomaly1.get('depth_pct', 0)

        return f"""{quality} Match (Similarity: {similarity:.1%})

These anomalies were matched based on proximity in location (distance and clock position)
and similar characteristics. The depth changed by {depth_change:+.1f} percentage points
between inspections.

Distance similarity: {match_result.get('distance_similarity', 0):.1%}
Clock similarity: {match_result.get('clock_similarity', 0):.1%}
Type match: {match_result.get('type_similarity', 0):.1%}"""

    def _fallback_explanation(
        self,
        anomaly1: Dict[str, Any],
        anomaly2: Dict[str, Any],
        match_result: Dict[str, Any],
        error: str
    ) -> Dict[str, Any]:
        """Generate fallback explanation if agents fail."""

        similarity = match_result.get('similarity_score', 0)

        # Determine confidence
        if similarity >= 0.8:
            confidence = 'HIGH'
            quality = 'Strong'
        elif similarity >= 0.6:
            confidence = 'MEDIUM'
            quality = 'Good'
        else:
            confidence = 'LOW'
            quality = 'Weak'

        # Get field values with fallbacks for different naming conventions
        depth1 = anomaly1.get('depth_pct', 0)
        depth2 = anomaly2.get('depth_pct', 0)
        length1 = anomaly1.get('length', anomaly1.get('length_in', 0))
        length2 = anomaly2.get('length', anomaly2.get('length_in', 0))
        width1 = anomaly1.get('width', anomaly1.get('width_in', 0))
        width2 = anomaly2.get('width', anomaly2.get('width_in', 0))

        # Generate simple explanation
        explanation = f"""{quality} Match (Confidence: {confidence})

Similarity Score: {similarity:.3f}

This match was identified based on:
- Distance proximity: {match_result.get('distance_similarity', 0):.3f}
- Clock position: {match_result.get('clock_similarity', 0):.3f}
- Feature type: {match_result.get('type_similarity', 0):.3f}
- Dimensional similarity: {match_result.get('depth_similarity', 0):.3f}

Changes observed:
- Depth: {depth2 - depth1:+.1f} percentage points
- Length: {length2 - length1:+.1f} inches
- Width: {width2 - width1:+.1f} inches

Note: Full agent analysis unavailable ({error}). This is a simplified explanation."""

        anom1_id = anomaly1.get('id', anomaly1.get('anomaly_id', 'unknown'))
        anom2_id = anomaly2.get('id', anomaly2.get('anomaly_id', 'unknown'))

        return {
            'match_id': f"{anom1_id} -> {anom2_id}",
            'explanation': explanation,
            'confidence': confidence,
            'similarity_score': similarity,
            'alignment_analysis': 'Not available',
            'similarity_analysis': 'Not available',
            'validation_analysis': 'Not available',
            'concerns': ['Agent system unavailable - using fallback'],
            'recommendation': 'Review match manually' if confidence == 'LOW' else 'Accept match'
        }

    def explain_batch(
        self,
        matches: List[Dict[str, Any]],
        anomalies_run1: pd.DataFrame,
        anomalies_run2: pd.DataFrame,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Explain multiple matches (typically top N by similarity).

        Args:
            matches: List of match results
            anomalies_run1: Anomalies from first run
            anomalies_run2: Anomalies from second run
            top_n: Number of top matches to explain

        Returns:
            List of explanations
        """
        # Sort by similarity and take top N
        sorted_matches = sorted(
            matches,
            key=lambda x: x.get('similarity_score', 0),
            reverse=True
        )[:top_n]

        explanations = []
        for match in sorted_matches:
            # Get anomaly data
            anom1_id = match.get('anomaly_id_run1')
            anom2_id = match.get('anomaly_id_run2')

            anom1 = anomalies_run1[anomalies_run1['anomaly_id'] == anom1_id].iloc[0].to_dict()
            anom2 = anomalies_run2[anomalies_run2['anomaly_id'] == anom2_id].iloc[0].to_dict()

            # Generate explanation
            explanation = self.explain_match(anom1, anom2, match)

            explanations.append(explanation)

        return explanations
