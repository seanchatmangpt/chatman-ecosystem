def standing(census_rows):
    if not census_rows:return "UNKNOWN"
    states={v for _,v in census_rows}
    if "FAIL" in states:return "BUILD_BROKEN"
    if "CONTRADICTED" in states or "UNKNOWN" in states:return "UNKNOWN"
    if states=={"UNSUPPORTED"}:return "UNSUPPORTED"
    if "PASS" in states:return "PARTIAL_ALIVE"
    return "UNKNOWN"
