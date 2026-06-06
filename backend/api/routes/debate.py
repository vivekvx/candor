import json
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.orchestrator.debate import DebateOrchestrator
from backend.orchestrator.router import get_available_models
from backend.orchestrator.state import DebateState

router = APIRouter(prefix="/api", tags=["debate"])


class DebateRequest(BaseModel):
    query: str
    model: str = "groq/llama-3.3-70b-versatile"


@router.post("/debate")
async def run_debate(request: DebateRequest):
    """Stream a full debate as Server-Sent Events."""

    async def generate():
        try:
            state = DebateState(query=request.query, model=request.model)
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
            yield f"data: {json.dumps({'type': 'complete', 'metadata': metadata})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/models")
async def get_models():
    return {"models": get_available_models()}
