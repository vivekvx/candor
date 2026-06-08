# Candor: Multi-Agent Career Intelligence System

> **The honest take on every career decision.**

Candor is a production-grade multi-agent reasoning system that orchestrates three specialized AI agents to evaluate career decisions with structured rigor. The system combines adversarial reasoning (Advocate/Challenger debate), evidence-based judgment (raw tool outputs), and mechanical confidence scoring to deliver transparent, actionable verdicts.

**Status**: Fully operational. Deployed on Railway (backend) + Vercel (frontend). Free tier: 3 debates/hour/user.

---

## System Overview

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query (Career Decision)              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼──────┐           ┌─────▼────────┐
   │  Advocate  │           │  Challenger  │
   │ (Build Case)│           │ (Attack Case) │
   └────┬──────┘           └─────┬────────┘
        │                         │
        │    Round 1: Research    │
        │   (Tool Calls + LLM)    │
        │                         │
        │    Round 2: Rebuttal    │
        │   (Cross-examination)   │
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼──────────────┐
        │    Arbitrator             │
        │  (Evidence-based verdict) │
        │  + Data confidence score  │
        │  + Unresolved disputes    │
        │  + Reasoning trail        │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │  Structured Verdict JSON  │
        │  (bull/bear scores + tips)│
        └────────────────────────────┘
```

### Three-Agent Pattern

1. **Advocate** (Optimistic)
   - Maximizes the opportunity case
   - Calls tools: company health, founder signals, market timing
   - Round 1: Research → Round 2: Rebuttal
   - Fast tier model (cost optimization)

2. **Challenger** (Skeptical)
   - Finds contradictions and hidden risks
   - Sees Advocate's research, then calls tools
   - Round 1: Research → Round 2: Rebuttal
   - Mixed tier (Fast Round 1, Quality Round 2)

3. **Arbitrator** (Evidence-Based Judge)
   - Reads raw tool outputs (not summaries)
   - Detects factual contradictions automatically
   - Scores based on data confidence, not LLM opinion
   - Applies industry-specific evaluation rules
   - Quality tier model (one-step verdict)

### Key Innovations

| Feature | Why It Matters |
|---------|---------------|
| **Raw Evidence Context** | Arbitrator sees actual tool outputs, not agent summaries → reduces hallucination |
| **Mechanical Confidence** | `score = tools_returned_data / tools_called_total` → transparent about data quality |
| **Contradiction Detection** | Regex-based pattern matching for factual disputes (funding, profitability, headcount) |
| **Industry Overlays** | Fintech/Edtech/E-commerce/SaaS → context-specific research signals appended at runtime |
| **Reasoning Trail** | Single paragraph: what Advocate found, what Challenger disputed, what Arbitrator weighted |
| **Persistent Outcomes** | Append-only outcome recording (90-day follow-up) → builds longitudinal decision accuracy dataset |

---

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Backend** | FastAPI 0.104+ | Type-safe, async-first, automatic OpenAPI docs |
| **LLM Routing** | LiteLLM 1.44+ | Multi-provider abstraction (Groq/Claude/Gemini/OpenRouter) |
| **Agent Framework** | Custom (agentic loop) | Tool-calling loop with error recovery, state threading |
| **Tools** | MCP Python SDK (FastMCP) | Structured tool definitions, Tavily search, ZaubaCorp scraping |
| **Data Layer** | Supabase (free tier) | PostgreSQL + Auth (free tier: 500MB, 2GB bandwidth/month) |
| **Observability** | Langfuse (free tier) | Trace every LLM call, cost tracking, latency analysis |
| **Frontend** | React 18 + Vite 5 | SSE event streaming for real-time debate visualization |
| **Deployment** | Railway + Vercel | Railway: $5/month (starter), Vercel: free (Hobby) |

---

## API Reference

### Debate Endpoint

```http
POST /api/debate
Content-Type: application/json

