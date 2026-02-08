"""
Explain Router
==============

Endpoints for AI-powered explanations of matches and chains.
"""

from fastapi import APIRouter, HTTPException

from src.api.schemas.requests import ExplainChainRequest, ExplainMatchRequest
from src.api.schemas.responses import ChainExplanationResponse, MatchExplanationResponse

router = APIRouter()


@router.post("/explain/chain", response_model=ChainExplanationResponse)
async def explain_chain(request: ExplainChainRequest):
    """
    Generate an AI-powered explanation for an anomaly chain.

    Uses 6 specialized agents to tell the full lifecycle story of the anomaly:
    - TrendAgent analyzes growth acceleration
    - ProjectionAgent projects future state
    - Plus 4 existing agents for match quality analysis
    """
    try:
        from src.agents.chain_storyteller import ChainStorytellerSystem

        storyteller = ChainStorytellerSystem()

        chain_data = {
            "chain_id": request.chain_id,
            "anomaly_2007_id": request.anomaly_2007_id,
            "anomaly_2015_id": request.anomaly_2015_id,
            "anomaly_2022_id": request.anomaly_2022_id,
            "depth_2007": request.depth_2007,
            "depth_2015": request.depth_2015,
            "depth_2022": request.depth_2022,
            "growth_rate_07_15": request.growth_rate_07_15,
            "growth_rate_15_22": request.growth_rate_15_22,
            "acceleration": request.acceleration,
            "match_confidence_07_15": request.match_confidence_07_15,
            "match_confidence_15_22": request.match_confidence_15_22,
            "risk_score": request.risk_score,
        }

        result = storyteller.explain_chain(chain_data)

        return ChainExplanationResponse(
            chain_id=result["chain_id"],
            trend_classification=result["trend_classification"],
            urgency_level=result["urgency_level"],
            lifecycle_narrative=result["lifecycle_narrative"],
            trend_analysis=result["trend_analysis"],
            projection_analysis=result["projection_analysis"],
            recommendation=result["recommendation"],
            concerns=result.get("concerns", []),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain explanation failed: {str(e)}")


@router.post("/explain/match", response_model=MatchExplanationResponse)
async def explain_match(request: ExplainMatchRequest):
    """
    Generate an AI-powered explanation for a single anomaly match.

    Uses 4 specialized agents:
    1. AlignmentAgent - Verifies distance correction
    2. MatchingAgent - Explains similarity scores
    3. ValidatorAgent - Assesses match quality
    4. ExplainerAgent - Synthesizes explanation
    """
    try:
        from src.agents.match_explainer import MatchExplainerSystem

        explainer = MatchExplainerSystem()
        result = explainer.explain_match(
            request.anomaly1,
            request.anomaly2,
            request.match_result,
        )

        return MatchExplanationResponse(
            match_id=result["match_id"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            recommendation=result["recommendation"],
            concerns=result.get("concerns", []),
            similarity_score=result.get("similarity_score", 0.0),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Match explanation failed: {str(e)}")

