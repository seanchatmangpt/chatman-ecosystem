def standing(census):
    if not census:
        return "UNKNOWN"
    states={state for _,_,state in census}
    if "BLOCKED" in states:
        return "BLOCKED"
    if states & {"PENDING_DELIVERY","PENDING_ACK","PENDING_DISCHARGE"}:
        return "UNKNOWN"
    if states == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if states <= {"REQUALIFIED","UNSUPPORTED"} and "REQUALIFIED" in states:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
