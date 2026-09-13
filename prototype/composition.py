"""Pure composition operators over plain dicts tagged by a Sigma "type" key.

Vocabulary reused verbatim from the 20 Sigma classes at
/Users/sac/chatman-ecosystem/packs/scm-sigma-pack/ontology.ttl.
These functions are SELECT/CONSTRUCT-shaped only: they never DO, never
produce a Receipt, and never grant Authority.
"""


def aggregate(*elements):
    """Preserves associativity and flattens nested Aggregates; refuses nothing, no args yields the identity element."""
    members = []
    for element in elements:
        if isinstance(element, dict) and element.get("type") == "Aggregate":
            members.extend(element.get("members", []))
        else:
            members.append(element)
    return {"type": "Aggregate", "members": members}


def compose_heterogeneous(a, b):
    """Preserves order/non-commutativity (left/right are never sorted or merged); refuses nothing."""
    return {"type": "Composite", "left": a, "right": b}


def sequence(*elements):
    """Preserves step order exactly and associativity, flattening nested Sequences; refuses nothing."""
    steps = []
    for element in elements:
        if isinstance(element, dict) and element.get("type") == "Sequence":
            steps.extend(element.get("steps", []))
        else:
            steps.append(element)
    return {"type": "Sequence", "steps": steps}


def project(element, role):
    """Preserves idempotence under repeated projection with the same role; refuses nothing."""
    return {"type": "Projection", "role": role, "source_type": element["type"]}


def admit(element, evidence):
    """Preserves total-ness (never raises); refuses admission (admitted=False) whenever evidence is falsy."""
    return {"type": "Admitted", "subject": element, "evidence": evidence, "admitted": bool(evidence)}
