"""Idempotent local setup: initializes the SQLite schema and validates every
synthetic scenario file against the dataset schema. Does not write any
scenario data into the database — scenarios are always read fresh from
data/scenarios/*.json, so there is nothing to "seed" beyond schema creation.
Safe to run multiple times.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapters.dataset_adapter import LocalDatasetAdapter  # noqa: E402
from app.repositories.db import init_db  # noqa: E402


def main() -> None:
    init_db()
    print("Database schema initialized (or already up to date).")

    adapter = LocalDatasetAdapter()
    datasets = adapter.load_all()
    if not datasets:
        print("WARNING: no scenario files found under data/scenarios/.")
        return

    print(f"Validated {len(datasets)} scenario file(s):")
    for dataset in datasets:
        print(f"  - {dataset.scenario_id}: {dataset.title}")


if __name__ == "__main__":
    main()
