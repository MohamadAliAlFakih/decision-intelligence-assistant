"""Prompts for the RAG pipeline."""
from __future__ import annotations

from app.schemas.query import RetrievedTicket

SYSTEM_PROMPT_RAG = (
    "You are a customer support assistant. You will receive a customer query and a set of "
    "relevant past support tickets inside <context> tags. "
    "First, decide whether the query is a genuine customer support request (account issues, "
    "billing, product problems, service outages, etc.). "
    "If it is NOT a customer support query (e.g. general knowledge, cooking advice, "
    "off-topic questions), apologize briefly and explain you can only assist with "
    "customer support issues — do not use the context to answer it. "
    "If it IS a support query, use the context to synthesize a helpful, empathetic reply "
    "in your own words. Do not copy or repeat the context verbatim. "
    "If the context does not contain enough information to answer, say so honestly. "
    "Keep the answer concise (2-4 sentences)."
)


def build_rag_user_prompt(query: str, tickets: list[RetrievedTicket]) -> str:
    context_lines = []
    for i, t in enumerate(tickets, start=1):
        context_lines.append(f"[{i}] (similarity={t.similarity:.2f})\n{t.text}")
    context_block = "\n\n".join(context_lines)
    return (
        f"<context>\n{context_block}\n</context>\n\n"
        f"Customer query: {query}\n\nAnswer:"
    )
