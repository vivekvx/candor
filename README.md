# Candor

> The honest take on every career decision.

A multi-agent career intelligence system. Three AI agents debate your
career decision — Advocate, Challenger, Arbitrator — and deliver a
structured verdict with a negotiation package.

## Architecture

- **Advocate** — builds the strongest case for the opportunity
- **Challenger** — attacks every claim with fresh context
- **Arbitrator** — delivers an honest, practical verdict

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| Agents | LiteLLM (Groq / Claude / Gemini) |
| Tools | MCP Python SDK (FastMCP) |
| Search | Tavily |
| Observability | Langfuse |
| Frontend | React + Vite |
| Deployment | Railway + Vercel |

## Live Demo

🌐 **[Try Candor](https://your-vercel-url.vercel.app)**

Ask any career question. Three AI agents debate it.
One honest verdict.

## Example Questions
- "Should I join Zepto as a backend engineer for 42 LPA?"
- "Is this ESOP offer from a Series A startup worth taking?"
- "Leave TCS after 2 years for a product startup?"

## Phases

See `docs/phases.md` for the build plan.

## Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
