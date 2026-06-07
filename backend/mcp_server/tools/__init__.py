import logging
import os
from typing import Any

from tavily import AsyncTavilyClient

logger = logging.getLogger(__name__)


async def tavily_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Shared Tavily search used by every research tool.

    Returns a list of {url, title, content} dicts on success. Never raises —
    a missing API key, an expired key, a hit monthly limit, or any client
    error all degrade to an empty list so the calling tool still returns its
    normal (empty-signal) shape and the agent can keep reasoning from its
    own base knowledge instead of seeing an opaque tool failure.
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set — search '%s' returning no results", query)
        return []

    try:
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(query, max_results=max_results)
    except Exception as error:
        logger.warning("Tavily search failed for '%s': %s — returning no results", query, error)
        return []

    results = []
    for r in response.get("results", []):
        results.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", ""),
        })
    return results