{
  "query": "Should I join Zepto as a backend engineer for 38 LPA?",
  "model": "groq/llama-3.3-70b-versatile",  // optional, defaults to configured model
  "user_profile": {                          // optional
    "role": "Backend Engineer",
    "experience": "5 years",
    "current_ctc_lpa": 32.5,
    "risk_appetite": "High"
  }
}
```

**Response**: Server-Sent Events (streaming)

```
data: {"type":"status","stage":"round_1_start"}
data: {"type":"advocate_research","content":{...}}
data: {"type":"challenger_research","content":{...}}
data: {"type":"status","stage":"cross_examination_start"}
data: {"type":"advocate_rebuttal","content":{...}}
data: {"type":"challenger_rebuttal","content":{...}}
data: {"type":"status","stage":"arbitration_start"}
data: {"type":"verdict","content":{"bull_score":7,"bear_score":4,"verdict":"...","reasoning_trail":"...","unresolved_disputes":[...],"data_confidence":{...}}}
data: {"type":"complete","metadata":{"total_tokens":2156,"cost_usd":0.00127,"duration_seconds":45.2,"data_confidence":{...},"outcome_url":"/api/debate/{id}/outcome"}}
```

### Retrieve Debate

```http
GET /api/debate/{debate_id}
GET /api/debate/{debate_id}?format=card  # HTML verdict card for sharing
```

### Record Outcome (90-day follow-up)

```http
POST /api/debate/{debate_id}/outcome?outcome=joined
Content-Type: application/json
```

Valid outcomes: `joined`, `declined`, `still_deciding`, `offer_rescinded`

### Provider Status

```http
GET /api/provider-status
```

Returns health of all configured LLM providers (rate-limit status, cooldown remaining).

---

## Environment Configuration

### Required (Free Tier)

```bash
# Core LLM (Groq free tier — 14K free requests/month)
GROQ_API_KEY=gsk_...

# Search (Tavily — 1000 free requests/month)
TAVILY_API_KEY=tvly-...

# Optional: Observability (Langfuse — free tier: unlimited traces)
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Optional (Paid Providers — Activate When Groq Exhausted)

```bash
# Groq paid tier (separate key, separate pool)
GROQ_PAID_KEY=gsk_...

# Anthropic (fallback only, requires active billing)
ANTHROPIC_API_KEY=sk-ant-...

# Google (Gemini free: 1500 requests/day)
GEMINI_API_KEY=...

# OpenRouter (free tier: 100K tokens/month across all free models)
OPENROUTER_API_KEY=...
```

### Infrastructure

```bash
# Supabase (PostgreSQL + Auth, free tier)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173  # dev
FRONTEND_URL=https://candor-seven.vercel.app  # prod

# Deployment
ENVIRONMENT=production
```

---

## Installation & Development

### Prerequisites

- Python 3.11+
- Node 18+
- PostgreSQL 14+ (or Supabase free tier account)

### Backend Setup

```bash
cd backend

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with your API keys

# Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Tests (always green before deploy)
python -m pytest tests/ -v
```

### Frontend Setup

```bash
cd frontend

# Dependencies
npm install

# Development server
npm run dev  # http://localhost:5173

# Build for production
npm run build
npm run preview
```

### Database (One-Time Setup)

Create Supabase table (manual via Supabase console):

```sql
CREATE TABLE debates (
  id TEXT PRIMARY KEY,
  data JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX debates_created_at ON debates(created_at DESC);
```

---

## Verdict JSON Schema

Every debate produces a structured verdict:

```json
{
  "bull_score": 7,
  "bear_score": 4,
  "verdict": "JOIN but negotiate base + ESOP cliff. Growth + equity upside outweighs execution risk at 38 LPA.",
  "strongest_bull_point": "Series D at $X valuation, clear exit path, ex-Flipkart leadership.",
  "strongest_bear_point": "No profitability roadmap, burn rate unsustainable beyond 18 months.",
  "what_to_find_out": [
    "Exact vesting schedule and cliff period (4yr/1yr standard)",
    "Liquidation preference — are late investors in junior positions?",
    "Current burn rate vs. runway (cash left / monthly burn)"
  ],
  "if_i_were_you": "At 38 LPA with this equity upside, you're taking justified startup risk. Negotiate 3-month grace period for visa sponsorship.",
  "negotiation_tip": "Ask: 'Can we lock in a base of 40 LPA with accelerated ESOP vesting if we hit Series E?' Positions you for upside without salary risk.",
  "unresolved_disputes": [
    "funding status",
    "profitability"
  ],
  "reasoning_trail": "Advocate built a strong growth case on Series D funding and ex-Flipkart leadership. Challenger disputed profitability claims and burn rate sustainability. Arbitrator weighted the founder pedigree and clear market (quick commerce) more heavily than profitability concerns, given Series D stage. Raw tool outputs confirmed funding events but showed no revenue guidance, creating data gaps the Arbitrator made explicit.",
  "data_confidence": {
    "score": 0.82,
    "label": "HIGH",
    "tools_summary": "9/11 data sources returned results"
  }
}
```

