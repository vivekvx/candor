import logging
import os
from datetime import datetime, timezone
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

    retrieved_at = datetime.now(timezone.utc).isoformat()
    results = []
    for r in response.get("results", []):
        url = r.get("url", "")
        results.append({
            "url": url,
            "title": r.get("title", ""),
            "content": r.get("content", ""),
            # Source-registry fields — let agents/Arbitrator trace every claim
            # back to where (and when) it came from.
            "source_url": url or "general_knowledge",
            "retrieved_at": retrieved_at,
        })
    return results
