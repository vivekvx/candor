import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import litellm

from backend.orchestrator.router import AgentRole, get_model_for_role
from backend.orchestrator.state import DebateState

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "agents" / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


async def _call_llm(model: str, system_prompt: str, user_content: str, state: DebateState) -> dict[str, Any]:
    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    usage = response.usage
    if usage:
        cost = litellm.completion_cost(completion_response=response)
        state.add_usage(
            input_tokens=usage.prompt_tokens or 0,
            output_tokens=usage.completion_tokens or 0,
            cost=cost or 0.0,
        )
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM JSON response: %s", content[:200])
        return {"error": "Failed to parse model response", "raw": content}


class DebateOrchestrator:
    def __init__(self, state: DebateState):
        self.state = state

    async def run_round_one(self) -> tuple[dict, dict]:
        advocate_model = get_model_for_role(AgentRole.ADVOCATE, self.state.model if self.state.model != "groq/llama-3.3-70b-versatile" else None)
        challenger_model = get_model_for_role(AgentRole.CHALLENGER, self.state.model if self.state.model != "groq/llama-3.3-70b-versatile" else None)

        advocate_prompt = _load_prompt("advocate")
        challenger_prompt = _load_prompt("challenger").replace("{advocate_output}", "")

        advocate_out, challenger_out = await asyncio.gather(
            _call_llm(advocate_model, advocate_prompt, self.state.query, self.state),
            _call_llm(challenger_model, challenger_prompt, self.state.query, self.state),
        )

        self.state.advocate_research = json.dumps(advocate_out)
        self.state.challenger_research = json.dumps(challenger_out)
        self.state.round = 1
        return advocate_out, challenger_out

    async def run_cross_examination(self) -> tuple[dict, dict]:
        advocate_model = get_model_for_role(AgentRole.ADVOCATE, self.state.model if self.state.model != "groq/llama-3.3-70b-versatile" else None)
        challenger_model = get_model_for_role(AgentRole.CHALLENGER, self.state.model if self.state.model != "groq/llama-3.3-70b-versatile" else None)

        # Challenger attacks advocate's Round 1 output specifically
        challenger_prompt = _load_prompt("challenger").replace(
            "{advocate_output}", self.state.advocate_research
        )
        # Advocate reinforces its weakest points after seeing challenger's research
        advocate_rebuttal_prompt = (
            _load_prompt("advocate")
            + f"\n\nThe Challenger has raised these concerns:\n{self.state.challenger_research}\n\n"
            "Now reinforce your weakest points and address their strongest counter-arguments."
        )

        adv_rebuttal, chall_rebuttal = await asyncio.gather(
            _call_llm(advocate_model, advocate_rebuttal_prompt, self.state.query, self.state),
            _call_llm(challenger_model, challenger_prompt, self.state.query, self.state),
        )

        self.state.advocate_rebuttal = json.dumps(adv_rebuttal)
        self.state.challenger_rebuttal = json.dumps(chall_rebuttal)
        self.state.round = 2
        return adv_rebuttal, chall_rebuttal

    async def run_arbitrator(self) -> dict:
        model = get_model_for_role(AgentRole.ARBITRATOR, self.state.model if self.state.model != "groq/llama-3.3-70b-versatile" else None)

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

        verdict = await _call_llm(model, system_prompt, full_transcript, self.state)
        self.state.verdict = verdict
        self.state.completed_at = time.time()
        self.state.round = 3
        return verdict

    async def run_full_debate(self) -> DebateState:
        await self.run_round_one()
        await self.run_cross_examination()
        await self.run_arbitrator()
        return self.state
