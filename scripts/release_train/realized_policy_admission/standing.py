ORDER=("UNKNOWN","REQUALIFYING","PARTIAL_ALIVE","BLOCKED","BUILD_BROKEN")

def bounded_standing(*, admitted: bool, blockers=(), drifted=False, explicit_failure=False):
    if explicit_failure: return "BUILD_BROKEN"
    if blockers: return "BLOCKED"
    if drifted or not admitted: return "UNKNOWN"
    return "PARTIAL_ALIVE"
