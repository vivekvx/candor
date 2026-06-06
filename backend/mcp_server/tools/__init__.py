import os
from typing import Any

from tavily import AsyncTavilyClient


async def tavily_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Shared Tavily search. Returns list of {url, title, content} dicts.
    Raises ValueError if TAVILY_API_KEY not set.
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in environment")
    client = AsyncTavilyClient(api_key=api_key)
    response = await client.search(query, max_results=max_results)
    results = []
    for r in response.get("results", []):
        results.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", ""),
        })
    return results
