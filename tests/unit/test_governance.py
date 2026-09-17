from __future__ import annotations

from app.schemas.enums import Role
from app.services.governance import actor_has_role, is_authorized_to_decide
from tests.unit.factories import make_dataset


def test_tech_lead_is_authorized():
    assert is_authorized_to_decide(Role.TECH_LEAD) is True


def test_qa_lead_is_authorized():
    assert is_authorized_to_decide(Role.QA_LEAD) is True


def test_delivery_manager_is_not_authorized():
    assert is_authorized_to_decide(Role.DELIVERY_MANAGER) is False


def test_observer_is_not_authorized():
    assert is_authorized_to_decide(Role.OBSERVER) is False


def test_actor_has_role_matches_registered_actor():
    dataset = make_dataset()
    assert actor_has_role(dataset.authorized_actors, "Tessa Lead", Role.TECH_LEAD) is True


def test_actor_has_role_rejects_role_self_assertion():
    dataset = make_dataset()
    # "Olive Watcher" is registered as an Observer, not a Tech Lead.
    assert actor_has_role(dataset.authorized_actors, "Olive Watcher", Role.TECH_LEAD) is False


def test_actor_has_role_rejects_unknown_actor():
    dataset = make_dataset()
    assert actor_has_role(dataset.authorized_actors, "Nobody Registered", Role.TECH_LEAD) is False
