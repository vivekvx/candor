import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import litellm

from config import settings
from orchestrator.router import get_load_balanced_model, get_fallback_models
from orchestrator.state import DebateState
from orchestrator.agent_loop import run_agent_with_tools, parse_json_response

os.environ["GROQ_API_KEY"] = settings.groq_api_key or ""

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "agents" / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


async def _call_llm(model: str, system_prompt: str, user_content: str, state: DebateState, step: str = "") -> dict[str, Any]:
    models_to_try = [model] + get_fallback_models(model)
    last_error = None

    for attempt_model in models_to_try:
        try:
            response = await litellm.acompletion(
                model=attempt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
                # Bounds cost/latency and stretches free-tier daily quotas —
                # the arbitrator's verdict JSON is the largest structured
                # output in the system but still comfortably fits in 2000.
                max_tokens=2000,
            )
            usage = response.usage
            cost = 0.0
            if usage:
                try:
                    cost = litellm.completion_cost(model=attempt_model, completion_response=response)
                except Exception:
                    cost = 0.0
                state.add_usage(
                    input_tokens=usage.prompt_tokens or 0,
                    output_tokens=usage.completion_tokens or 0,
                    cost=cost or 0.0,
                )
            if step:
                state.step_costs[step] = round(cost or 0.0, 8)
            if attempt_model != model:
                logger.warning("Fell back from %s to %s for step %s", model, attempt_model, step)
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM JSON response: %s", content[:200])
                return {"error": "Failed to parse model response", "raw": content}

        except litellm.RateLimitError as e:
            last_error = e
            logger.warning("Rate limit on %s (step=%s), trying fallback", attempt_model, step)
            continue
        except litellm.AuthenticationError as e:
            last_error = e
            logger.warning("Auth error on %s (step=%s), trying fallback", attempt_model, step)
            continue
        except litellm.BadRequestError as e:
            err_str = str(e).lower()
            if "credit" in err_str or "billing" in err_str or "quota" in err_str:
                last_error = e
                logger.warning("Billing error on %s (step=%s), trying fallback", attempt_model, step)
                continue
            raise
        except litellm.NotFoundError as e:
            last_error = e
            logger.warning("Model not found %s (step=%s), trying fallback", attempt_model, step)
            continue

    raise last_error or RuntimeError(f"All models exhausted for step {step}")


def _ensure_valid_verdict(verdict: dict) -> dict:
    """
    Guard against a malformed arbitrator response reaching the frontend.

    _call_llm returns {"error": "Failed to parse model response", "raw": ...}
    when the model's JSON doesn't parse — that shape lacks bull_score/
    bear_score/verdict that the frontend expects, and was being stored and
    streamed to the user verbatim as if it were a real verdict. Detect that
    and substitute a safe, complete fallback shape with all expected keys
    present (zeroed scores, an explanatory message) instead.
    """
    if isinstance(verdict, dict) and "bull_score" in verdict and "verdict" in verdict:
        return verdict

    logger.error("Arbitrator returned a malformed verdict shape: %s", verdict)
    return {
        "error": verdict.get("error", "Arbitrator returned a malformed response")
        if isinstance(verdict, dict) else "Arbitrator returned a malformed response",
        "bull_score": 0,
        "bear_score": 0,
        "verdict": "Could not generate a verdict — please try the debate again.",
        "strongest_bull_point": "",
        "strongest_bear_point": "",
        "what_to_find_out": [],
        "if_i_were_you": "The AI arbitrator's response could not be parsed. Please retry the debate.",
        "negotiation_tip": "",
    }


def _sanitize_agent_result(result: dict) -> dict:
    """
    Replace infrastructure errors (e.g. "All AI providers rate limited") with a
    neutral placeholder before the result is stored/passed to the Arbitrator.

    Without this, the Arbitrator reads error objects as if they were research
    findings — producing verdicts like "the AI is rate limited, indicating
    unsustainable growth". Deterministic filter, not LLM-instruction-dependent.
    Only strips results that are purely error objects — partial research with
    real data passes through untouched.
    """
    if isinstance(result, dict) and result.get("error"):
        return {"status": "unavailable", "reason": "research could not be completed"}
    content = result.get("content") if isinstance(result, dict) else None
    if isinstance(content, dict) and content.get("error"):
        return {"status": "unavailable", "reason": "research could not be completed"}
    return result


