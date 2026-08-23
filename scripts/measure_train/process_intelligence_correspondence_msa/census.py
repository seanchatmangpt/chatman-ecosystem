def census(rails, methodology_result, oracle_state, region_state, authority_state):
    states=[r.state for r in rails]
    return {"rail_failures":sum(s=="FAIL" for s in states),"rail_unknown":sum(s=="UNKNOWN" for s in states),"methodology_complete":methodology_result["complete"],"oracle_state":oracle_state,"region_state":region_state,"authority_state":authority_state}
