from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from app.core.metrics import render_metrics
from app.repositories.db import get_engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> JSONResponse:
    try:
        engine = get_engine()
        with engine.connect():
            pass
    except Exception:
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "database": "unreachable"}
        )
    return JSONResponse(status_code=200, content={"status": "ready", "database": "reachable"})


@router.get("/metrics")
def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
