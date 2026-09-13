"""Enforced jurisdiction registry for the Chatman Semantic Coordination Machine.

Maps components to the Sigma Z-coordinates they are allowed to touch:
Z = (P, Gamma, Omega, B, tau, J, Authority, Receipts).

A component acting outside its declared coordinates raises JurisdictionViolation.
SELECT is not CONSTRUCT is not DO; PlannerOutput is not Authority; DO requires a
Receipt; new Authority requires an explicit Grant, Delegation, or Rule. This
registry enforces the jurisdictional boundary component of that discipline.
"""

import functools

JURISDICTION_TABLE = {
    "ash_r2rml": ["B"],
    "beam4pm": ["Omega", "J"],
    "ash_a2a": ["P", "Gamma"],
    "ggen": [],
    "ggen-marketplace": ["Gamma", "A", "R"],
    "bcinr": ["B", "Omega", "A"],
    "mfw": ["A", "R"],
    "gymact": ["A", "R"],
    "gitvan": ["tau", "R", "B"],
    "ggen-ecosystem": ["R", "B"],
    "ash_pplan": ["P", "Omega", "tau"],
    "autofde-lab": ["Omega", "J", "B", "R"],
    "chatman-ecosystem": ["A", "R"],
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


def guard(component):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(z_coordinate, *args, **kwargs):
            check_jurisdiction(component, z_coordinate)
            return fn(z_coordinate, *args, **kwargs)

        return wrapper

    return decorator
