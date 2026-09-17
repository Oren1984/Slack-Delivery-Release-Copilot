"""Drops and recreates all SQLite tables, clearing every gate evaluation,
human decision, audit event, and close-out report. Scenario JSON files under
data/scenarios/ are untouched. Use this to return the local demo to a clean
state before a fresh walkthrough.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repositories.db import reset_db  # noqa: E402


def main() -> None:
    reset_db()
    print(
        "Database reset: all audit events, decisions, gate evaluations, and close-out "
        "reports were cleared. Scenario data files were not modified."
    )


if __name__ == "__main__":
    main()
