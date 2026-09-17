from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_TMP_DB = Path(tempfile.gettempdir()) / "slack_copilot_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"
os.environ["SCENARIOS_DIR"] = str(ROOT / "data" / "scenarios")
os.environ["LLM_MODE"] = "mock"

from app.adapters.dataset_adapter import LocalDatasetAdapter  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.repositories.db import get_session_factory, reset_db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    """Every test gets a clean, isolated SQLite schema — no gate evaluation,
    decision, audit event, or close-out report leaks between tests, even
    though scenario release/sprint IDs are fixed across the test suite."""
    get_settings.cache_clear()
    reset_db()
    yield


@pytest.fixture
def dataset_adapter() -> LocalDatasetAdapter:
    return LocalDatasetAdapter()


@pytest.fixture
def db_session():
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client
