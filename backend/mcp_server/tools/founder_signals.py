import asyncio
from typing import Any, Optional

from pydantic import BaseModel

from backend.mcp_server.tools import tavily_search
from backend.mcp_server.tools.sanitizer import sanitize_web_content


class FounderSignalsInput(BaseModel):
    company_name: str
    founder_name: Optional[str] = None


async def get_founder_signals(inp: FounderSignalsInput) -> dict[str, Any]:
    queries = [f'"{inp.company_name}" founder CEO background track record']
    if inp.founder_name:
        queries.append(f'"{inp.founder_name}" "{inp.company_name}" previous startup exit')

    results = await asyncio.gather(*[tavily_search(q) for q in queries])

    founder_background, previous_ventures, credibility_signals, concern_signals, sources = [], [], [], [], []
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
            if any(w in text for w in ("fraud", "lawsuit", "scam", "fired", "controversy")):
                concern_signals.append(cleaned[:200].strip())
            elif any(w in text for w in ("exit", "acquired", "ipo", "previous", "founded")):
                previous_ventures.append(cleaned[:200].strip())
            elif any(w in text for w in ("iit", "iim", "harvard", "stanford", "google", "amazon", "mckinsey")):
                credibility_signals.append(cleaned[:200].strip())
            else:
                founder_background.append(cleaned[:200].strip())

    return {
        "company": inp.company_name,
        "founder_background": founder_background[:5],
        "previous_ventures": previous_ventures[:5],
        "credibility_signals": credibility_signals[:5],
        "concern_signals": concern_signals[:5],
        "sources": list(dict.fromkeys(sources))[:10],
        "sanitized": any_sanitized,
    }
