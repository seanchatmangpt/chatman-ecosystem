def standing(rows,calibration,capital):
 states={r.state for r in rows}
 if "FAIL" in states:return "BUILD_BROKEN"
 if "REFUSED" in states:return "REFUSED"
 if "UNKNOWN" in states:return "UNKNOWN"
 if calibration.state!="CALIBRATED" or capital<4:return "UNKNOWN"
 if states=={"UNSUPPORTED"}:return "UNSUPPORTED"
 return "PARTIAL_ALIVE"
