def standing(census, correspondence):
    states=set(census["rail_states"].values())
    if "FAIL" in states: return "BUILD_BROKEN"
    if correspondence["divergent"] or correspondence["contradictory"]: return "UNKNOWN"
    if census["obligations"]: return "UNKNOWN"
    return "PARTIAL_ALIVE"
