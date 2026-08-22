def bounded_standing(selected_count: int, blockers: tuple[str, ...]) -> str:
    if blockers:
        return "BLOCKED"
    if selected_count == 0:
        return "UNKNOWN"
    return "REQUALIFYING"
