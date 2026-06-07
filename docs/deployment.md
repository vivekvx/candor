# Deployment Guide

## Backend (Railway)

1. Go to railway.app and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select the `vivekvx/candor` repo
4. Keep root directory at the repo root (the `Procfile` and `nixpacks.toml`
   live in `backend/` but reference `backend.main:app` and
   `backend/requirements.txt` so imports resolve correctly — do NOT set
   root directory to `backend/`)
5. Railway auto-detects Python and uses `backend/nixpacks.toml`

### Environment Variables to Add in Railway Dashboard
Copy from `backend/.env.production` template and fill in real values:
- GROQ_API_KEY
- GEMINI_API_KEY
- ANTHROPIC_API_KEY
- TAVILY_API_KEY
- LANGFUSE_PUBLIC_KEY
- LANGFUSE_SECRET_KEY
- LANGFUSE_HOST
- ENVIRONMENT=production
- FRONTEND_URL=https://your-vercel-url.vercel.app

### After Deploy
Copy your Railway URL (e.g. `candor-backend.railway.app`).
Update `frontend/vercel.json` and `frontend/.env.production` with this URL.

## Frontend (Vercel)

1. Go to vercel.com and sign in with GitHub
2. Click "New Project" → Import `vivekvx/candor`
3. Set root directory to `frontend/`
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add environment variable:
   `VITE_API_URL=https://your-railway-url.railway.app`

### After Deploy
Copy your Vercel URL and add it to Railway env vars as `FRONTEND_URL`.

## Verify Deployment

Backend health:
```bash
curl https://your-railway-url.railway.app/ping
```

Frontend:
Open `https://your-vercel-url.vercel.app` in browser

Full debate:
```bash
curl -X POST https://your-railway-url.railway.app/api/debate \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I join Zepto for 42 LPA?"}' \
  --no-buffer
```

## Keep-Warm

Run `backend/keep_warm.py` as a separate process (e.g. a small cron
job or scheduled GitHub Action) to ping `/ping` every 10 minutes and
prevent Railway free-tier cold starts:

```bash
BACKEND_URL=https://your-railway-url.railway.app python3 backend/keep_warm.py
```
