# syntax=docker/dockerfile:1.7
# D-02: python:3.11-slim matches pyproject.toml `requires-python = ">=3.11,<3.13"`;
# avoids Alpine's gcc/musl failures for numpy / scikit-learn / chromadb wheels.
FROM python:3.11-slim

# System deps required for chromadb + sentence-transformers at runtime.
# Keep minimal — slim image already has most of what we need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# D-01: install uv into the image (pinned to astral release) and run uv sync.
# Using the official installer script keeps this reproducible.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

# D-03: WORKDIR /app so config.py ROOT_DIR (parent-parent-parent of app/core/config.py)
# resolves to /app — which is where bind-mounted /app/data/chroma_store and
# /app/logs live. This is load-bearing: if WORKDIR changes, volume paths drift.
WORKDIR /app

# D-03: copy lockfile + pyproject first to maximize Docker layer cache.
# Only re-runs `uv sync` when deps change, not on every code edit.
COPY pyproject.toml uv.lock ./

# --frozen uses the lockfile exactly; --no-dev skips pytest/httpx (dev-only).
# Build dep groups are installed implicitly by uv from pyproject.toml.
RUN uv sync --frozen --no-dev

# Copy the FastAPI application code after deps (rarely-changing layer above,
# frequently-changing layer below).
COPY app ./app

# D-04: expose 8000 and start uvicorn via uv run so it uses the synced .venv.
# --host 0.0.0.0 required for Docker port mapping; --port 8000 matches D-08.
# No --reload in image (production-style start; dev uses compose override or
# direct `uv run uvicorn` on host).
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
