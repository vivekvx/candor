"""
Agentic tool-calling loop for Candor debate agents.

An agent receives a prompt, autonomously decides which tools to call,
executes them, reads results, and repeats until it has enough information
to produce a final JSON answer. When the primary model rate-limits,
the loop automatically falls back to the next provider in the chain.
"""

import json
import logging
from typing import Any

import litellm

from orchestrator.tool_schemas import DEBATE_TOOL_SCHEMAS
from orchestrator.tool_executor import execute_tool_call, parse_tool_arguments

logger = logging.getLogger(__name__)

# Cap per agent per round — enough for thorough research, prevents runaway cost
MAX_TOOL_CALLS_PER_AGENT = 2

# Provider fallback chain — tried in order when the preferred model rate-limits.
# Groq is first (free, fast), then Gemini (free tier), then Anthropic (paid, best quality).
FALLBACK_MODEL_CHAIN = [
    "groq/llama-3.3-70b-versatile",
    "gemini/gemini-2.0-flash",
    "anthropic/claude-haiku-3-5",
]

# Substrings that identify a rate-limit or quota error in an exception message.
# These are recoverable — we retry with the next provider.
# Logic errors (bad key format, invalid request) are not in this list and are not retried.
RATE_LIMIT_ERROR_SIGNALS = [
    "rate limit",
    "ratelimit",
    "quota",
    "tokens per day",
    "tpd",
    "429",
    "resource exhausted",
    "too many requests",
    "credit",
    "billing",
]


def is_rate_limit_error(error: Exception) -> bool:
    """
    Return True if the error represents a recoverable rate-limit or quota exhaustion.

    Checks for known signal substrings in the lowercased error message.
    Returns False for logic errors (bad API key format, malformed request)
    because retrying a different provider won't fix those.
    """
    error_message = str(error).lower()
    return any(signal in error_message for signal in RATE_LIMIT_ERROR_SIGNALS)


def build_model_priority_list(preferred_model: str) -> list[str]:
    """
    Build the ordered list of models to attempt for one LLM call.

    The preferred model comes first. Every other model in FALLBACK_MODEL_CHAIN
    follows, with the preferred model excluded to avoid duplicates.
    """
    fallbacks_without_preferred = [
        model for model in FALLBACK_MODEL_CHAIN
        if model != preferred_model
    ]
    return [preferred_model] + fallbacks_without_preferred


async def attempt_llm_call(
    model: str,
    messages: list[dict],
    use_tools: bool,
) -> Any:
    """
    Make one LiteLLM completion call with or without tool schemas.

    Raises on any error — the caller owns the retry and fallback logic.

    Args:
        model: LiteLLM model string e.g. groq/llama-3.3-70b-versatile
        messages: Full conversation history to send
        use_tools: If True, attaches DEBATE_TOOL_SCHEMAS and sets tool_choice=auto
    """
    if use_tools:
        return await litellm.acompletion(
            model=model,
            messages=messages,
            tools=DEBATE_TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.7,
        )
    return await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=0.7,
    )


async def call_llm_with_fallback(
    messages: list[dict],
    use_tools: bool,
    preferred_model: str,
) -> tuple[Any, str]:
    """
    Call LiteLLM with automatic provider fallback on rate-limit errors.

    Tries the preferred model first. On a rate-limit or quota error, logs
    the failure and tries the next provider in the priority list. Fallback
    is silent to the end user — they only see an error if all providers fail.

    Args:
        messages: Conversation history to send
        use_tools: Whether to include tool schemas in the call
        preferred_model: Model to try first (from user or router selection)

    Returns:
        Tuple of (LiteLLM response object, model string that succeeded)

    Raises:
        RuntimeError if every provider in the priority list is exhausted
    """
    models_to_try = build_model_priority_list(preferred_model)
    last_error = None

    for model in models_to_try:
        try:
            response = await attempt_llm_call(
                model=model,
                messages=messages,
                use_tools=use_tools,
            )
            return response, model

        except Exception as error:
            if is_rate_limit_error(error):
                logger.warning(
                    "Model '%s' rate limited — trying next provider", model
                )
                last_error = error
                continue
            # Non-rate-limit errors are not retried — raise immediately
            raise

    raise RuntimeError(f"All providers exhausted. Last error: {last_error}")


async def run_agent_with_tools(
    system_prompt: str,
    user_message: str,
    model: str,
    agent_name: str,
) -> str:
    """
    Run one debate agent through the full tool-calling loop with provider fallback.

    The agent calls tools autonomously until it decides it has enough research
    to write its final answer, or until MAX_TOOL_CALLS_PER_AGENT is reached.
    Each LLM call uses call_llm_with_fallback so rate limits are handled silently.

    Args:
        system_prompt: Agent role and instructions (loaded from .md file)
        user_message: The debate query or context the agent is responding to
        model: Preferred LiteLLM model string
        agent_name: Human-readable label for logging e.g. "Advocate"

    Returns:
        Agent's final response as a string — should be valid JSON
    """
    messages = _build_initial_messages(system_prompt, user_message)
    total_tool_calls_made = 0

    logger.info("%s starting agent loop with preferred model %s", agent_name, model)

    while total_tool_calls_made < MAX_TOOL_CALLS_PER_AGENT:
        try:
            response, model_used = await call_llm_with_fallback(
                messages=messages,
                use_tools=True,
                preferred_model=model,
            )
        except RuntimeError as error:
            logger.error("%s all providers exhausted: %s", agent_name, error)
            return json.dumps({
                "error": "All AI providers rate limited",
                "message": str(error),
            })

        if model_used != model:
            logger.info(
                "%s fell back from %s to %s", agent_name, model, model_used
            )

        assistant_message = response.choices[0].message

        if not _has_tool_calls(assistant_message):
            logger.info(
                "%s finished after %d tool call(s) using %s",
                agent_name,
                total_tool_calls_made,
                model_used,
            )
            return assistant_message.content or ""

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

    Kept as a named function so tests can verify the message structure
    without running a full agent loop.
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def _has_tool_calls(assistant_message: Any) -> bool:
    """
    Return True if the assistant message contains one or more tool call requests.

    Defensive — some providers return None or omit the attribute entirely
    when the model decides not to call any tools.
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


async def _get_final_answer_without_tools(
    model: str, messages: list[dict]
) -> str:
    """
    Force a final answer after hitting the tool call limit.

    Uses the fallback chain here too — hitting the tool limit does not mean
    we give up on getting an answer from the best available provider.
    """
    try:
        response, model_used = await call_llm_with_fallback(
            messages=messages,
            use_tools=False,
            preferred_model=model,
        )
        return response.choices[0].message.content or ""
    except RuntimeError as error:
        logger.error("Final answer failed — all providers exhausted: %s", error)
        return json.dumps({"error": str(error)})


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
        # Drop the opening fence (```json) and closing fence (```)
        cleaned = "\n".join(lines[1:-1])

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse agent JSON response: %s...", cleaned[:120]
        )
        return {"raw_response": raw_response}
