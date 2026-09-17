from __future__ import annotations

from app.repositories import audit_repo


def test_append_event_persists_and_is_retrievable(db_session):
    record = audit_repo.append_event(
        db_session,
        event_type="dataset_loaded",
        outcome="loaded",
        sprint_id="SPR-TEST",
        release_id="REL-TEST",
        evidence_reference="unit-test-scenario",
    )
    assert record.id
    assert record.correlation_id

    events = audit_repo.list_events(db_session, release_id="REL-TEST")
    assert len(events) == 1
    assert events[0].event_type == "dataset_loaded"


def test_list_events_filters_by_release_id(db_session):
    audit_repo.append_event(db_session, event_type="a", outcome="x", release_id="REL-A")
    audit_repo.append_event(db_session, event_type="b", outcome="x", release_id="REL-B")

    events_a = audit_repo.list_events(db_session, release_id="REL-A")
    assert len(events_a) == 1
    assert events_a[0].release_id == "REL-A"


def test_events_are_ordered_most_recent_first(db_session):
    first = audit_repo.append_event(
        db_session, event_type="first", outcome="x", release_id="REL-ORDER"
    )
    second = audit_repo.append_event(
        db_session, event_type="second", outcome="x", release_id="REL-ORDER"
    )

    events = audit_repo.list_events(db_session, release_id="REL-ORDER")
    assert events[0].id == second.id
    assert events[1].id == first.id


def test_audit_table_has_no_update_or_delete_helpers():
    # The audit repository intentionally exposes only append_event and
    # list_events — no update/delete function exists at the application
    # layer, keeping the trail append-only by construction.
    public_names = [n for n in dir(audit_repo) if not n.startswith("_")]
    assert not any("update" in n.lower() or "delete" in n.lower() for n in public_names)
