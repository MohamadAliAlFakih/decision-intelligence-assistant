"""GET /logs?limit=N — return the last N entries from logs/queries.jsonl."""
from fastapi import APIRouter, Query

from app.services.logger import read_recent

router = APIRouter(tags=["logs"])


@router.get(
    "/logs",
    summary="Query history",
    description="Returns the last N entries from `logs/queries.jsonl`. Each entry contains the query, all four outputs, latency, and cost. File: `routers/logs.py`",
)
def list_logs(limit: int = Query(default=100, ge=0, le=1000)) -> list[dict]:
    return read_recent(n=limit)
