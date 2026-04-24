"""POST /query — orchestrates RAG + non-RAG + ML + LLM zero-shot.

Orchestration contract (from 02-CONTEXT.md §§2, 6, 7):
- rag and non_rag LLM calls run in parallel via asyncio.gather.
- ml and zero-shot priority predictions run synchronously (ml is ~1ms; zero-shot
  uses the sync instructor API — wrapping it in an executor adds overhead without
  parallelism benefit because rag + non_rag already saturate Groq concurrency).
- Each service call is isolated in try/except. Any failure sets that branch's
  fields to None and appends a human-readable message to errors[] — never a
  stack trace, never an exception class name.
- Every successful or partially-successful request is appended to queries.jsonl.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas.query import (
    AtScaleProjection,
    LLMPredictorResult,
    PredictorResult,
    QueryRequest,
    QueryResponse,
    RetrievedTicket,
)
from app.services import llm as llm_svc
from app.services import logger as log_svc
from app.services import ml_model as ml_svc
from app.services import rag as rag_svc

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])

TICKETS_PER_HOUR = 10_000  # COMP-03 at-scale projection scenario


async def _rag_branch(query: str) -> tuple[
    list[RetrievedTicket], str | None, float | None, float | None, str | None
]:
    """Returns (tickets, answer, latency_ms, cost_usd, err_msg)."""
    try:
        tickets = rag_svc.retrieve(query)
    except Exception:
        logger.exception("RAG retrieval failed")
        return [], None, None, None, "RAG retrieval unavailable"
    try:
        answer, lat, cost = await rag_svc.generate_rag_answer(query, tickets)
        return tickets, answer, lat, cost, None
    except Exception:
        logger.exception("RAG generation failed")
        return tickets, None, None, None, "RAG generation unavailable"


async def _non_rag_branch(query: str) -> tuple[str | None, float | None, float | None, str | None]:
    try:
        answer, lat, cost = await llm_svc.generate_non_rag_answer(query)
        return answer, lat, cost, None
    except Exception:
        logger.exception("Non-RAG LLM call failed")
        return None, None, None, "Non-RAG LLM unavailable"


def _ml_branch(query: str) -> tuple[PredictorResult | None, str | None]:
    try:
        return ml_svc.predict(query), None
    except Exception:
        logger.exception("ML prediction failed")
        return None, "ML prediction unavailable"


def _zero_shot_branch(query: str) -> tuple[LLMPredictorResult | None, str | None]:
    try:
        result, _, _ = llm_svc.predict_priority_zero_shot(query)
        return result, None
    except Exception:
        logger.exception("LLM zero-shot prediction failed")
        return None, "LLM zero-shot unavailable"


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Four-way query comparison",
    description="Runs a customer support query through four pipelines in parallel: RAG (Chroma + Groq), non-RAG (Groq only), ML classifier (sklearn), and LLM zero-shot (Groq + instructor). Returns all four answers with latency, cost, and an at-scale cost projection. File: `routers/query.py`",
)
async def run_query(req: QueryRequest) -> QueryResponse:
    try:
        # Parallel: RAG + non-RAG LLM calls (both wall-clock ~0.5-2s each)
        rag_task = _rag_branch(req.query)
        non_rag_task = _non_rag_branch(req.query)
        (tickets, rag_answer, rag_lat, rag_cost, rag_err), (
            non_rag_answer, non_rag_lat, non_rag_cost, non_rag_err,
        ) = await asyncio.gather(rag_task, non_rag_task)

        # Synchronous: ML (<1ms) + zero-shot (sync instructor client)
        ml_result, ml_err = _ml_branch(req.query)
        llm_result, llm_err = _zero_shot_branch(req.query)

        errors = [e for e in (rag_err, non_rag_err, ml_err, llm_err) if e]

        llm_cost_per_hour = (
            llm_result.cost_usd * TICKETS_PER_HOUR if llm_result else 0.0
        )

        response = QueryResponse(
            rag_answer=rag_answer,
            non_rag_answer=non_rag_answer,
            ml_prediction=ml_result,
            llm_prediction=llm_result,
            retrieved_tickets=tickets,
            at_scale_projection=AtScaleProjection(
                tickets_per_hour=TICKETS_PER_HOUR,
                ml_cost_per_hour=0.0,
                llm_cost_per_hour=llm_cost_per_hour,
            ),
            rag_latency_ms=rag_lat,
            rag_cost_usd=rag_cost,
            non_rag_latency_ms=non_rag_lat,
            non_rag_cost_usd=non_rag_cost,
            errors=errors,
        )

        # Log (crash-safe inside append_query; failures there don't break response)
        log_svc.append_query({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": req.query,
            "retrieved_tickets": [t.model_dump() for t in tickets],
            "rag_answer": rag_answer,
            "non_rag_answer": non_rag_answer,
            "ml_prediction": ml_result.model_dump() if ml_result else None,
            "llm_prediction": llm_result.model_dump() if llm_result else None,
            "rag_latency_ms": rag_lat,
            "rag_cost_usd": rag_cost,
            "non_rag_latency_ms": non_rag_lat,
            "non_rag_cost_usd": non_rag_cost,
            "errors": errors,
        })
        return response
    except HTTPException:
        raise
    except Exception:
        # Catch-all: log the trace server-side, generic message to client.
        logger.exception("Unhandled error in POST /query orchestration")
        raise HTTPException(status_code=500, detail="Internal server error")
