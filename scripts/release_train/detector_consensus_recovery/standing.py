ORDER=("UNKNOWN","PARTIAL_ALIVE","ALIVE","BLOCKED","BUILD_BROKEN","UNSUPPORTED")

def calculate(consensus, regime, dependency_blockers=()):
    if dependency_blockers: return "BLOCKED"
    if consensus.verdict=="FAIL" or regime=="FAILED": return "BUILD_BROKEN"
    if consensus.verdict in {"STABLE_CONFIRMED","DRIFT_CONFIRMED"} and regime in {"STABLE","DRIFT"}: return "PARTIAL_ALIVE"
    return "UNKNOWN"