class DebateOrchestrator:
    def __init__(self, state: DebateState):
        self.state = state

    async def run_round_one(self) -> tuple[dict, dict]:
        """
        Run the first research round for both Advocate and Challenger in parallel.

        Both agents use the tool-calling loop so they can autonomously call
        MCA intelligence, company health, compensation, and other tools before
        producing their initial research output.
        """
        advocate_model = get_load_balanced_model("advocate_round1", self.state.model)
        challenger_model = get_load_balanced_model("challenger_round1", self.state.model)

        advocate_prompt = _load_prompt("advocate")
        challenger_prompt = _load_prompt("challenger").replace("{advocate_output}", "")

        # return_exceptions=True keeps one agent's failure from cancelling the
        # other mid-flight and silently killing the SSE stream — instead both
        # results (or exceptions) come back so we can surface a clear error.
        advocate_raw, challenger_raw = await asyncio.gather(
            run_agent_with_tools(advocate_prompt, self.state.query, advocate_model, "Advocate"),
            run_agent_with_tools(challenger_prompt, self.state.query, challenger_model, "Challenger"),
            return_exceptions=True,
        )

        for agent_name, raw_result in (("Advocate", advocate_raw), ("Challenger", challenger_raw)):
            if isinstance(raw_result, BaseException):
                logger.error("Round 1 %s task raised: %s", agent_name, raw_result)
                raise RuntimeError(
                    f"Round 1 failed — {agent_name} agent raised an unrecoverable error: {raw_result}"
                )

        advocate_out = _sanitize_agent_result(parse_json_response(advocate_raw))
        challenger_out = _sanitize_agent_result(parse_json_response(challenger_raw))

        self.state.advocate_research = json.dumps(advocate_out)
        self.state.challenger_research = json.dumps(challenger_out)
        self.state.round = 1
        return advocate_out, challenger_out

    async def run_cross_examination(self) -> tuple[dict, dict]:
        """
        Run the rebuttal round with tool-calling enabled for both agents.

        Advocate sees the Challenger's concerns and can call tools to
        reinforce weak points. Challenger sees the Advocate's full case
        and calls tools to find contradicting evidence.
        """
        advocate_model = get_load_balanced_model("advocate_round2", self.state.model)
        challenger_model = get_load_balanced_model("challenger_round2", self.state.model)

        challenger_prompt = _load_prompt("challenger").replace(
            "{advocate_output}", self.state.advocate_research
        )
        advocate_rebuttal_prompt = (
            _load_prompt("advocate")
            + f"\n\nThe Challenger has raised these concerns:\n{self.state.challenger_research}\n\n"
            "Now reinforce your weakest points and address their strongest counter-arguments."
        )

        # Same return_exceptions=True guard as Round 1 — without it, one
        # agent's failure cancels its sibling and can surface as
        # asyncio.CancelledError (a BaseException, not Exception), which
        # would silently kill the SSE stream past cross_examination_start.
        adv_raw, chall_raw = await asyncio.gather(
            run_agent_with_tools(advocate_rebuttal_prompt, self.state.query, advocate_model, "Advocate-Rebuttal"),
            run_agent_with_tools(challenger_prompt, self.state.query, challenger_model, "Challenger-Rebuttal"),
            return_exceptions=True,
        )

        for agent_name, raw_result in (("Advocate-Rebuttal", adv_raw), ("Challenger-Rebuttal", chall_raw)):
            if isinstance(raw_result, BaseException):
                logger.error("Round 2 %s task raised: %s", agent_name, raw_result)
                raise RuntimeError(
                    f"Round 2 failed — {agent_name} agent raised an unrecoverable error: {raw_result}"
                )

        adv_rebuttal = _sanitize_agent_result(parse_json_response(adv_raw))
        chall_rebuttal = _sanitize_agent_result(parse_json_response(chall_raw))

        self.state.advocate_rebuttal = json.dumps(adv_rebuttal)
        self.state.challenger_rebuttal = json.dumps(chall_rebuttal)
        self.state.round = 2
        return adv_rebuttal, chall_rebuttal

    async def run_arbitrator(self) -> dict:
        model = get_load_balanced_model("arbitrator", self.state.model)

        profile_context = ""
        if self.state.user_profile:
            p = self.state.user_profile
            profile_context = (
                "\n\nUSER CONTEXT (calibrate your advice to this person):\n"
                f"- Role: {p.get('role') or 'Not specified'}\n"
                f"- Experience: {p.get('experience') or 'Not specified'}\n"
                f"- Current CTC: {p.get('current_ctc_lpa') or 'Not specified'} LPA\n"
                f"- Risk appetite: {p.get('risk_appetite') or 'Balanced'}\n"
            )

        system_prompt = (
            _load_prompt("arbitrator")
            .replace("{advocate_output}", self.state.advocate_research)
            .replace("{challenger_output}", self.state.challenger_research)
            + profile_context
        )

        full_transcript = (
            f"Original query: {self.state.query}\n\n"
            f"Advocate Round 1: {self.state.advocate_research}\n\n"
            f"Challenger Round 1: {self.state.challenger_research}\n\n"
            f"Advocate Rebuttal: {self.state.advocate_rebuttal}\n\n"
            f"Challenger Rebuttal: {self.state.challenger_rebuttal}"
        )

        verdict = await _call_llm(model, system_prompt, full_transcript, self.state, step="arbitrator")
        verdict = _ensure_valid_verdict(verdict)
        self.state.verdict = verdict
        self.state.completed_at = time.time()
        self.state.round = 3
        return verdict

    async def run_full_debate(self) -> DebateState:
        await self.run_round_one()
        await self.run_cross_examination()
        await self.run_arbitrator()
        return self.state
