def standing(c):
    if c["rail_failures"]: return "BUILD_BROKEN"
    if c["rail_unknown"] or not c["methodology_complete"]: return "UNKNOWN"
    if c["oracle_state"]!="AGREE" or c["region_state"]!="CURRENT": return "UNKNOWN"
    if c["authority_state"] not in {"CORRESPONDENT","UNOBSERVED"}: return "BLOCKED"
    return "PARTIAL_ALIVE"
