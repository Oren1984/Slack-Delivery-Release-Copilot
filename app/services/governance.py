from __future__ import annotations

from app.schemas.enums import Role

# Only Tech Lead and QA Lead hold release-approval authority: both own the
# technical/quality evidence the gate evaluates. Delivery Manager/PMO owns
# scope and convergence tracking but not the go/no-go call, and Observer is
# explicitly read-only per the product spec. This set is the single source
# of truth for approval authorization and is covered by unit tests.
AUTHORIZED_DECISION_ROLES: frozenset[Role] = frozenset({Role.TECH_LEAD, Role.QA_LEAD})


def is_authorized_to_decide(role: Role) -> bool:
    return role in AUTHORIZED_DECISION_ROLES


def actor_has_role(dataset_actors: list, actor_name: str, role: Role) -> bool:
    """Confirms the acting person is registered in the dataset's authorized
    actor list under the claimed role, preventing role self-assertion."""
    return any(a.name == actor_name and a.role == role for a in dataset_actors)
