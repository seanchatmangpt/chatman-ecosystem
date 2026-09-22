"""Enforced jurisdiction registry for the Chatman Semantic Coordination Machine.

Maps components to the Sigma Z-coordinates they are allowed to touch:
Z = (P, Gamma, Omega, B, tau, J, Authority, Receipts).

A component acting outside its declared coordinates raises JurisdictionViolation.
SELECT is not CONSTRUCT is not DO; PlannerOutput is not Authority; DO requires a
Receipt; new Authority requires an explicit Grant, Delegation, or Rule. This
registry enforces the jurisdictional boundary component of that discipline.

PR-3 slice: the AGENTS.md "Jurisdiction table" is now mechanically enforced
(prototype/tests/test_jurisdiction_contracts.py parses the markdown table and
refuses doc/code drift):
  - JURISDICTION_TABLE = the doc's "Owns" column. Coordinate vocabulary now
    includes Mu (Construct, ggen's row) and DeltaZ (bounded world execution
    / ΔZ, gymact's row); the previous code table silently dropped both.
  - MUST_NOT_OWN = the doc's "Must not own" column, verbatim capability tags.
    check_forbidden() refuses a component performing a forbidden capability
    (REFUSED_JURISDICTION_FORBIDDEN) and refuses components with no admitted
    contract at all (REFUSED_JURISDICTION_UNKNOWN_COMPONENT, fail-closed).
"""

import functools

JURISDICTION_TABLE = {
    "ash_r2rml": ["B"],
    "beam4pm": ["Omega", "J"],
    "ash_a2a": ["P", "Gamma"],
    "ggen": ["Mu"],
    "ggen-marketplace": ["Gamma", "A", "R"],
    "bcinr": ["B", "Omega", "A"],
    "mfw": ["A", "R"],
    "gymact": ["A", "DeltaZ", "R"],
    "gitvan": ["tau", "R", "B"],
    "ggen-ecosystem": ["R", "B"],
    "ash_pplan": ["P", "Omega", "tau"],
    "autofde-lab": ["Omega", "J", "B", "R"],
    "chatman-ecosystem": ["A", "R"],
    # 2026-09-21 doc-refresh cycle: the five loop participants that had no
    # admitted contract (they failed closed as REFUSED_JURISDICTION_UNKNOWN
    # _COMPONENT). Values derived from the observed role each repo plays in
    # the v26.9.22 cross-repo order, recorded in the receipt for that cycle.
    "xaas": ["B", "J", "tau", "R"],
    "ggen_igniter": ["Mu"],
    "zcode-cli": ["DeltaZ", "R"],
    "ash_surface": ["P", "R"],
    "dfcm-autonomous": ["A", "tau", "R"],
}

# The AGENTS.md jurisdiction table's "Must not own" column, verbatim
# (comma-split). A capability listed here is refused for that component even
# if the component's Owns coordinates would otherwise admit the request.
MUST_NOT_OWN = {
    "ash_r2rml": ["External writes", "DO"],
    "beam4pm": ["DO"],
    "ash_a2a": ["Canonical human ontology", "minting Authority"],
    "ggen": ["Runtime standing"],
    "ggen-marketplace": ["Canonical domain state", "execution"],
    "bcinr": ["DO"],
    "mfw": ["Freeform planning"],
    "gymact": ["Planning", "ontology ownership"],
    "gitvan": ["Planning", "world actuation"],
    "ggen-ecosystem": ["Manufacture semantics", "business authority"],
    "ash_pplan": ["Duplicate lifecycle/queue/planner/runtime"],
    "autofde-lab": ["Production authority"],
    "chatman-ecosystem": ["Product/runtime implementation"],
    "xaas": ["Canonical human ontology", "minting Authority"],
    "ggen_igniter": ["DO", "Runtime standing"],
    "zcode-cli": ["Planning", "ontology ownership"],
    "ash_surface": ["Business authority", "DO"],
    "dfcm-autonomous": ["Product implementation", "ontology ownership"],
}


class JurisdictionViolation(Exception):
    pass


def check_jurisdiction(component, z_coordinate):
    allowed = JURISDICTION_TABLE.get(component, [])
    if z_coordinate not in allowed:
        raise JurisdictionViolation(
            f"component {component!r} is not permitted to act on Z-coordinate "
            f"{z_coordinate!r}; allowed coordinates for {component!r}: {allowed!r}"
        )
    return True


def check_forbidden(component, capability):
    """Refuses a component performing a capability its contract forbids.

    Enforces the AGENTS.md "Must not own" column: REFUSED_JURISDICTION_FORBIDDEN
    for an admitted component touching a forbidden capability, and
    REFUSED_JURISDICTION_UNKNOWN_COMPONENT (fail-closed) for a component with
    no admitted contract at all.
    """
    if component not in MUST_NOT_OWN:
        raise JurisdictionViolation(
            f"REFUSED_JURISDICTION_UNKNOWN_COMPONENT: component {component!r} has "
            f"no admitted jurisdiction contract; every capability is refused"
        )
    if capability in MUST_NOT_OWN[component]:
        raise JurisdictionViolation(
            f"REFUSED_JURISDICTION_FORBIDDEN: component {component!r} must not own "
            f"capability {capability!r} (AGENTS.md jurisdiction table, Must-not-own column)"
        )
    return True


def guard(component):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(z_coordinate, *args, capability=None, **kwargs):
            check_jurisdiction(component, z_coordinate)
            if capability is not None:
                check_forbidden(component, capability)
            return fn(z_coordinate, *args, **kwargs)

        return wrapper

    return decorator
