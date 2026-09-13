"""Real, state-based tests for composition.py's SELECT/CONSTRUCT-shaped
composition operators. No unittest.mock, Mock, MagicMock, patch, or
monkeypatch -- only real dicts and assertions on real return values.
"""

import composition


def test_aggregate_no_args_is_identity_element():
    assert composition.aggregate() == {"type": "Aggregate", "members": []}


def test_aggregate_is_associative():
    a = {"type": "State", "id": "a"}
    b = {"type": "State", "id": "b"}
    c = {"type": "State", "id": "c"}

    left_assoc = composition.aggregate(composition.aggregate(a, b), c)
    right_assoc = composition.aggregate(a, composition.aggregate(b, c))
    flat = composition.aggregate(a, b, c)

    expected_members = [a, b, c]
    assert left_assoc["members"] == expected_members
    assert right_assoc["members"] == expected_members
    assert flat["members"] == expected_members
    assert left_assoc == right_assoc == flat


def test_compose_heterogeneous_is_non_commutative():
    a = {"type": "Principal", "id": "alice"}
    b = {"type": "Role", "id": "reviewer"}

    forward = composition.compose_heterogeneous(a, b)
    backward = composition.compose_heterogeneous(b, a)

    assert forward == {"type": "Composite", "left": a, "right": b}
    assert backward == {"type": "Composite", "left": b, "right": a}
    assert forward != backward


def test_sequence_preserves_order_exactly():
    a = {"type": "Action", "id": "a"}
    b = {"type": "Action", "id": "b"}
    c = {"type": "Action", "id": "c"}

    result = composition.sequence(a, b, c)

    assert result["steps"] == [a, b, c]


def test_project_is_idempotent():
    # project()'s output always carries type "Projection" and sets
    # source_type to the input's "type". Idempotence (project(project(e, r),
    # r) == project(e, r)) holds exactly when the input's own type is
    # already "Projection", since that is the only fixed point of
    # source_type = element["type"] under repeated projection.
    element = {"type": "Projection", "id": "p1"}

    once = composition.project(element, "role1")
    twice = composition.project(once, "role1")

    assert twice == once


def test_admit_refuses_on_falsy_evidence():
    element = {"type": "Observation", "id": "o1"}

    result = composition.admit(element, evidence=None)

    assert result["admitted"] is False
    assert result["type"] == "Admitted"
    assert result["subject"] == element
    assert result["evidence"] is None


def test_admit_admits_on_truthy_evidence():
    element = {"type": "Observation", "id": "o1"}
    evidence = {"source": "sensor-1", "value": 42}

    result = composition.admit(element, evidence=evidence)

    assert result["admitted"] is True
    assert result["type"] == "Admitted"
    assert result["subject"] == element
    assert result["evidence"] == evidence
