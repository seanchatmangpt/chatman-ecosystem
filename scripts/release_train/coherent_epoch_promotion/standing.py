from __future__ import annotations
from .census import CensusRow

def aggregate_standing(rows: tuple[CensusRow, ...]) -> str:
    states = {r.state for r in rows}
    if 'BUILD_BROKEN' in states: return 'BUILD_BROKEN'
    if 'UNKNOWN' in states: return 'UNKNOWN'
    if states and states <= {'UNSUPPORTED'}: return 'UNSUPPORTED'
    if 'UNSUPPORTED' in states: return 'UNKNOWN'
    if states and states <= {'PARTIAL_ALIVE'}: return 'PARTIAL_ALIVE'
    return 'UNKNOWN'
