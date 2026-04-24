"""FastAPI app factory. Routers only, zero business logic.

Hard rule (CLAUDE.md): no handlers defined here — all logic lives in routers/
and services/. This file exists only to wire them together and set up CORS +
startup warm-up.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.logs import router as logs_router
from app.routers.query import router as query_router
from app.services import ml_model as _ml_model_svc

# Base logging config: INFO with a readable format. Docker/compose can override.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Decision Intelligence Assistant",
    description="Four-way comparison API: RAG, non-RAG, ML, LLM zero-shot",
    version="0.1.0",
)

# CORS: permissive for local dev; frontend hits this from http://localhost:5173
# (Vite dev server) in development and from the frontend container in Docker.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(logs_router)
app.include_router(query_router)


@app.on_event("startup")
def _warm_up() -> None:
    """Load the ML model and compute startup accuracy once.

    Without this, the first POST /query would eat a cold-load latency spike
    (pickle.load + test_features.csv + predict over all rows). Doing it at
    boot keeps request latency consistent.
    """
    try:
        _ml_model_svc.get_ml_model()
        acc = _ml_model_svc.get_accuracy()
        logger.info("ML warm-up complete; startup F1 URGENT = %.4f", acc)
    except Exception:
        logger.exception("ML warm-up failed; /query will surface the error per request")
