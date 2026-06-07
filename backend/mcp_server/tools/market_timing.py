import asyncio
from typing import Any, Literal

from pydantic import BaseModel

from mcp_server.tools import tavily_search
from mcp_server.tools.sanitizer import sanitize_web_content

MarketDirection = Literal["growing", "contracting", "stable", "unclear"]


class MarketTimingInput(BaseModel):
    company_name: str
    industry: str
    country: str = "India"


async def get_market_timing(inp: MarketTimingInput) -> dict[str, Any]:
    queries = [
        f'"{inp.industry}" market {inp.country} 2025 2026 growth trends',
        f'"{inp.company_name}" competitors market position',
    ]
    results = await asyncio.gather(*[tavily_search(q) for q in queries])

    timing_signals, competition_landscape, opportunity_signals, risk_signals, sources = [], [], [], [], []
    any_sanitized = False
    growth_score = 0

    for batch in results:
        for r in batch:
            raw = r.get("content", "") + " " + r.get("title", "")
            san = sanitize_web_content(raw)
            cleaned = san.cleaned_text
            if san.was_sanitized:
                any_sanitized = True
            url = r.get("url", "")
            if url:
                sources.append(url)
            text = cleaned.lower()
            if any(w in text for w in ("growing", "boom", "surge", "expand", "rise")):
                growth_score += 1
                opportunity_signals.append(cleaned[:200].strip())
            if any(w in text for w in ("decline", "shrink", "contract", "oversatur", "bust")):
                growth_score -= 1
                risk_signals.append(cleaned[:200].strip())
            if any(w in text for w in ("competitor", "rival", "market share", "vs")):
                competition_landscape.append(cleaned[:200].strip())
            timing_signals.append(cleaned[:200].strip())

    if growth_score > 1:
        direction: MarketDirection = "growing"
    elif growth_score < -1:
        direction = "contracting"
    elif growth_score == 0:
        direction = "unclear"
    else:
        direction = "stable"

    return {
        "industry": inp.industry,
        "market_direction": direction,
        "timing_signals": timing_signals[:5],
        "competition_landscape": competition_landscape[:5],
        "opportunity_signals": opportunity_signals[:5],
        "risk_signals": risk_signals[:5],
        "sources": list(dict.fromkeys(sources))[:10],
        "sanitized": any_sanitized,
    }
