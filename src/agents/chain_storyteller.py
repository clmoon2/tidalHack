"""
Chain Storyteller System
========================

Extended multi-agent system for explaining anomaly chains across three inspection runs.

Adds 2 new specialized agents to the existing 4-agent system:
5. TrendAgent - Analyzes growth acceleration across intervals
6. ProjectionAgent - Projects future state and urgency

The ChainStorytellerSystem orchestrates all 6 agents to tell the full lifecycle
story of an anomaly from first detection through current state.

Author: ILI Data Alignment System
Date: 2025
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union

# AutoGen 0.7.5 imports
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core.models import ModelInfo
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

# Fallback to direct Gemini API
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
    from src.data_models.models import AnomalyChain, ChainExplanation
except ImportError:
    AnomalyChain = None
    ChainExplanation = None


class TrendAgent:
    """
    Analyzes growth acceleration across two time intervals.

    Compares 2007-2015 rate vs 2015-2022 rate and classifies:
    - ACCELERATING: growth rate increased by > 0.1 pp/yr²
    - STABLE: growth rate change within ±0.1 pp/yr²
    - DECELERATING: growth rate decreased by > 0.1 pp/yr²
    """

    ACCELERATION_THRESHOLD = 0.1  # pp/yr²

    @staticmethod
    def classify_trend(growth_rate_07_15: float, growth_rate_15_22: float) -> str:
        """Classify the growth trend based on acceleration."""
        acceleration = growth_rate_15_22 - growth_rate_07_15
        if acceleration > TrendAgent.ACCELERATION_THRESHOLD:
            return "ACCELERATING"
        elif acceleration < -TrendAgent.ACCELERATION_THRESHOLD:
            return "DECELERATING"
        else:
            return "STABLE"

    @staticmethod
    def analyze(chain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze growth trend for a chain.

        Args:
            chain: Dictionary with chain data including growth rates

        Returns:
            Dictionary with trend analysis results
        """
        gr_07_15 = chain.get("growth_rate_07_15", 0.0)
        gr_15_22 = chain.get("growth_rate_15_22", 0.0)
        acceleration = gr_15_22 - gr_07_15

        classification = TrendAgent.classify_trend(gr_07_15, gr_15_22)

        # Determine severity description
        if classification == "ACCELERATING":
            if acceleration > 1.0:
                severity = "rapidly accelerating"
            elif acceleration > 0.5:
                severity = "moderately accelerating"
            else:
                severity = "slightly accelerating"
        elif classification == "DECELERATING":
            if acceleration < -1.0:
                severity = "rapidly decelerating"
            elif acceleration < -0.5:
                severity = "moderately decelerating"
            else:
                severity = "slightly decelerating"
        else:
            severity = "stable"

        return {
            "classification": classification,
            "acceleration": acceleration,
            "severity": severity,
            "growth_rate_07_15": gr_07_15,
            "growth_rate_15_22": gr_15_22,
            "analysis": (
                f"Growth rate changed from {gr_07_15:.2f} pp/yr (2007-2015) to "
                f"{gr_15_22:.2f} pp/yr (2015-2022). "
                f"Acceleration: {acceleration:+.3f} pp/yr². "
                f"Trend: {severity} ({classification})."
            ),
        }


