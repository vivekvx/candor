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
