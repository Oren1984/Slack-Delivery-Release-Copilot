from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.adapters.dataset_adapter import LocalDatasetAdapter
from app.repositories.db import get_db

_dataset_adapter = LocalDatasetAdapter()


def get_dataset_adapter() -> LocalDatasetAdapter:
    return _dataset_adapter


def get_session() -> Generator[Session, None, None]:
    yield from get_db()
