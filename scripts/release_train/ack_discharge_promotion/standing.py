from __future__ import annotations
from .census import CensusRow

def standing(rows: tuple[CensusRow,...], strategy_complete: bool) -> str:
    if not rows:
        return "UNKNOWN"
    states={row.state for row in rows}
    if "BLOCKED" in states:
        return "BLOCKED"
    if any(state.startswith("PENDING_") for state in states):
        return "UNKNOWN"
    if not strategy_complete:
        return "UNKNOWN"
    if states == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
