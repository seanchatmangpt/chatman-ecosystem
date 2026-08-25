def census(transitions,conflicts,temporal_violations,durability,calibration):
    outcomes={t.outcome for t in transitions}
    if temporal_violations or any(kind=="LOST_UPDATE" for _,kind in conflicts) or durability=="FAIL": standing="BUILD_BROKEN"
    elif "IO_FAILURE" in outcomes or calibration.state!="CALIBRATED": standing="UNKNOWN"
    else: standing="PARTIAL_ALIVE"
    return {"standing":standing,"attempts":len(transitions),"conflicts":len(conflicts),"temporal_violations":len(temporal_violations),"durability":durability,"calibration":calibration.state}