**Confidence Levels**:
- `HIGH` (1.0): All tools returned data
- `MODERATE` (0.6-0.99): Most tools returned data  
- `LOW` (0.3-0.59): Some tools hit rate limits / empty results
- `VERY LOW` (0.01-0.29): Mostly failed tools
- `NO DATA` (0.0): No tools succeeded → verdict is general guidance only

---

## Performance & Costs

### Typical Run (Free Tier)

| Metric | Value |
|--------|-------|
| **Time** | 45-60s (2 research rounds + arbitration) |
| **Tokens** | ~2,200 (advocates 600 each, arbitrator 1000) |
| **Cost** | $0.0008-0.0012 (Groq free tier) |
| **Tools Called** | 10-12 (search, company health, salary data) |

### Free Tier Limits (Before Paid Fallback)

| Provider | Limit | Pool |
|----------|-------|------|
| Groq | 14,400 requests/month | Shared across all users |
| Tavily | 1,000 searches/month | Shared across all users |
| Gemini | 1,500 requests/day | Shared across all users |
| OpenRouter | 100K free tokens/month | Shared across all users |

**Rate Limiting**: 3 debates/hour/user (per IP address via X-Forwarded-For). No stored in-memory rate limit state on Railway (stateless design, resets on redeploy).

---

## Security & Data Privacy

### Input Sanitization

All user queries and agent outputs pass through a regex-based injection filter before entering agent context:
- Blocks prompt injection (`You are now DAN...`)
- Blocks extraction attacks (`Your instructions are...`)
- Blocks role hijacking (`Ignore previous...`)
- Logs all attempted attacks at WARNING level

See `backend/mcp_server/tools/sanitizer.py` for patterns.

### Data Retention

- **Debates**: Stored in Supabase indefinitely (user can delete via API later)
- **Outcomes**: Append-only (90-day follow-up), never deleted or modified
- **Search Results**: Not stored (fetched live, cached 5 minutes locally)
- **API Keys**: Never logged, stored only as environment variables
- **Personal Info**: User profile (role, salary) stored in SSE metadata only, not in debates table

### Tracing & Observability

All LLM calls traced via Langfuse (free tier):
- **Cost-optimized**: Only critical paths traced (arbitration always, research conditionally)
- **No PII**: User queries hashed before logging
- **Access**: Dashboard at https://cloud.langfuse.com (restricted to configured accounts)

---

## Extending Candor

### Adding a New Tool

1. Create function in `backend/mcp_server/tools/{tool_name}.py`
2. Register with FastMCP:
   ```python
   @mcp.tool()
   async def get_visa_sponsorship_status(company_name: str) -> dict:
       """Check if company has active visa sponsorship history."""
   ```
3. Add to `FASTMCP_TOOLS` in `backend/main.py`
4. Agents automatically discover via dynamic tool listing

### Adding a New LLM Provider

1. Add to `FALLBACK_MODEL_CHAIN` in `backend/orchestrator/router.py`
2. Configure env var in `backend/config.py` (pydantic BaseSettings)
3. No code changes needed — LiteLLM handles provider routing

### Custom Industry Overlays

Add a new file `backend/agents/prompts/overlays/{industry}.md`:

```markdown
## INDUSTRY CONTEXT: CRYPTO
Key signals to research specifically:
- Regulatory risk (US CFTC/SEC action)
- Burn rate relative to token treasury
- Founder background in regulated finance vs. pure crypto

Red flags specific to crypto: missing audit reports, founder controversy, no institutional backing
```

Industry detection is automatic (grep-based in `backend/orchestrator/debate.py`).

---

## Testing

### Run All Tests

