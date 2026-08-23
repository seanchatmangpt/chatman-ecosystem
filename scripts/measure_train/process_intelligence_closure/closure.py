from .evidence import RAILS

def closure_census(methodology,evidence,distributed_state):
    rail_states={}
    for rail in sorted(RAILS):
        rows=[e.outcome for e in evidence if e.rail==rail]
        if "FAIL" in rows: state="FAIL"
        elif "PENDING" in rows or "UNKNOWN" in rows or not rows: state="UNKNOWN"
        elif rows and all(x=="UNSUPPORTED" for x in rows): state="UNSUPPORTED"
        elif rows and all(x=="PASS" for x in rows): state="PASS"
        else: state="UNKNOWN"
        rail_states[rail]=state
    missing=methodology.missing
    obligations=[]
    obligations.extend(f"METHODOLOGY:{x}" for x in missing)
    obligations.extend(f"RAIL:{r}" for r,s in rail_states.items() if s!="PASS")
    if distributed_state!="CURRENT": obligations.append(f"DISTRIBUTED:{distributed_state}")
    return {"methodology_missing":missing,"rail_states":rail_states,"distributed":distributed_state,"obligations":tuple(sorted(obligations))}
