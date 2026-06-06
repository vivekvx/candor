from fastmcp import FastMCP

from backend.mcp_server.tools.company_health import CompanyHealthInput, search_company_health
from backend.mcp_server.tools.compensation import CompensationInput, benchmark_compensation
from backend.mcp_server.tools.founder_signals import FounderSignalsInput, get_founder_signals
from backend.mcp_server.tools.market_timing import MarketTimingInput, get_market_timing
from backend.mcp_server.tools.company_intelligence import (
    CompanyIntelligenceInput,
    get_company_intelligence,
)

mcp = FastMCP("candor_mcp")


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def candor_search_company_health(
    company_name: str,
    funding_stage: str | None = None,
    country: str = "India",
) -> dict:
    """Search for real signals about a company's health — funding, layoffs, employee sentiment."""
    return await search_company_health(
        CompanyHealthInput(company_name=company_name, funding_stage=funding_stage, country=country)
    )


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def candor_benchmark_compensation(
    role: str,
    company_name: str,
    location: str = "Bangalore",
    years_experience: int = 0,
    current_ctc_lpa: float | None = None,
) -> dict:
    """Benchmark a compensation package against market rates for similar roles in India."""
    return await benchmark_compensation(
        CompensationInput(
            role=role,
            company_name=company_name,
            location=location,
            years_experience=years_experience,
            current_ctc_lpa=current_ctc_lpa,
        )
    )


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def candor_get_founder_signals(
    company_name: str,
    founder_name: str | None = None,
) -> dict:
    """Research founder background, track record, and credibility signals."""
    return await get_founder_signals(
        FounderSignalsInput(company_name=company_name, founder_name=founder_name)
    )


@mcp.tool(
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
)
async def candor_get_market_timing(
    company_name: str,
    industry: str,
    country: str = "India",
) -> dict:
    """Assess market timing — is the sector growing, contracting, or overcrowded?"""
    return await get_market_timing(
        MarketTimingInput(company_name=company_name, industry=industry, country=country)
    )


@mcp.tool(
    description=(
        "Fetch real Indian company intelligence from MCA government filings "
        "via ZaubaCorp. Returns charge documents (debt signals), director "
        "information, compliance status, and salary benchmarks from AmbitionBox. "
        "Use this for any Indian startup evaluation — it surfaces signals "
        "that web search cannot find. Government filings are legally filed facts."
    ),
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
    },
)
async def candor_get_company_intelligence(
    company_name: str,
    city: str = None,
) -> dict:
    """MCP tool wrapper for the company intelligence scraper."""
    input_data = CompanyIntelligenceInput(
        company_name=company_name,
        city=city,
    )
    return await get_company_intelligence(input_data)


if __name__ == "__main__":
    mcp.run()
