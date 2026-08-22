SEVERITY={"PASS":0,"PENDING":1,"UNKNOWN":2,"UNSUPPORTED":2,"FAIL":3}
def contradictions(rows):
    by={}
    for sensor,outcome in rows: by.setdefault(sensor,set()).add(outcome)
    return tuple((k,tuple(sorted(v))) for k,v in sorted(by.items()) if len(v)>1)
def worst(outcomes): return max(outcomes,key=lambda x:SEVERITY[x]) if outcomes else "UNKNOWN"
