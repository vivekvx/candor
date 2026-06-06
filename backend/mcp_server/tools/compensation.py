import asyncio
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.mcp_server.tools import tavily_search
from backend.mcp_server.tools.sanitizer import sanitize_web_content


class CompensationInput(BaseModel):
    role: str
    company_name: str
    location: str = "Bangalore"
    years_experience: int = Field(ge=0, le=30)
    current_ctc_lpa: Optional[float] = None


async def benchmark_compensation(inp: CompensationInput) -> dict[str, Any]:
    queries = [
        f'"{inp.role}" salary {inp.location} India 2025 2026 LPA',
        f'"{inp.company_name}" "{inp.role}" compensation package offer',
    ]
    results = await asyncio.gather(*[tavily_search(q) for q in queries])

    company_notes, negotiation_signals, sources = [], [], []
    any_sanitized = False
    lpa_values: list[float] = []

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
            # crude LPA extraction: look for "X lpa" or "X lakhs"
            import re
            for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?)', text):
                lpa_values.append(float(m.group(1)))
            if any(w in text for w in ("negotiate", "counter", "flexible", "band")):
                negotiation_signals.append(cleaned[:200].strip())
            if inp.company_name.lower() in text:
                company_notes.append(cleaned[:200].strip())

    lpa_values_sorted = sorted(set(lpa_values))
    if lpa_values_sorted:
        low = lpa_values_sorted[0]
        high = lpa_values_sorted[-1]
        median = lpa_values_sorted[len(lpa_values_sorted) // 2]
    else:
        low = median = high = 0.0

    return {
        "role": inp.role,
        "location": inp.location,
        "market_range_lpa": {"low": low, "median": median, "high": high},
        "company_specific_notes": company_notes[:5],
        "negotiation_signals": negotiation_signals[:5],
        "sources": list(dict.fromkeys(sources))[:10],
        "disclaimer": "Ranges are estimates from public sources. Verify with offer letter.",
        "sanitized": any_sanitized,
    }
