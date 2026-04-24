"""GET /health — trivial liveness check."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness check",
    description="Returns `{status: ok}` if the server is up. File: `routers/health.py`",
)
def health() -> dict[str, str]:
    return {"status": "ok"}
