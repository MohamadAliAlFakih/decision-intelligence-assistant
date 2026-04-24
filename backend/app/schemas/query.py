"""Pydantic request/response contract for the POST /query endpoint.

Locked by .planning/phases/02-fastapi-backend/02-CONTEXT.md sections 2, 4, 6.
Every field name is load-bearing — the React frontend reads them by name.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """POST /query request body."""
    query: str = Field(min_length=1, max_length=2000)


class RetrievedTicket(BaseModel):
    """One Chroma hit rendered for the source-panel UI."""
    text: str
    similarity: float = Field(ge=0.0, le=1.0)


class PredictorResult(BaseModel):
    """Common shape for ML and LLM priority predictions.

    accuracy: test-set F1 on URGENT class (ML) or None (LLM zero-shot — no
    ground truth, frontend displays N/A).
    cost_usd: 0.0 for ML (no tokens), computed for LLM.
    """
    label: str                   # "URGENT" or "NORMAL"
    confidence: float = Field(ge=0.0, le=1.0)
    accuracy: Optional[float] = None
    latency_ms: float
    cost_usd: float


class LLMPredictorResult(PredictorResult):
    """Zero-shot predictor result, adds the LLM's reasoning string."""
    reasoning: str


class ZeroShotOutput(BaseModel):
    """Structured output schema passed to Groq via instructor.

    The LLM is required to return EXACTLY these three fields. Never parsed
    from free-form text — instructor enforces the schema or raises.
    """
    label: str
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class AtScaleProjection(BaseModel):
    """Projected hourly cost at COMP-03's 10,000 tickets/hour scenario."""
    tickets_per_hour: int = 10000
    ml_cost_per_hour: float = 0.0
    llm_cost_per_hour: float


class QueryResponse(BaseModel):
    """POST /query response body.

    All optional fields default to None to support the partial-failure
    contract (CONTEXT.md §6): if the LLM service fails, ml_prediction is
    still returned; errors[] lists human-readable descriptions.
    """
    model_config = ConfigDict(extra="forbid")

    rag_answer: Optional[str] = None
    non_rag_answer: Optional[str] = None
    ml_prediction: Optional[PredictorResult] = None
    llm_prediction: Optional[LLMPredictorResult] = None
    retrieved_tickets: list[RetrievedTicket] = Field(default_factory=list)
    at_scale_projection: AtScaleProjection
    rag_latency_ms: Optional[float] = None
    rag_cost_usd: Optional[float] = None
    non_rag_latency_ms: Optional[float] = None
    non_rag_cost_usd: Optional[float] = None
    errors: list[str] = Field(default_factory=list)
