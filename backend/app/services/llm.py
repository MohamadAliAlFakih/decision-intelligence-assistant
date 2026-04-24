"""LLM service: non-RAG answer + LLM zero-shot priority classification.

Both functions call Groq. The zero-shot path uses instructor (hard rule: no
regex parsing of LLM output). Pricing follows CONTEXT.md cost calculation.
"""
from __future__ import annotations

import asyncio
import logging
import time
from functools import lru_cache

import instructor
from groq import Groq

from app.core.config import get_settings
from app.schemas.query import LLMPredictorResult, ZeroShotOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_NON_RAG = (
    "You are a customer support assistant. Answer the user's query using your "
    "own knowledge only — no external context is provided. "
    "Keep the answer concise (2-4 sentences)."
)

SYSTEM_PROMPT_ZERO_SHOT = (
    "You classify customer support messages as URGENT or NORMAL. URGENT means the "
    "customer needs immediate action (account security, service outage, payment "
    "failure, stated emergency). NORMAL means routine inquiry. Return a label, a "
    "brief reasoning (one sentence), and a confidence value between 0 and 1."
)


def compute_cost(input_tokens: int, output_tokens: int) -> float:
    """Per CONTEXT.md cost-calculation block.

    cost = (in * GROQ_INPUT_USD_PER_MTOK + out * GROQ_OUTPUT_USD_PER_MTOK) / 1_000_000
    Rates live on Settings so tests can override. For llama3-8b-8192 defaults are
    0.05 (input) and 0.08 (output) per million tokens.
    """
    settings = get_settings()
    return (
        input_tokens * settings.GROQ_INPUT_USD_PER_MTOK
        + output_tokens * settings.GROQ_OUTPUT_USD_PER_MTOK
    ) / 1_000_000


@lru_cache
def _get_raw_groq() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


@lru_cache
def _get_instructor_groq():
    """Instructor-patched client for structured outputs."""
    return instructor.from_groq(_get_raw_groq(), mode=instructor.Mode.JSON)


async def generate_non_rag_answer(query: str) -> tuple[str, float, float]:
    """Bare LLM call — no retrieval, no context."""
    settings = get_settings()
    client = _get_raw_groq()
    t0 = time.perf_counter()
    loop = asyncio.get_running_loop()

    def _call():
        return client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_NON_RAG},
                {"role": "user", "content": query},
            ],
            temperature=0.2,
        )

    resp = await loop.run_in_executor(None, _call)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    answer = resp.choices[0].message.content or ""
    cost = compute_cost(resp.usage.prompt_tokens, resp.usage.completion_tokens)
    return answer, latency_ms, cost


def predict_priority_zero_shot(
    query: str,
) -> tuple[LLMPredictorResult, float, float]:
    """Structured zero-shot priority classification via instructor.

    Returns (LLMPredictorResult, latency_ms, cost_usd). accuracy=None because
    LLM zero-shot has no pre-computable ground-truth accuracy (frontend N/A).
    """
    settings = get_settings()
    client = _get_instructor_groq()
    t0 = time.perf_counter()
    # instructor returns (parsed, completion) when use_raw=True-ish; we use
    # create_with_completion to get both the parsed object and the raw response
    # for token counts.
    parsed, raw = client.chat.completions.create_with_completion(
        model=settings.GROQ_MODEL,
        response_model=ZeroShotOutput,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_ZERO_SHOT},
            {"role": "user", "content": query},
        ],
        temperature=0.0,
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0
    cost = compute_cost(raw.usage.prompt_tokens, raw.usage.completion_tokens)

    result = LLMPredictorResult(
        label=parsed.label,
        reasoning=parsed.reasoning,
        confidence=parsed.confidence,
        accuracy=None,  # N/A for zero-shot
        latency_ms=latency_ms,
        cost_usd=cost,
    )
    return result, latency_ms, cost
