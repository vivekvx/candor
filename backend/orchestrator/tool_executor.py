"""
Executes tool calls made by debate agents.

Calls tool Python functions directly rather than through the MCP network
protocol. Direct calls are ~10x faster (no HTTP round-trip) and reuse
the same tool functions the MCP server exposes.

Design principle: this module never raises — every error is returned as
structured data so the agent can reason about the failure instead of
crashing the debate.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def execute_tool_call(tool_name: str, tool_arguments: dict) -> dict:
    """
    Execute a named tool with the given arguments.

    Dispatches to the correct tool function and returns its result.
    On any error, returns a structured error dict so the calling agent
    can acknowledge the failure and continue reasoning.

    Args:
        tool_name: The tool's registered name e.g. candor_search_company_health
        tool_arguments: Parsed argument dict matching the tool's input schema

    Returns:
        Tool result dict, or error dict with keys 'error' and 'tool_name'
    """
    try:
        result = await _route_to_tool(tool_name, tool_arguments)
        logger.info("Tool '%s' executed successfully", tool_name)
        return result

    except Exception as error:
        logger.error(
            "Tool '%s' failed with arguments %s: %s",
            tool_name,
            tool_arguments,
            error,
        )
        return {
            "error": f"Tool {tool_name} failed: {str(error)}",
            "tool_name": tool_name,
        }


async def _route_to_tool(tool_name: str, arguments: dict) -> dict:
    """
    Route a tool name to its Python function and execute it.

    Each branch constructs the tool's Pydantic input model so argument
    validation happens consistently with the MCP server path.

    Raises ValueError for unknown tool names so the error surfaces clearly.
    """
    if tool_name == "candor_get_company_intelligence":
        from mcp_server.tools.company_intelligence import (
            CompanyIntelligenceInput,
            get_company_intelligence,
        )
        tool_input = CompanyIntelligenceInput(**arguments)
        return await get_company_intelligence(tool_input)

    if tool_name == "candor_search_company_health":
        from mcp_server.tools.company_health import (
            CompanyHealthInput,
            search_company_health,
        )
        tool_input = CompanyHealthInput(**arguments)
        return await search_company_health(tool_input)

    if tool_name == "candor_benchmark_compensation":
        from mcp_server.tools.compensation import (
            CompensationInput,
            benchmark_compensation,
        )
        tool_input = CompensationInput(**arguments)
        return await benchmark_compensation(tool_input)

    if tool_name == "candor_get_founder_signals":
        from mcp_server.tools.founder_signals import (
            FounderSignalsInput,
            get_founder_signals,
        )
        tool_input = FounderSignalsInput(**arguments)
        return await get_founder_signals(tool_input)

    if tool_name == "candor_get_market_timing":
        from mcp_server.tools.market_timing import (
            MarketTimingInput,
            get_market_timing,
        )
        tool_input = MarketTimingInput(**arguments)
        return await get_market_timing(tool_input)

    raise ValueError(f"Unknown tool name: '{tool_name}'")


def parse_tool_arguments(raw_arguments: str) -> dict[str, Any]:
    """
    Parse a JSON string of tool arguments into a Python dict.

    LiteLLM returns tool arguments as a JSON string in
    message.tool_calls[n].function.arguments. Returns an empty dict
    if parsing fails so the tool call can still be attempted.
    """
    try:
        return json.loads(raw_arguments)
    except json.JSONDecodeError as error:
        logger.warning("Failed to parse tool arguments '%s': %s", raw_arguments, error)
        return {}
