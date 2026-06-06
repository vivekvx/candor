"""
Tool schemas for LiteLLM function-calling.

Each schema tells the LLM what tools exist, what they do, and what
arguments they accept. LiteLLM passes these to any provider that
supports tool-use (Groq, Anthropic, Gemini all support this format).

Schema format follows the OpenAI function-calling specification,
which is the common denominator across all providers LiteLLM supports.
"""

# The complete set of tools available to debate agents.
# Arbitrator does NOT receive these — it reads transcripts, not tools.
DEBATE_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "candor_get_company_intelligence",
            "description": (
                "Fetch REAL Indian company intelligence from MCA government "
                "filings via ZaubaCorp. Returns charge documents (debt signals), "
                "director info, compliance status, and salary benchmarks. "
                "ALWAYS call this first for any Indian company — government "
                "filings are legally filed facts that beat all other sources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name e.g. Zepto, Swiggy, BYJU's",
                    },
                    "city": {
                        "type": "string",
                        "description": "City if known, helps narrow search (optional)",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "candor_search_company_health",
            "description": (
                "Search for company health signals: funding rounds, growth "
                "trajectory, layoffs, employee sentiment. Use for financial "
                "and operational health signals not found in MCA filings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name e.g. Zepto, Swiggy",
                    },
                    "funding_stage": {
                        "type": "string",
                        "description": "e.g. Series B, pre-IPO (optional)",
                    },
                    "country": {
                        "type": "string",
                        "default": "India",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "candor_benchmark_compensation",
            "description": (
                "Benchmark a compensation package against market rates for "
                "similar roles in India. Use to evaluate whether an offer "
                "is above market, at market, or below market."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "e.g. Senior Backend Engineer",
                    },
                    "company_name": {"type": "string"},
                    "location": {
                        "type": "string",
                        "default": "Bangalore",
                    },
                    "years_experience": {
                        "type": "integer",
                        "description": "Years of total experience (0-30)",
                    },
                },
                "required": ["role", "company_name", "years_experience"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "candor_get_founder_signals",
            "description": (
                "Research founder background, previous companies, track record, "
                "and credibility signals. Use to evaluate leadership quality "
                "and founder-market fit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "founder_name": {
                        "type": "string",
                        "description": "Founder name if known (optional)",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "candor_get_market_timing",
            "description": (
                "Assess market timing for an opportunity. Is the sector growing, "
                "contracting, or overcrowded? Use to evaluate industry dynamics "
                "and competitive landscape."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "industry": {
                        "type": "string",
                        "description": "e.g. quick commerce, B2B SaaS, edtech",
                    },
                    "country": {
                        "type": "string",
                        "default": "India",
                    },
                },
                "required": ["company_name", "industry"],
            },
        },
    },
]
