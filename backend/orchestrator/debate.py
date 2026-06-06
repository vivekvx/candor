import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import litellm

from backend.config import settings
from backend.orchestrator.router import get_model_for_step, get_fallback_models
from backend.orchestrator.state import DebateState

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

    raise last_error or RuntimeError(f"All models exhausted for step {step}")


class DebateOrchestrator:
    def __init__(self, state: DebateState):
        self.state = state

    async def run_round_one(self) -> tuple[dict, dict]:
        advocate_model = get_model_for_step("advocate_round1", self.state.model)
        challenger_model = get_model_for_step("challenger_round1", self.state.model)

        advocate_prompt = _load_prompt("advocate")
        challenger_prompt = _load_prompt("challenger").replace("{advocate_output}", "")

        advocate_out, challenger_out = await asyncio.gather(
            _call_llm(advocate_model, advocate_prompt, self.state.query, self.state, step="advocate_round1"),
            _call_llm(challenger_model, challenger_prompt, self.state.query, self.state, step="challenger_round1"),
        )

        self.state.advocate_research = json.dumps(advocate_out)
        self.state.challenger_research = json.dumps(challenger_out)
        self.state.round = 1
        return advocate_out, challenger_out

    async def run_cross_examination(self) -> tuple[dict, dict]:
        advocate_model = get_model_for_step("advocate_round2", self.state.model)
        challenger_model = get_model_for_step("challenger_round2", self.state.model)

        challenger_prompt = _load_prompt("challenger").replace(
            "{advocate_output}", self.state.advocate_research
        )
        advocate_rebuttal_prompt = (
            _load_prompt("advocate")
            + f"\n\nThe Challenger has raised these concerns:\n{self.state.challenger_research}\n\n"
            "Now reinforce your weakest points and address their strongest counter-arguments."
        )

        adv_rebuttal, chall_rebuttal = await asyncio.gather(
            _call_llm(advocate_model, advocate_rebuttal_prompt, self.state.query, self.state, step="advocate_round2"),
            _call_llm(challenger_model, challenger_prompt, self.state.query, self.state, step="challenger_round2"),
        )

        self.state.advocate_rebuttal = json.dumps(adv_rebuttal)
        self.state.challenger_rebuttal = json.dumps(chall_rebuttal)
        self.state.round = 2
        return adv_rebuttal, chall_rebuttal

    async def run_arbitrator(self) -> dict:
        model = get_model_for_step("arbitrator", self.state.model)

        system_prompt = (
            _load_prompt("arbitrator")
            .replace("{advocate_output}", self.state.advocate_research)
            .replace("{challenger_output}", self.state.challenger_research)
        )

        full_transcript = (
            f"Original query: {self.state.query}\n\n"
            f"Advocate Round 1: {self.state.advocate_research}\n\n"
            f"Challenger Round 1: {self.state.challenger_research}\n\n"
            f"Advocate Rebuttal: {self.state.advocate_rebuttal}\n\n"
            f"Challenger Rebuttal: {self.state.challenger_rebuttal}"
        )

        verdict = await _call_llm(model, system_prompt, full_transcript, self.state, step="arbitrator")
        self.state.verdict = verdict
        self.state.completed_at = time.time()
        self.state.round = 3
        return verdict

    async def run_full_debate(self) -> DebateState:
        await self.run_round_one()
        await self.run_cross_examination()
        await self.run_arbitrator()
        return self.state
