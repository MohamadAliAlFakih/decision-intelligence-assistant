"""RAG service: Chroma retrieval + Groq generation with retrieved context.

The Chroma collection was populated in Phase 1 (01-03-SUMMARY.md):
- collection name: "support_tickets"
- embedding function: sentence-transformers all-MiniLM-L6-v2
- distance space: cosine (so similarity = 1 - distance)
"""
from __future__ import annotations

import asyncio
import logging
import time
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

from app.core.config import ROOT_DIR, get_settings
from app.prompts.rag import SYSTEM_PROMPT_RAG, build_rag_user_prompt
from app.schemas.query import RetrievedTicket
from app.services.llm import compute_cost

logger = logging.getLogger(__name__)

COLLECTION_NAME = "customer_tickets"


@lru_cache
def get_chroma_client():
    settings = get_settings()
    p = Path(settings.CHROMA_PATH)
    if not p.is_absolute():
        p = (ROOT_DIR.parent / p).resolve()
    logger.info("Connecting to Chroma persistent store at %s", p)
    return chromadb.PersistentClient(path=str(p))


@lru_cache
def get_embedding_function():
    settings = get_settings()
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.EMBEDDING_MODEL,
    )


@lru_cache
def get_chroma_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


@lru_cache
def get_groq_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


def retrieve(query: str, k: int | None = None) -> list[RetrievedTicket]:
    """Top-k semantic retrieval over the Chroma collection."""
    settings = get_settings()
    top_k = k if k is not None else settings.TOP_K_RESULTS
    coll = get_chroma_collection()
    result = coll.query(query_texts=[query], n_results=top_k)
    docs = (result.get("documents") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    tickets: list[RetrievedTicket] = []
    for text, dist in zip(docs, distances):
        sim = max(0.0, min(1.0, 1.0 - float(dist)))
        tickets.append(RetrievedTicket(text=text, similarity=sim))
    return tickets


async def generate_rag_answer(
    query: str, tickets: list[RetrievedTicket]
) -> tuple[str, float, float]:
    """Call Groq with retrieved context. Returns (answer, latency_ms, cost_usd)."""
    settings = get_settings()
    client = get_groq_client()
    user_prompt = build_rag_user_prompt(query, tickets)

    t0 = time.perf_counter()
    # groq sdk is synchronous — run_in_executor keeps event loop responsive for
    # parallel asyncio.gather with non_rag generation
    loop = asyncio.get_running_loop()

    def _call():
        return client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_RAG},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

    resp = await loop.run_in_executor(None, _call)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    answer = resp.choices[0].message.content or ""
    usage = resp.usage
    cost = compute_cost(usage.prompt_tokens, usage.completion_tokens)
    return answer, latency_ms, cost
