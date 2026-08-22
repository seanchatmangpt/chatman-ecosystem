def standing(census_rows, torn=()):
    if torn:
        return "UNKNOWN"
    if not census_rows:
        return "UNKNOWN"
    states={row[2] for row in census_rows}
    if "FAIL" in states:
        return "BUILD_BROKEN"
    if "CONTRADICTED" in states or "UNKNOWN" in states:
        return "UNKNOWN"
    if states == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if "PASS" in states:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
