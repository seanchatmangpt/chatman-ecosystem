def standing(census_rows):
    if not census_rows: return "UNKNOWN"
    states={r[2] for r in census_rows}
    if "BLOCKED" in states: return "BLOCKED"
    if states=={"UNSUPPORTED"}: return "UNSUPPORTED"
    if states <= {"REQUALIFIED","UNSUPPORTED"} and "REQUALIFIED" in states: return "PARTIAL_ALIVE"
    return "UNKNOWN"