```bash
cd backend
python -m pytest tests/ -v

# Expected: 21 passed, 3 warnings
```

### Test Coverage

- **Unit**: Config loading, sanitization patterns, confidence scoring
- **Integration**: Agent loop, tool execution, state threading
- **Live**: SSE event ordering, debate ID uniqueness, cache persistence

### Pre-Deployment Checklist

```bash
# 1. Tests pass
python -m pytest tests/ -v

# 2. Linting (optional, not enforced)
python -m flake8 backend/ --max-line-length=120

# 3. Type hints (optional, not enforced)
python -m mypy backend/ --ignore-missing-imports

# 4. Full debate flows (manual)
curl -X POST http://localhost:8000/api/debate \
  -H "Content-Type: application/json" \
  -d '{"query":"test question"}' \
  --no-buffer --max-time 120
```

---

## Known Limitations & Trade-offs

| Issue | Reason | Workaround |
|-------|--------|-----------|
| **Rate limiting state lost on redeploy** | In-memory store, no persistent backend | Deploy on Railway Starter ($7/mo) with persistent volume for production |
| **Debate cache ephemeral without volume** | Railway filesystem resets on redeploy | Supabase integration handles persistence; /tmp fallback during redeploy |
| **No user authentication** | Free tier, single-tenant prototype | Add Supabase Auth or OAuth2 for production multi-tenant |
| **No async tool parallelization** | Simplicity (agents run sequentially) | Rewrite agent_loop.py to spawn tool calls in parallel per round |
| **Arbitrator sees only final summaries from agents (Round 1)** | By design — forces advocates to be concise, challenges to be surgical | No change intended; by design for cost optimization |
| **No custom scoring weights** | Equal weighting of bull/bear scores | Extend verdict JSON with `user_weight_bull` field in future |

---

## Deployment

### Railway (Backend)

```bash
# 1. Create Railway project
# 2. Connect GitHub repo
# 3. Set environment variables in Railway dashboard
# 4. Auto-deploy on push to main
# 5. Monitor: railway logs -f
```

**Recommended**: Railway Starter plan ($7/month) for persistent volume.

### Vercel (Frontend)

```bash
# 1. Connect GitHub repo to Vercel
# 2. Configure environment:
#    VITE_API_URL=https://candor-production-xxx.up.railway.app
# 3. Auto-deploy on push to main
```

### Domain & CORS

Update `FRONTEND_URL` in backend config when adding custom domain.

---

## Contributing

### Code Style

- Python: Black (line length 120)
- TypeScript/React: Prettier (same as existing)
- Commits: Conventional (`feat()`, `fix()`, `docs()`)

### Before Opening a PR

1. Run tests: `python -m pytest tests/ -v` (must be 21 passed)
2. Update relevant docs in `docs/`
3. Test manually: run a full debate, verify all 9 SSE events arrive in order
4. Check for injection vulnerabilities (new string-matching in agents)

---

## Resources

- **Docs**: See `docs/` directory
- **API Docs**: Swagger UI at `http://localhost:8000/docs`
- **Cost Tracker**: Langfuse dashboard (free tier)
- **Observability**: Railway logs + Vercel analytics
- **Architecture Decision Records**: `docs/adr/` (in progress)

---

## License

MIT — use freely in personal and commercial projects.

---

## Contact & Support

- **Issues**: GitHub Issues (public repo)
- **Questions**: Discussions (GitHub)
- **Bugs**: File an issue with: debate_id, query, expected vs. actual verdict

---

## Version History

| Version | Date | Notable Changes |
|---------|------|-----------------|
| 1.0.0 | Jun 2026 | Shipped Prompts 1-4: Trust layer, Agent intelligence, Reliability, Frontend polish |
| 0.9.0 | Jun 2026 | Supabase integration, Free-first routing, X-Forwarded-For rate limiting |
| 0.8.0 | Jun 2026 | ZaubaCorp resilience, Outcomes tracking, Verdict share card |
| 0.7.0 | Jun 2026 | Arbitrator evidence context, Contradiction detector, Industry overlays |
| 0.1.0 | Jun 2026 | Initial: Advocate/Challenger/Arbitrator agents, basic routing |

---

**Built with ❤️ by Vivek.**
