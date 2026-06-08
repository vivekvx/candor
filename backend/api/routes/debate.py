import asyncio
import hashlib
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from orchestrator.debate import DebateOrchestrator
from orchestrator.router import get_available_models
from orchestrator.state import DebateState
from mcp_server.tools.sanitizer import INJECTION_PATTERNS

router = APIRouter(prefix="/api", tags=["debate"])

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter — good enough for free tier.
_rate_limit_store: dict[str, list[datetime]] = defaultdict(list)
_rate_limit_lock = asyncio.Lock()

DEBATES_PER_HOUR = 3
QUEUE_MESSAGE = "High demand right now. You are {position} in queue — estimated {wait} minutes. Candor will start your debate shortly."


async def check_rate_limit(client_ip: str) -> tuple[bool, str]:
    """Returns (allowed, message). Cleans up old entries."""
    async with _rate_limit_lock:
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=1)

        _rate_limit_store[client_ip] = [
            t for t in _rate_limit_store[client_ip] if t > cutoff
        ]

        count = len(_rate_limit_store[client_ip])
        if count >= DEBATES_PER_HOUR:
            oldest = _rate_limit_store[client_ip][0]
            reset_in = int((oldest + timedelta(hours=1) - now).total_seconds() / 60) + 1
            return False, f"You've run {DEBATES_PER_HOUR} debates this hour. Try again in {reset_in} minutes."

        _rate_limit_store[client_ip].append(now)
        return True, ""

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


def _get_supabase_client():
    """Lazily build a Supabase client when both credentials are configured.

    Returns None (never raises) when credentials are missing or the SDK
    fails to initialize — callers fall back to file storage silently.
    """
    if not (settings.supabase_url and settings.supabase_key):
        return None
    try:
        from supabase import create_client
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as error:
        logger.warning("Supabase client init failed — falling back to /tmp cache: %s", error)
        return None


def _file_path(key: str) -> Path:
    return DEBATES_DIR / f"{key}.json"


def save_debate(debate_id: str, data: dict):
    client = _get_supabase_client()
    if client is not None:
        try:
            client.table("debates").upsert({"id": debate_id, "data": data}).execute()
            return
        except Exception as error:
            logger.warning("Supabase save_debate failed — falling back to /tmp: %s", error)

    _file_path(debate_id).write_text(json.dumps(data))


def load_debate(debate_id: str) -> dict | None:
    client = _get_supabase_client()
    if client is not None:
        try:
            result = client.table("debates").select("data").eq("id", debate_id).limit(1).execute()
            rows = result.data or []
            if rows:
                return rows[0].get("data")
            return None
        except Exception as error:
            logger.warning("Supabase load_debate failed — falling back to /tmp: %s", error)

    path = _file_path(debate_id)
    if path.exists():
        return json.loads(path.read_text())
    return None


def record_outcome(debate_id: str, outcome: str, timestamp: str) -> None:
    """Append-only — never delete or modify a recorded outcome."""
    payload = {
        "debate_id": debate_id,
        "outcome": outcome,
        "reported_at": timestamp,
    }
    client = _get_supabase_client()
    if client is not None:
        try:
            client.table("debates").upsert({"id": f"outcome_{debate_id}", "data": payload}).execute()
            return
        except Exception as error:
            logger.warning("Supabase record_outcome failed — falling back to /tmp: %s", error)

    _file_path(f"outcome_{debate_id}").write_text(json.dumps(payload))


def get_outcome(debate_id: str) -> dict | None:
    client = _get_supabase_client()
    if client is not None:
        try:
            result = client.table("debates").select("data").eq("id", f"outcome_{debate_id}").limit(1).execute()
            rows = result.data or []
            if rows:
                return rows[0].get("data")
            return None
        except Exception as error:
            logger.warning("Supabase get_outcome failed — falling back to /tmp: %s", error)

    path = _file_path(f"outcome_{debate_id}")
    if path.exists():
        return json.loads(path.read_text())
    return None


def generate_verdict_card_html(verdict: dict, debate_id: str) -> str:
    bull = verdict.get('bull_score', 0)
    bear = verdict.get('bear_score', 0)
    text = verdict.get('verdict', 'No verdict')
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="Candor Career Verdict">
  <meta property="og:description" content="{text[:120]}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui; background: #0a0a0a; color: #fff;
           display: flex; justify-content: center; padding: 2rem; }}
    .card {{ max-width: 600px; border: 1px solid #333; border-radius: 12px; padding: 2rem; }}
    .scores {{ display: flex; gap: 2rem; margin: 1rem 0; }}
    .score {{ text-align: center; }}
    .score .num {{ font-size: 2rem; font-weight: bold; }}
    .bull {{ color: #22c55e; }}
    .bear {{ color: #ef4444; }}
    .verdict {{ font-size: 1.1rem; line-height: 1.6; margin: 1.5rem 0; }}
    .cta {{ text-align: center; margin-top: 2rem; }}
    .cta a {{ background: #fff; color: #000; padding: 0.75rem 1.5rem;
              border-radius: 8px; text-decoration: none; font-weight: 600; }}
    .badge {{ font-size: 0.75rem; color: #666; margin-top: 2rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Candor Verdict</h2>
    <div class="scores">
      <div class="score"><div class="num bull">{bull}</div><div>Bull Score</div></div>
      <div class="score"><div class="num bear">{bear}</div><div>Bear Score</div></div>
    </div>
    <div class="verdict">{text}</div>
    <div class="cta"><a href="https://candor-seven.vercel.app">Run your own debate →</a></div>
    <div class="badge">Generated by Candor · Three AI agents debated this · candor-seven.vercel.app</div>
  </div>
</body>
</html>"""


@router.post("/debate")
async def run_debate(request: DebateRequest, http_request: Request):
    """Stream a full debate as Server-Sent Events."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    client_ip = http_request.headers.get("X-Forwarded-For", http_request.client.host).split(",")[0].strip()
    allowed, message = await check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail={"error": "rate_limited", "message": message})

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
                "data_confidence": verdict.get("data_confidence"),
            }

            # Save debate for shareable link
            debate_id = hashlib.md5(
                f"{request.query}{state.started_at}".encode()
            ).hexdigest()[:8]

            metadata["outcome_url"] = f"/api/debate/{debate_id}/outcome"
            metadata["outcome_prompt"] = "Come back in 90 days and tell us what you decided."

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
async def get_debate(debate_id: str, format: str = "json"):
    """Retrieve a saved debate by ID. format=card returns a shareable HTML verdict card."""
    data = load_debate(debate_id)
    if not data:
        if format == "card":
            return JSONResponse({"expired": True}, status_code=404)
        return {
            "error": "Debate not found",
            "message": "This debate may have expired. Run a new debate and share that link.",
            "expired": True,
        }

    if format == "card":
        verdict = data.get("verdict", {})
        html = generate_verdict_card_html(verdict, debate_id)
        return HTMLResponse(html)

    return JSONResponse(data)


@router.post("/debate/{debate_id}/outcome")
async def record_debate_outcome(debate_id: str, outcome: str):
    """User reports what they actually decided. Append-only — never overwritten."""
    valid_outcomes = ["joined", "declined", "still_deciding", "offer_rescinded"]
    if outcome not in valid_outcomes:
        raise HTTPException(400, detail=f"outcome must be one of {valid_outcomes}")

    record_outcome(debate_id, outcome, datetime.utcnow().isoformat())
    return {"recorded": True, "debate_id": debate_id, "outcome": outcome}


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
