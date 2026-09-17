from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes_audit import router as audit_router
from app.api.routes_convergence import router as convergence_router
from app.api.routes_health import router as health_router
from app.api.routes_release import router as release_router
from app.api.routes_scenarios import router as scenarios_router
from app.api.routes_sprints import router as sprints_router
from app.core.config import get_settings
from app.core.errors import CopilotError
from app.core.logging import configure_logging, get_logger, set_correlation_id
from app.repositories.db import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    logger.info("Slack Delivery & Release Copilot API starting up.")
    yield


app = FastAPI(
    title="Slack Delivery & Release Copilot",
    description=(
        "Read-only, advisory, offline-first release-governance copilot for the final "
        "50-100% of the SDLC. Deterministic decision engine with human-in-the-loop "
        "approval, simulated as a Slack workflow. No real Slack access, no real "
        "deployments, no automatic approvals."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    incoming = request.headers.get("X-Correlation-ID")
    cid = set_correlation_id(incoming or uuid.uuid4().hex[:16])
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


@app.exception_handler(CopilotError)
async def copilot_error_handler(_: Request, exc: CopilotError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Request validation failed."})


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled error: {type(exc).__name__}")
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})


app.include_router(health_router)
app.include_router(scenarios_router)
app.include_router(convergence_router)
app.include_router(release_router)
app.include_router(sprints_router)
app.include_router(audit_router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": "Slack Delivery & Release Copilot",
        "description": "Deterministic, human-in-the-loop release governance for the final "
        "50-100% of the SDLC, demonstrated through a simulated Slack workflow.",
        "docs": "/docs",
        "redoc": "/redoc",
        "demo_ui": "Run the Streamlit demo separately: streamlit run demo/streamlit_app.py "
        "(see README for local/Docker instructions).",
        "governance": "Read-only, advisory, offline-first, human-in-the-loop. No real "
        "deployments or Slack messages are ever sent.",
    }
