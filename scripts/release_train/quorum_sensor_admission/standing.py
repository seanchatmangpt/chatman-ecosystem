from __future__ import annotations

from .topology import Topology


def bounded_standing(topology: Topology, blockers: tuple[str, ...], sensor_admitted: bool) -> tuple[str, str]:
    if blockers:
        return "BLOCKED", "dependency_blocker"
    if not sensor_admitted:
        return "UNKNOWN", "sensor_not_admitted"
    if topology == Topology.HEALTHY:
        return "PARTIAL_ALIVE", "calibrated_current_quorum"
    if topology == Topology.SPLIT_BRAIN:
        return "BLOCKED", "split_brain"
    if topology == Topology.STALE_MAJORITY:
        return "UNKNOWN", "stale_majority"
    if topology == Topology.PARTIAL_VISIBILITY:
        return "UNKNOWN", "partial_visibility"
    return "UNKNOWN", "no_quorum"
