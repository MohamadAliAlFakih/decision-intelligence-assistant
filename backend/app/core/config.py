"""Centralized configuration via pydantic-settings.

Every env var the backend reads flows through this file. Never call os.getenv()
elsewhere — call get_settings() and read attributes.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ROOT_DIR points at the `backend/` package directory (parent of `app/`).
# Resolved from this file's location so it is correct whether the app is
# launched from the backend/ directory (dev) or from a Docker working dir.
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Loaded from .env at process start; cached via get_settings()."""

    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-8b-8192"

    # Paths (string form so they survive relative -> absolute conversion
    # at the service layer; see ml_model.py / rag.py / logger.py)
    CHROMA_PATH: str = "./data/chroma_store"
    MODEL_PATH: str = "./app/models/priority_model.pkl"
    LOG_PATH: str = "./logs/queries.jsonl"

    # Embeddings + retrieval
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    TOP_K_RESULTS: int = 3

    # Groq llama3-8b-8192 pricing (per CONTEXT.md cost calculation block).
    # Kept on Settings so tests can override, and so at-scale projection math
    # lives at a single source of truth.
    GROQ_INPUT_USD_PER_MTOK: float = 0.05
    GROQ_OUTPUT_USD_PER_MTOK: float = 0.08

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Process-wide Settings singleton. Cached so env parsing runs once."""
    return Settings()  # type: ignore[call-arg]  # env provides required fields