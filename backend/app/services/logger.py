"""Append-only JSONL logger for every POST /query.

Schema: see 02-CONTEXT.md §10. Every line is a self-contained JSON object;
the file can be tailed, grepped, or replayed without a parser.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.core.config import ROOT_DIR, get_settings

logger = logging.getLogger(__name__)


def _resolve_log_path() -> Path:
    settings = get_settings()
    p = Path(settings.LOG_PATH)
    if not p.is_absolute():
        # LOG_PATH defaults to ./logs/queries.jsonl — resolve relative to the
        # project root (parent of backend/)
        p = (ROOT_DIR.parent / p).resolve()
    return p


def append_query(entry: dict) -> None:
    """Append a single log entry as one JSONL line."""
    path = _resolve_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # swallow IO errors so the request still returns — log but don't crash
        logger.exception("Failed to append query log to %s", path)


def read_recent(n: int = 100) -> list[dict]:
    """Return the last n parsed JSON objects from the log file.

    Returns [] if the file does not exist. Malformed lines are skipped with a
    warning — a corrupt line must not block the /logs endpoint.
    """
    path = _resolve_log_path()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()
    tail = lines[-n:] if n > 0 else []
    out: list[dict] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Skipping malformed log line: %r", line[:100])
    return out
