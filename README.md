# Decision Intelligence Assistant

A four-way comparison dashboard for customer support triage: every query returns a RAG answer (LLM + retrieved past tickets), a non-RAG answer (LLM alone), an ML priority prediction (trained classifier), and an LLM zero-shot priority prediction — side by side with accuracy, latency, and cost. The goal is a defensible deployment recommendation backed by real numbers, not guesses.

Built for AIE Bootcamp Week 3.

## Quick Start (under 5 minutes)

Prerequisites: **Docker Desktop** only (no Python, no Node required on the host).

1. Clone the repo and cd into the project:
   ```bash
   git clone <repo-url>
   cd 3-week3/decision-intelligence-assistant
   ```
2. Copy the env template and add your Groq key:
   ```bash
   cp .env.example .env
   # Open .env in your editor and set GROQ_API_KEY=<your key from https://console.groq.com/keys>
   # Also uncomment / set the Docker path overrides documented inside .env.example:
   #   CHROMA_PATH=/app/data/chroma_store
   #   LOG_PATH=/app/logs/queries.jsonl
   ```
3. Start the stack:
   ```bash
   docker compose up --build
   ```
4. Open **http://localhost:3000** in your browser. Type a query, click **Analyze Query**, read four outputs.

To stop: `Ctrl+C`, then `docker compose down`. Data in `./data/chroma_store` and `./logs` persists across restarts.

## Architecture Overview

```
Browser (localhost:3000)
    |
    v
Frontend container (nginx:alpine, serves React build from dist/)
    |  proxies /api/* -> http://backend:8000/* (strips /api prefix)
    v
Backend container (python:3.11-slim, uvicorn + FastAPI on :8000)
    +-- services/rag.py        -> Chroma persistent store  (bind mount)
    +-- services/ml_model.py   -> priority_model.pkl       (baked in image)
    +-- services/llm.py        -> Groq API                 (egress)
    +-- services/logger.py     -> logs/queries.jsonl       (bind mount)
```

Four outputs per POST /query: RAG answer, non-RAG answer, ML priority, LLM zero-shot priority — all with latency and cost. See `.planning/flow.MD` for a file-by-file walkthrough and `.planning/pitch.MD` for the 10-minute pitch arc.

## Environment Variables

All variables live in `.env` (loaded via pydantic-settings in `backend/app/core/config.py`). `.env` is gitignored; only `.env.example` is committed. Never commit `.env`.

| Variable | Purpose | Dev default | Docker override |
|----------|---------|-------------|-----------------|
| `GROQ_API_KEY` | Groq API key — required | (none) | (same) |
| `GROQ_MODEL` | Groq model name | `llama3-8b-8192` | (same) |
| `CHROMA_PATH` | Chroma persistent store directory | `./data/chroma_store` | `/app/data/chroma_store` |
| `MODEL_PATH` | Pickled sklearn pipeline | `./app/models/priority_model.pkl` | (same — baked in image) |
| `LOG_PATH` | JSONL query log path | `./logs/queries.jsonl` | `/app/logs/queries.jsonl` |
| `EMBEDDING_MODEL` | Sentence-transformer model | `all-MiniLM-L6-v2` | (same) |
| `TOP_K_RESULTS` | Retrieval top-k | `3` | (same) |

The Docker path overrides (`/app/data/chroma_store` and `/app/logs/queries.jsonl`) are required when running via `docker compose` because the container `WORKDIR` is `/app` and `config.py` resolves paths relative to `ROOT_DIR` (the `backend/` package root, which maps to `/app` inside the container). The bind mounts in `docker-compose.yml` land at those exact container paths.

## Project Structure

```
decision-intelligence-assistant/
+-- docker-compose.yml            -- two services: backend + frontend
+-- .env.example                  -- required env vars with dummy values
+-- README.md                     -- this file
+-- notebook.ipynb                -- EDA, labeling, ML training (Phase 1)
+-- data/
|   +-- chroma_store/             -- persistent vector DB (bind-mounted)
+-- logs/
|   +-- queries.jsonl             -- append-only query log (bind-mounted)
+-- backend/
|   +-- Dockerfile                -- python:3.11-slim + uv sync --no-dev
|   +-- pyproject.toml            -- uv-managed deps
|   +-- app/
|       +-- main.py               -- FastAPI app factory
|       +-- routers/              -- query.py, health.py, logs.py
|       +-- schemas/query.py      -- Pydantic request/response contract
|       +-- services/             -- rag.py, llm.py, ml_model.py, logger.py
|       +-- core/config.py        -- pydantic-settings + ROOT_DIR
|       +-- models/               -- priority_model.pkl (baked in image)
+-- frontend/
    +-- Dockerfile                -- multi-stage: node:20-alpine -> nginx:alpine
    +-- nginx.conf                -- serves dist/, proxies /api/* to backend
    +-- package.json              -- Vite 8 + React 19 + Tailwind v4
    +-- src/
        +-- App.jsx               -- root state + POST /api/query handler
        +-- components/           -- QueryInput, ResultCard, ComparisonTable
```

## How to Run (other modes)

**Dev (host Python, host Node) — no Docker:**
```bash
# Backend
cd backend && uv sync && uv run uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend && npm install && npm run dev   # port 3000
```

In host-only mode, keep the dev defaults for `CHROMA_PATH` and `LOG_PATH` (relative paths). Do not set the Docker container overrides.

**Docker stack (recommended):** see Quick Start above.

## Known Limitations

- **Weak supervision labels.** No ground-truth urgency labels exist for the TWCS dataset; the labeling function is a proxy (response time + keywords + caps/exclamations). Acknowledged honestly in `notebook.ipynb` and `.planning/pitch.MD`.
- **Single-user local tool.** No auth, no multi-tenancy, no HTTPS. Out of scope for v1.
- **Local Docker Compose only.** Cloud deployment is post-bootcamp.
- **LLM accuracy is reported as "N/A".** No ground-truth labels means the LLM zero-shot classifier cannot be accuracy-scored against this dataset.
- **Groq cost dependency.** Cost comparison numbers assume `llama3-8b-8192` pricing (`$0.05` / `$0.08` per million input/output tokens) as documented in `backend/app/core/config.py`. Rates can change.
