def standing(*, blockers: tuple[str,...], calibrated: bool, independent: bool, frontier_nonempty: bool) -> str:
    if blockers: return "BLOCKED"
    if not calibrated or not independent or not frontier_nonempty: return "UNKNOWN"
    return "PARTIAL_ALIVE"
