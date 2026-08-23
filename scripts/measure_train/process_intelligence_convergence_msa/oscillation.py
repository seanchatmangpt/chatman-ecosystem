def obligation_oscillations(epochs):
    states={}
    result={}
    for epoch in epochs:
        for o in epoch.obligations:
            seq=states.setdefault(o.obligation_id,[])
            if not seq or seq[-1] != o.state: seq.append(o.state)
    for oid, seq in states.items():
        toggles=max(0,len(seq)-1)
        result[oid]={"toggles":toggles,"sequence":tuple(seq),"oscillating":toggles>=2}
    return result
