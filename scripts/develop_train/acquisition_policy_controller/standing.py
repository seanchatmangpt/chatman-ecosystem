def bounded_standing(*,selected,drifted,blockers=()):
    if blockers:return "BLOCKED"
    if drifted:return "UNKNOWN"
    return "PARTIAL_ALIVE" if selected else "UNKNOWN"
