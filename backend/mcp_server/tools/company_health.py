import asyncio
from typing import Any, Optional

from pydantic import BaseModel

from backend.mcp_server.tools import tavily_search
from backend.mcp_server.tools.sanitizer import sanitize_web_content


class CompanyHealthInput(BaseModel):
    company_name: str
    funding_stage: Optional[str] = None
    country: str = "India"


async def search_company_health(inp: CompanyHealthInput) -> dict[str, Any]:
    queries = [
        f'"{inp.company_name}" funding layoffs growth 2025 2026',
        f'"{inp.company_name}" glassdoor employees review culture',
        f'"{inp.company_name}" {inp.funding_stage or ""} runway burn rate',
    ]
    results = await asyncio.gather(*[tavily_search(q) for q in queries])

    funding_signals, employee_sentiment, red_flags, positive_signals, sources = [], [], [], [], []
    any_sanitized = False

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
            if any(w in text for w in ("layoff", "cut", "bankrupt", "shut", "fraud", "scandal")):
                red_flags.append(cleaned[:200].strip())
            elif any(w in text for w in ("funding", "raised", "series", "ipo", "revenue", "growth")):
                funding_signals.append(cleaned[:200].strip())
            elif any(w in text for w in ("glassdoor", "employee", "culture", "review", "work")):
                employee_sentiment.append(cleaned[:200].strip())
            elif any(w in text for w in ("unicorn", "profitable", "expand", "hiring")):
                positive_signals.append(cleaned[:200].strip())

    return {
        "company": inp.company_name,
        "funding_signals": funding_signals[:5],
        "employee_sentiment": employee_sentiment[:5],
        "red_flags": red_flags[:5],
        "positive_signals": positive_signals[:5],
        "sources": list(dict.fromkeys(sources))[:10],
        "sanitized": any_sanitized,
    }
