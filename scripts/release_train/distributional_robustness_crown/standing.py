def bounded_standing(*,calibrated,realized,methods,engines,oracles,regions,failures,blockers):
    if blockers: return "BUILD_BROKEN"
    if not all((calibrated,realized,methods,engines,oracles,regions,failures)): return "PARTIAL_ALIVE"
    return "PARTIAL_ALIVE"
