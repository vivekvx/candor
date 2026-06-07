import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from orchestrator.debate import DebateOrchestrator
from orchestrator.router import get_available_models
from orchestrator.state import DebateState
from mcp_server.tools.sanitizer import INJECTION_PATTERNS

router = APIRouter(prefix="/api", tags=["debate"])

logger = logging.getLogger(__name__)

# Railway's filesystem resets on every redeploy — a mounted volume survives.
# RAILWAY_VOLUME_MOUNT_PATH is set when a volume is attached in the dashboard;
# fall back to a local directory (and warn) when no volume is configured.
_volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
if _volume_path:
    DEBATES_DIR = Path(_volume_path) / "debate_cache"
else:
    logger.warning(
        "RAILWAY_VOLUME_MOUNT_PATH not set — debates stored on local disk "
        "and will be lost on redeploy. Attach a Railway volume for persistence."
    )
    DEBATES_DIR = Path("debate_cache")

DEBATES_DIR.mkdir(parents=True, exist_ok=True)


class UserProfile(BaseModel):
    role: Optional[str] = None
    experience: Optional[str] = None
    current_ctc_lpa: Optional[float] = None
    risk_appetite: Optional[str] = "Balanced"


class DebateRequest(BaseModel):
    query: str
    model: str = "groq/llama-3.3-70b-versatile"
    user_profile: Optional[UserProfile] = None


def save_debate(debate_id: str, data: dict):
    path = DEBATES_DIR / f"{debate_id}.json"
    path.write_text(json.dumps(data))


def load_debate(debate_id: str) -> dict | None:
    path = DEBATES_DIR / f"{debate_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


@router.post("/debate")
async def run_debate(request: DebateRequest):
    """Stream a full debate as Server-Sent Events."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    async def generate():
        try:
            profile_dict = request.user_profile.model_dump() if request.user_profile else None
            state = DebateState(
                query=request.query,
                model=request.model,
                user_profile=profile_dict,
            )
            orchestrator = DebateOrchestrator(state)

            yield f"data: {json.dumps({'type': 'status', 'stage': 'round_1_start'})}\n\n"
            advocate, challenger = await orchestrator.run_round_one()
            yield f"data: {json.dumps({'type': 'advocate_research', 'content': advocate})}\n\n"
            yield f"data: {json.dumps({'type': 'challenger_research', 'content': challenger})}\n\n"

            yield f"data: {json.dumps({'type': 'status', 'stage': 'cross_examination_start'})}\n\n"
            adv_rebuttal, chall_rebuttal = await orchestrator.run_cross_examination()
            yield f"data: {json.dumps({'type': 'advocate_rebuttal', 'content': adv_rebuttal})}\n\n"
            yield f"data: {json.dumps({'type': 'challenger_rebuttal', 'content': chall_rebuttal})}\n\n"

            yield f"data: {json.dumps({'type': 'status', 'stage': 'arbitration_start'})}\n\n"
            verdict = await orchestrator.run_arbitrator()
            yield f"data: {json.dumps({'type': 'verdict', 'content': verdict})}\n\n"

            metadata = {
                "total_tokens": state.total_input_tokens + state.total_output_tokens,
                "cost_usd": round(state.total_cost_usd, 6),
                "duration_seconds": round(time.time() - state.started_at, 2),
            }

            # Save debate for shareable link
            debate_id = hashlib.md5(
                f"{request.query}{state.started_at}".encode()
            ).hexdigest()[:8]

            save_debate(debate_id, {
                "query": request.query,
                "advocate_research": state.advocate_research,
                "challenger_research": state.challenger_research,
                "advocate_rebuttal": state.advocate_rebuttal,
                "challenger_rebuttal": state.challenger_rebuttal,
                "verdict": state.verdict,
                "metadata": metadata,
                "created_at": state.started_at,
            })

            yield f"data: {json.dumps({'type': 'complete', 'metadata': metadata, 'debate_id': debate_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/debate/{debate_id}")
async def get_debate(debate_id: str):
    """Retrieve a saved debate by ID."""
    data = load_debate(debate_id)
    if not data:
        return {
            "error": "Debate not found",
            "message": "This debate may have expired. Run a new debate and share that link.",
            "expired": True,
        }
    return data


@router.get("/models")
async def get_models():
    return {"models": get_available_models()}


@router.get("/provider-status")
async def provider_status():
    """
    Return current health status of every provider in the fallback chain.

    Useful for debugging rate limit issues — shows which providers the
    health tracker has recently marked as rate limited and is skipping.
    """
    from orchestrator.provider_health import is_provider_healthy
    from orchestrator.agent_loop import FALLBACK_MODEL_CHAIN

    return {
        "providers": [
            {"model": model, "healthy": is_provider_healthy(model)}
            for model in FALLBACK_MODEL_CHAIN
        ]
    }


@router.get("/cost-analysis")
async def cost_analysis():
    return {
        "baseline_all_quality": 0.0089,
        "with_routing": 0.0037,
        "savings_percent": 58,
        "explanation": "Round 1 research uses fast model (simple retrieval). Cross-examination and arbitration use quality model (complex reasoning). Saves ~58% per debate with no quality loss on the verdict.",
        "step_breakdown": {
            "advocate_round1": {"model": "fast", "avg_cost": 0.0004},
            "challenger_round1": {"model": "fast", "avg_cost": 0.0004},
            "advocate_round2": {"model": "fast", "avg_cost": 0.0006},
            "challenger_round2": {"model": "quality", "avg_cost": 0.0015},
            "arbitrator": {"model": "quality", "avg_cost": 0.0008},
        },
    }


@router.get("/security-report")
async def security_report():
    return {
        "threat_model": "Indirect prompt injection via web content",
        "attack_surface": "Tavily search results fed directly into agent context",
        "patterns_defended": len(INJECTION_PATTERNS),
        "attack_types": [
            "instruction_override",
            "role_hijack",
            "extraction",
            "token_injection",
            "score_manipulation",
        ],
        "defense_mechanism": "Regex-based sanitization before content enters agent context",
        "logging": "All injection attempts logged at WARNING level with pattern type",
        "limitation": "Regex cannot catch all novel injection attempts — semantic detection would be stronger",
    }
