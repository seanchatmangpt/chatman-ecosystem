def compute(feasible, calibration, blockers, complete_methods, complete_failures):
    if blockers: return 'BUILD_BROKEN'
    if not feasible: return 'BLOCKED'
    if calibration.false_safe_rate > 0 or calibration.mae > 0: return 'PARTIAL_ALIVE'
    if not complete_methods or not complete_failures: return 'PARTIAL_ALIVE'
    return 'PARTIAL_ALIVE'