class ProjectionAgent:
    """
    Projects future state and assesses urgency.

    Calculates years to 80% critical threshold and assigns urgency:
    - IMMEDIATE: < 3 years or already > 70%
    - NEAR_TERM: 3-7 years
    - SCHEDULED: 7-15 years
    - MONITOR: > 15 years or negative growth
    """

    CRITICAL_DEPTH = 80.0  # % wall thickness

    @staticmethod
    def project_years_to_critical(
        current_depth: float,
        growth_rate: float,
        acceleration: float = 0.0,
    ) -> Optional[float]:
        """
        Project years until 80% critical depth threshold.

        Uses linear projection from current growth rate.
        If acceleration is positive, uses the higher rate for conservative estimate.

        Args:
            current_depth: Current depth percentage
            growth_rate: Current growth rate (pp/year)
            acceleration: Growth acceleration (pp/yr²)

        Returns:
            Years to 80% threshold, or None if already above or not growing
        """
        if current_depth >= ProjectionAgent.CRITICAL_DEPTH:
            return 0.0

        remaining = ProjectionAgent.CRITICAL_DEPTH - current_depth

        # Use the higher of current rate or accelerated rate for conservative estimate
        effective_rate = growth_rate
        if acceleration > 0:
            # Conservative: assume acceleration continues for 5 years
            effective_rate = growth_rate + (acceleration * 2.5)

        if effective_rate <= 0:
            return None  # Not growing or shrinking

        return remaining / effective_rate

    @staticmethod
    def assess_urgency(
        years_to_critical: Optional[float], current_depth: float
    ) -> str:
        """
        Assess urgency level based on projected timeline.

        Args:
            years_to_critical: Years to 80% threshold (None if not growing)
            current_depth: Current depth percentage

        Returns:
            Urgency level string
        """
        if current_depth >= 70.0:
            return "IMMEDIATE"
        if years_to_critical is None:
            return "MONITOR"
        if years_to_critical <= 0:
            return "IMMEDIATE"
        if years_to_critical <= 3:
            return "IMMEDIATE"
        if years_to_critical <= 7:
            return "NEAR_TERM"
        if years_to_critical <= 15:
            return "SCHEDULED"
        return "MONITOR"

    @staticmethod
    def analyze(chain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Project future state for a chain.

        Args:
            chain: Dictionary with chain data

        Returns:
            Dictionary with projection results
        """
        current_depth = chain.get("depth_2022", 0.0)
        growth_rate = chain.get("growth_rate_15_22", 0.0)
        acceleration = chain.get("acceleration", 0.0)

        years_to_critical = ProjectionAgent.project_years_to_critical(
            current_depth, growth_rate, acceleration
        )
        urgency = ProjectionAgent.assess_urgency(years_to_critical, current_depth)

        # Build projection narrative
        if years_to_critical is not None and years_to_critical > 0:
            projection_text = (
                f"At current growth rate ({growth_rate:.2f} pp/yr), "
                f"this anomaly will reach the 80% critical threshold in "
                f"approximately {years_to_critical:.1f} years."
            )
        elif years_to_critical == 0.0:
            projection_text = (
                f"This anomaly has ALREADY exceeded the 80% critical threshold "
                f"at {current_depth:.1f}% depth. Immediate action required."
            )
        else:
            projection_text = (
                f"Growth rate is not positive ({growth_rate:.2f} pp/yr). "
                f"The anomaly is stable or shrinking. Current depth: {current_depth:.1f}%."
            )

        return {
            "years_to_critical": years_to_critical,
            "urgency": urgency,
            "current_depth": current_depth,
            "growth_rate": growth_rate,
            "projection_text": projection_text,
            "analysis": (
                f"Current depth: {current_depth:.1f}%. "
                f"Projected years to 80%: {years_to_critical if years_to_critical is not None else 'N/A'}. "
                f"Urgency: {urgency}."
            ),
        }


class ChainStorytellerSystem:
    """
    Orchestrates all 6 agents (4 existing + 2 new) to generate full lifecycle
    narratives for anomaly chains.

    Agents:
    1. AlignmentAgent - Verifies distance correction quality
    2. MatchingAgent - Explains similarity score components
    3. ValidatorAgent - Assesses overall match quality
    4. ExplainerAgent - Synthesizes human-readable explanation
    5. TrendAgent - Analyzes growth acceleration across intervals
    6. ProjectionAgent - Projects future state
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chain storyteller system.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._use_fallback = False

        if not self.api_key:
            print("  [WARN] No Google API key found. Using rule-based storytelling.")
            self._use_fallback = True
        elif not AUTOGEN_AVAILABLE:
            print("  [WARN] AutoGen not available. Using rule-based storytelling.")
            self._use_fallback = True
        else:
            self._initialize_agents()

    def _initialize_agents(self):
        """Initialize AI agents using AutoGen 0.7.5."""
        self.model_client = OpenAIChatCompletionClient(
            model="gemini-2.0-flash",
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model_info=ModelInfo(
                vision=False,
                function_calling=True,
                json_output=True,
                family="gemini",
                structured_output=False,
            ),
        )

        # TrendNarratorAgent - Tells the growth acceleration story via AI
        self.trend_narrator_agent = AssistantAgent(
            name="TrendNarratorAgent",
            model_client=self.model_client,
            system_message="""You are a pipeline corrosion trend analyst.

Your role:
1. Analyze growth acceleration patterns across two time intervals
2. Explain what the changing growth rates mean for pipeline integrity
3. Compare early-period vs late-period corrosion behavior
4. Identify concerning acceleration patterns

When analyzing a chain, focus on:
- Whether growth is accelerating, stable, or decelerating
- What acceleration means for the corrosion mechanism
- Whether the pattern suggests a change in operating conditions
- Historical context of the anomaly's evolution

Provide concise, technical analysis. Keep your response to 2-3 sentences.""",
        )

        # ProjectionNarratorAgent - Tells the future state story via AI
        self.projection_narrator_agent = AssistantAgent(
            name="ProjectionNarratorAgent",
            model_client=self.model_client,
            system_message="""You are a pipeline integrity projection specialist.

Your role:
1. Project future corrosion depth based on current trends
2. Assess urgency of intervention
3. Recommend inspection intervals
4. Calculate time-to-critical thresholds

When analyzing a chain, focus on:
- Years until 80% wall thickness (critical threshold per 49 CFR 192.933)
- Whether acceleration warrants earlier intervention
- Recommended dig/repair timeline
- Cost implications of delayed vs. proactive action

Provide concise projections with clear timelines. Keep to 2-3 sentences.
End with "CHAIN ANALYSIS COMPLETE" when done.""",
        )

        print("  [OK] 6 specialized AI agents initialized (4 existing + 2 new)")

    def explain_chain(self, chain_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a full lifecycle narrative for an anomaly chain.

        Uses all 6 agents to tell the story from first detection
        through current state with future projection.

        Args:
            chain_data: Dictionary with chain data including:
                - chain_id, anomaly IDs for each run
                - depth_2007, depth_2015, depth_2022
                - growth_rate_07_15, growth_rate_15_22
                - acceleration
                - match_confidence_07_15, match_confidence_15_22

        Returns:
            Dictionary with explanation components
        """
        # Step 1: Rule-based analysis (always runs)
        trend_result = TrendAgent.analyze(chain_data)
        projection_result = ProjectionAgent.analyze(chain_data)

        if self._use_fallback:
            return self._build_fallback_explanation(
                chain_data, trend_result, projection_result
            )

        try:
            return asyncio.run(
                self._async_explain_chain(chain_data, trend_result, projection_result)
            )
        except Exception as e:
            print(f"  [WARN] AI storytelling failed: {e}. Using fallback.")
            return self._build_fallback_explanation(
                chain_data, trend_result, projection_result
            )

    async def _async_explain_chain(
        self,
        chain_data: Dict[str, Any],
        trend_result: Dict[str, Any],
        projection_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Async AI-powered chain explanation."""
        prompt = self._build_chain_prompt(chain_data, trend_result, projection_result)

        termination = MaxMessageTermination(max_messages=6) | TextMentionTermination(
            "CHAIN ANALYSIS COMPLETE"
        )

        team = RoundRobinGroupChat(
            participants=[
                self.trend_narrator_agent,
                self.projection_narrator_agent,
            ],
            termination_condition=termination,
        )

        result = await team.run(task=prompt)

        # Extract AI narratives
        ai_trend = ""
        ai_projection = ""
        for msg in result.messages:
            source = getattr(msg, "source", "")
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                if source == "TrendNarratorAgent":
                    ai_trend = content
                elif source == "ProjectionNarratorAgent":
                    ai_projection = content.replace("CHAIN ANALYSIS COMPLETE", "").strip()

        return self._build_explanation(
            chain_data, trend_result, projection_result, ai_trend, ai_projection
        )

    def _build_chain_prompt(
        self,
        chain_data: Dict[str, Any],
        trend_result: Dict[str, Any],
        projection_result: Dict[str, Any],
    ) -> str:
        """Build prompt for AI agents."""
        lines = [
            "ANOMALY CHAIN LIFECYCLE ANALYSIS",
            "",
            f"Chain ID: {chain_data.get('chain_id', 'N/A')}",
            "",
            "DEPTH HISTORY:",
            f"  2007: {chain_data.get('depth_2007', 0):.1f}%",
            f"  2015: {chain_data.get('depth_2015', 0):.1f}%",
            f"  2022: {chain_data.get('depth_2022', 0):.1f}%",
            "",
            "GROWTH RATES:",
            f"  2007-2015 (8 years): {chain_data.get('growth_rate_07_15', 0):.3f} pp/yr",
            f"  2015-2022 (7 years): {chain_data.get('growth_rate_15_22', 0):.3f} pp/yr",
            "",
            f"ACCELERATION: {chain_data.get('acceleration', 0):+.3f} pp/yr²",
            f"TREND: {trend_result['classification']} ({trend_result['severity']})",
            "",
            "MATCH CONFIDENCE:",
            f"  2007→2015: {chain_data.get('match_confidence_07_15', 0):.3f}",
            f"  2015→2022: {chain_data.get('match_confidence_15_22', 0):.3f}",
            "",
            f"PROJECTION: {projection_result['projection_text']}",
            f"URGENCY: {projection_result['urgency']}",
            "",
            "Please analyze this anomaly's lifecycle:",
            "1. TrendNarratorAgent: Explain the growth pattern and what it means",
            "2. ProjectionNarratorAgent: Project future state and recommend action",
        ]
        return "\n".join(lines)

    def _build_explanation(
        self,
        chain_data: Dict[str, Any],
        trend_result: Dict[str, Any],
        projection_result: Dict[str, Any],
        ai_trend: str,
        ai_projection: str,
    ) -> Dict[str, Any]:
        """Build complete explanation from all agent outputs."""
        chain_id = chain_data.get("chain_id", "unknown")
        depth_2007 = chain_data.get("depth_2007", 0)
        depth_2015 = chain_data.get("depth_2015", 0)
        depth_2022 = chain_data.get("depth_2022", 0)

        # Build lifecycle narrative
        narrative = (
            f"This anomaly was first detected in 2007 at {depth_2007:.1f}% depth. "
            f"By 2015, it had grown to {depth_2015:.1f}% (growth rate: "
            f"{chain_data.get('growth_rate_07_15', 0):.2f} pp/yr over 8 years). "
            f"By 2022, it reached {depth_2022:.1f}% (growth rate: "
            f"{chain_data.get('growth_rate_15_22', 0):.2f} pp/yr over 7 years). "
        )

        if ai_trend:
            narrative += f"\n\nTrend Analysis: {ai_trend}"
        else:
            narrative += f"\n\nTrend Analysis: {trend_result['analysis']}"

        if ai_projection:
            narrative += f"\n\nProjection: {ai_projection}"
        else:
            narrative += f"\n\nProjection: {projection_result['projection_text']}"

        # Determine recommendation
        urgency = projection_result["urgency"]
        if urgency == "IMMEDIATE":
            recommendation = (
                "IMMEDIATE ACTION REQUIRED. Schedule excavation and direct assessment. "
                "This anomaly poses a near-term integrity threat."
            )
        elif urgency == "NEAR_TERM":
            recommendation = (
                "Schedule repair within the next inspection cycle (3-7 years). "
                "Increase monitoring frequency for this location."
            )
        elif urgency == "SCHEDULED":
            recommendation = (
                "Include in next scheduled maintenance program. "
                "Continue standard monitoring."
            )
        else:
            recommendation = (
                "Continue standard monitoring. No immediate action required. "
                "Reassess at next inspection."
            )

        # Gather concerns
        concerns = []
        if trend_result["classification"] == "ACCELERATING":
            concerns.append(
                f"Growth is accelerating ({trend_result['acceleration']:+.3f} pp/yr²)"
            )
        if depth_2022 > 60:
            concerns.append(f"Current depth ({depth_2022:.1f}%) exceeds 60% threshold")
        if chain_data.get("growth_rate_15_22", 0) > 5.0:
            concerns.append(
                f"Rapid growth rate ({chain_data.get('growth_rate_15_22', 0):.2f} pp/yr) "
                f"exceeds ASME B31.8S high-risk threshold"
            )
        min_confidence = min(
            chain_data.get("match_confidence_07_15", 1.0),
            chain_data.get("match_confidence_15_22", 1.0),
        )
        if min_confidence < 0.7:
            concerns.append(
                f"Low match confidence ({min_confidence:.3f}) - verify chain linkage"
            )

        return {
            "chain_id": chain_id,
            "trend_classification": trend_result["classification"],
            "urgency_level": urgency,
            "lifecycle_narrative": narrative,
            "trend_analysis": ai_trend if ai_trend else trend_result["analysis"],
            "projection_analysis": (
                ai_projection if ai_projection else projection_result["projection_text"]
            ),
            "years_to_critical": projection_result["years_to_critical"],
            "recommendation": recommendation,
            "concerns": concerns,
            "risk_score": chain_data.get("risk_score", 0),
        }

    def _build_fallback_explanation(
        self,
        chain_data: Dict[str, Any],
        trend_result: Dict[str, Any],
        projection_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build explanation without AI agents (rule-based fallback)."""
        return self._build_explanation(
            chain_data, trend_result, projection_result, "", ""
        )

    def explain_chains_batch(
        self,
        chains: List[Dict[str, Any]],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate explanations for multiple chains.

        Args:
            chains: List of chain data dictionaries
            top_n: Number of top chains to explain (by risk score)

        Returns:
            List of explanation dictionaries
        """
        # Sort by risk score and take top N
        sorted_chains = sorted(
            chains, key=lambda c: c.get("risk_score", 0), reverse=True
        )[:top_n]

        explanations = []
        for i, chain in enumerate(sorted_chains, 1):
            print(f"  [{i}/{len(sorted_chains)}] Explaining chain {chain.get('chain_id', 'N/A')}...")
            explanation = self.explain_chain(chain)
            explanations.append(explanation)

        return explanations

