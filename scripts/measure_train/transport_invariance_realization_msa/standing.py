def standing(cases,calibration_state,confusion,dependency_states=(),drifted=False):
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps:return "BUILD_BROKEN"
    if "BLOCKED" in deps:return "BLOCKED"
    if not cases or calibration_state in {"INSUFFICIENT","UNRELIABLE"} or drifted:return "UNKNOWN"
    if confusion.false_stable>0:return "UNKNOWN"
    return "PARTIAL_ALIVE"
