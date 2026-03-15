# Prism

**Private edge inference agent**: simulated wearable data (HRV, sleep, activity) → preprocessed locally → anonymous signals to Nebius Token Factory LLM → personal performance forecast for the day. The agent runs autonomously on a timer and triggers actions without user input.

## Stack

- **Backend**: Python, FastAPI, [uv](https://docs.astral.sh/uv/)
- **Frontend**: React, Vite, Tailwind CSS
- **LLM**: [Nebius Token Factory](https://nebius.com/services/studio-inference-service) (OpenAI-compatible API)

## Setup

### Backend

```bash
# Install dependencies with uv
uv sync

# Copy env and set your Nebius API key
cp .env.example .env
# Edit .env: set NEBIUS_API_KEY (and optionally NEBIUS_MODEL)

# Run API (scheduler starts automatically)
uv run python main.py
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 (proxies `/api` and `/health` to the backend).

## Flow

1. **Simulated wearables** (or future real local ingestion): HRV, sleep, activity.
2. **Preprocessing**: Raw data → anonymous payload (no PII). Done locally.
3. **Nebius LLM**: Payload sent to Token Factory; returns a short forecast (summary, score, focus window, suggestions).
4. **Autonomous agent**: APScheduler runs the pipeline on a cron (default 6 AM). Latest result is stored and exposed at `GET /api/forecast/latest`.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness |
| `GET /api/forecast/latest` | Latest forecast from the scheduled agent |
| `POST /api/forecast/run?use_simulated=true` | Run agent once with simulated data |
| `POST /api/forecast/from-payload` | Run forecast from a preprocessed payload (JSON body) |
| `GET /api/simulate` | Get one simulated wearable set + payload (no LLM) |

## Env

See `.env.example`. Key variables:

- `NEBIUS_API_KEY` — Required for LLM calls.
- `AGENT_RUN_CRON` — Cron expression (default `0 6 * * *` = 6 AM daily).
- `AGENT_ENABLED` — Set to `false` to disable the scheduler.

## Live Demo

- **Frontend (Vercel):** https://frontend-brown-nu-53.vercel.app
- **Frontend (GitHub Pages):** https://electricgoatpod.github.io/prism/
- **Backend API:** https://prism-ecl6.onrender.com
- **API Docs:** https://prism-ecl6.onrender.com/docs
