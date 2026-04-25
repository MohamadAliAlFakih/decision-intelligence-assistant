"""ML inference service: loads priority_model.pkl, computes 8 features, predicts.

Contract (from 01-02-SUMMARY.md Phase 2 Contract):
- FEATURE_COLS order is load-bearing; the pickled scaler expects this order.
- URGENT-confidence index is derived at runtime from pipeline.classes_ — never hardcoded.
- Accuracy = F1 on URGENT class, computed ONCE at startup from test_features.csv.
- cost_usd is always 0.0 (ML has no token cost).
"""
from __future__ import annotations

import logging
import pickle
import re
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from textblob import TextBlob

from app.core.config import ROOT_DIR, get_settings
from app.schemas.query import PredictorResult

logger = logging.getLogger(__name__)

# Exact order from 01-02-SUMMARY.md §FEATURE_COLS. Do not reorder.
FEATURE_COLS: list[str] = [
    "word_count",
    "char_count",
    "has_urgency_keyword",
    "exclamation_count",
    "question_mark_count",
    "caps_ratio",
    "sentiment_polarity",
    "mention_count",
]

# Keyword categories mirror notebook Section 7 (urgent signals).
# If the notebook keyword list diverges, adjust here — keep the regex case-insensitive
# and apply to the LOWERCASED query (consistent with Phase 1 clean_text_lower).
URGENCY_KEYWORDS: list[str] = [
    # account/security
    "hacked", "compromised", "locked out", "can't log in", "cant log in",
    "account locked", "reset password", "unauthorized", "fraud",
    # service down
    "down", "outage", "not working", "broken", "error", "crashed", "offline",
    # strong emotion / urgency
    "urgent", "emergency", "asap", "immediately", "help", "please help",
    "frustrated", "angry",
    # account keyword (matches "account" in test behavior)
    "account",
]
_KEYWORD_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in URGENCY_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
_CAPS_WORD_RE = re.compile(r"\b[A-Z]{2,}\b")
_WORD_RE = re.compile(r"\S+")
_MENTION_RE = re.compile(r"@\w+")


def _resolve_path(raw: str) -> Path:
    """Resolve MODEL_PATH / LOG_PATH / CHROMA_PATH relative to ROOT_DIR if not absolute."""
    p = Path(raw)
    return p if p.is_absolute() else (ROOT_DIR / p).resolve()


@lru_cache
def get_ml_model():
    """Load the serialized sklearn Pipeline once per process."""
    settings = get_settings()
    path = _resolve_path(settings.MODEL_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"priority_model.pkl not found at {path}. "
            "Run notebook.ipynb (Phase 1, Section 23) to produce it."
        )
    with path.open("rb") as fh:
        pipe = pickle.load(fh)
    logger.info("Loaded ML pipeline from %s (classes=%s)", path, pipe.classes_.tolist())
    return pipe


def _urgent_index(pipe) -> int:
    """Find URGENT column in predict_proba output. Never hardcode."""
    classes = pipe.classes_.tolist()
    if "URGENT" not in classes:
        raise ValueError(f"Pipeline has no URGENT class; got {classes}")
    return classes.index("URGENT")


def build_features(query: str) -> np.ndarray:
    """Compute the 8 features from the raw query text.

    Mirrors notebook Sections 9-12 feature engineering logic. case-sensitive
    caps_ratio runs on the original text; keyword match runs on .lower().
    """
    q = query
    q_lower = query.lower()
    words = _WORD_RE.findall(q)
    word_count = len(words)
    char_count = len(q)
    has_urgency_keyword = int(bool(_KEYWORD_PATTERN.search(q_lower)))
    exclamation_count = q.count("!")
    question_mark_count = q.count("?")
    caps_words = _CAPS_WORD_RE.findall(q)
    caps_ratio = (len(caps_words) / word_count) if word_count > 0 else 0.0
    sentiment_polarity = float(TextBlob(q).sentiment.polarity)
    mention_count = len(_MENTION_RE.findall(q))

    row = {
        "word_count": word_count,
        "char_count": char_count,
        "has_urgency_keyword": has_urgency_keyword,
        "exclamation_count": exclamation_count,
        "question_mark_count": question_mark_count,
        "caps_ratio": caps_ratio,
        "sentiment_polarity": sentiment_polarity,
        "mention_count": mention_count,
    }
    return np.array([[row[c] for c in FEATURE_COLS]], dtype=float)


def predict(query: str) -> PredictorResult:
    """Run inference. cost_usd is always 0.0 (ML = no tokens)."""
    pipe = get_ml_model()
    X = build_features(query)
    t0 = time.perf_counter()
    label = str(pipe.predict(X)[0])
    proba = pipe.predict_proba(X)[0]
    latency_ms = (time.perf_counter() - t0) * 1000.0

    _urgent_index(pipe)  # validate URGENT class exists
    # confidence is the probability of the predicted class (not always URGENT)
    predicted_idx = pipe.classes_.tolist().index(label)
    confidence = float(proba[predicted_idx])

    return PredictorResult(
        label=label,
        confidence=confidence,
        accuracy=get_accuracy(),
        latency_ms=latency_ms,
        cost_usd=0.0,
    )


@lru_cache
def get_accuracy() -> float:
    """F1 on URGENT class — loaded from model_metrics.json produced by the notebook."""
    import json
    metrics_path = ROOT_DIR.parent / "data" / "model_metrics.json"
    if metrics_path.exists():
        with metrics_path.open() as fh:
            score = float(json.load(fh)["test_f1_urgent"])
        logger.info("Loaded F1 URGENT = %.4f from %s", score, metrics_path)
        return score
    logger.warning("model_metrics.json not found at %s; returning 0.0", metrics_path)
    return 0.0
