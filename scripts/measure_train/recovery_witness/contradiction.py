def contradictions(witnesses):
    grouped={}
    for w in witnesses:
        key=(w.before.digest,w.after.digest)
        grouped.setdefault(key,set()).add((w.kind,w.result))
    bad=[]
    for key, rows in grouped.items():
        outcomes={result for _,result in rows if result not in {"PENDING","UNKNOWN","UNSUPPORTED"}}
        if "PASS" in outcomes and "FAIL" in outcomes:
            bad.append((key,tuple(sorted(rows))))
    return tuple(sorted(bad))
