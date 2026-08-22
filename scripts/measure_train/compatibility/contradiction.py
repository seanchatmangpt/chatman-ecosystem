def contradictions(vector):
    by={}
    out=[]
    for row in vector.rows:
        key=row.axis
        prev=by.get(key)
        if prev is not None and prev != row.outcome:
            out.append((key.value, prev.value, row.outcome.value))
        by[key]=row.outcome
    return tuple(out)
