from __future__ import annotations


def bounded_standing(
    *,
    outcomes: tuple[str, ...],
    decision: str,
    independent_clusters: int,
    required_clusters: int,
    under_calibrated: bool,
) -> str:
    if "FAIL" in outcomes or decision == "REJECT":
        return "BUILD_BROKEN"
    if under_calibrated:
        return "UNKNOWN"
    if independent_clusters < required_clusters:
        return "UNKNOWN"
    if decision == "ACCEPT_BOUNDED" and all(o == "PASS" for o in outcomes):
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
