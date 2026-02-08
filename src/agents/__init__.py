"""
Agentic Match Explanation System
=================================

Multi-agent system using AutoGen for explaining anomaly matches.

Agents:
- AlignmentAgent: Verifies distance correction
- MatchingAgent: Explains similarity scores
- ValidatorAgent: Assesses match quality
- ExplainerAgent: Synthesizes explanations
- TrendAgent: Analyzes growth acceleration across intervals
- ProjectionAgent: Projects future state

Author: ILI Data Alignment System
Date: 2024
Updated: 2025 - Added Chain Storyteller agents
"""

from .match_explainer import MatchExplainerSystem
from .chain_storyteller import ChainStorytellerSystem, TrendAgent, ProjectionAgent

__all__ = [
    'MatchExplainerSystem',
    'ChainStorytellerSystem',
    'TrendAgent',
    'ProjectionAgent',
]
