"""
Agentic tool-calling loop for Candor debate agents.

An agent receives a prompt, autonomously decides which tools to call,
executes them, reads results, and repeats until it has enough information
to produce a final JSON answer. This replaces the previous single-shot
LLM call with a proper research loop.

The loop is capped at MAX_TOOL_CALLS_PER_AGENT to prevent runaway costs.
"""

import json
import logging
from typing import Any

import litellm

from backend.orchestrator.tool_schemas import DEBATE_TOOL_SCHEMAS
from backend.orchestrator.tool_executor import execute_tool_call, parse_tool_arguments

logger = logging.getLogger(__name__)

# Cap per agent per round — enough for thorough research, prevents runaway cost
MAX_TOOL_CALLS_PER_AGENT = 5


async def run_agent_with_tools(
    system_prompt: str,
    user_message: str,
    model: str,
    agent_name: str,
) -> str:
    """
    Run one debate agent through the full tool-calling loop.

    The agent calls tools autonomously until it decides it has enough
    research to write its final answer, or until MAX_TOOL_CALLS_PER_AGENT
    is reached. Returns the final response as a raw string (JSON expected).

    Args:
        system_prompt: Agent role and instructions (loaded from .md file)
        user_message: The debate query or context the agent is responding to
        model: LiteLLM model string e.g. groq/llama-3.3-70b-versatile
        agent_name: Human-readable label for logging e.g. "Advocate"

    Returns:
        Agent's final response as a string — should be valid JSON
    """
    messages = _build_initial_messages(system_prompt, user_message)
    total_tool_calls_made = 0

    logger.info("%s starting agent loop with model %s", agent_name, model)

    while total_tool_calls_made < MAX_TOOL_CALLS_PER_AGENT:
        response = await _call_llm_with_tools(model, messages)
        assistant_message = response.choices[0].message

        if not _has_tool_calls(assistant_message):
            logger.info(
                "%s finished after %d tool call(s)",
                agent_name,
                total_tool_calls_made,
            )
            return assistant_message.content or ""

        # Agent requested tools — execute them and feed results back
        messages.append(assistant_message)
        tool_result_messages = await _execute_all_tool_calls(
            assistant_message.tool_calls, agent_name
        )
        messages.extend(tool_result_messages)
        total_tool_calls_made += len(assistant_message.tool_calls)

    logger.warning(
        "%s hit tool call limit (%d) — forcing final answer",
        agent_name,
        MAX_TOOL_CALLS_PER_AGENT,
    )
    return await _get_final_answer_without_tools(model, messages)


def _build_initial_messages(system_prompt: str, user_message: str) -> list[dict]:
    """
    Build the starting conversation for an agent.

    Kept as a function so tests can verify the message structure
    without running a full agent loop.
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


async def _call_llm_with_tools(model: str, messages: list[dict]) -> Any:
    """
    Call LiteLLM with the full tool schema attached.

    tool_choice='auto' means the model decides whether to call a tool
    or answer directly — we never force it.
    """
    return await litellm.acompletion(
        model=model,
        messages=messages,
        tools=DEBATE_TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.7,
    )


def _has_tool_calls(assistant_message: Any) -> bool:
    """
    Return True if the assistant message contains one or more tool call requests.

    Defensive check — some providers return None or omit the attribute
    when no tools are called.
    """
    return (
        hasattr(assistant_message, "tool_calls")
        and assistant_message.tool_calls is not None
        and len(assistant_message.tool_calls) > 0
    )


async def _execute_all_tool_calls(
    tool_calls: list, agent_name: str
) -> list[dict]:
    """
    Execute every tool call the agent requested and return result messages.

    Each result is formatted as a 'tool' role message that LiteLLM expects
    when continuing the conversation after tool execution.
    """
    tool_result_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        raw_arguments = tool_call.function.arguments
        parsed_arguments = parse_tool_arguments(raw_arguments)

        logger.info("%s calling tool: %s", agent_name, tool_name)

        tool_result = await execute_tool_call(tool_name, parsed_arguments)

        tool_result_messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result),
        })

    return tool_result_messages


async def _get_final_answer_without_tools(model: str, messages: list[dict]) -> str:
    """
    Force a final answer from the agent with tools disabled.

    Called only when the agent has hit MAX_TOOL_CALLS_PER_AGENT.
    The accumulated tool results in messages give it enough context
    to answer without calling more tools.
    """
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""


def parse_json_response(raw_response: str) -> dict:
    """
    Parse JSON from an agent's raw string response.

    Handles the common case where a model wraps its JSON in a markdown
    code block (```json ... ```). Returns a dict with 'raw_response'
    as fallback so the debate never crashes on a parse failure.
    """
    if not raw_response:
        return {}

    cleaned = raw_response.strip()

    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Drop opening fence line and closing fence line
        cleaned = "\n".join(lines[1:-1])

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse agent JSON response: %s...", cleaned[:120]
        )
        return {"raw_response": raw_response}
