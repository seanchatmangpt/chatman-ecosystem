def current_witnesses(witnesses,attempt_id,now):
    current=[]; historical=[]; ids=set()
    for witness in sorted(witnesses,key=lambda item:(item.utc,item.evidence_id)):
        if witness.evidence_id in ids: raise ValueError("REFUSED[DUPLICATE_EVIDENCE_ID]")
        ids.add(witness.evidence_id)
        if witness.attempt_id!=attempt_id:
            historical.append(witness); continue
        if witness.utc>now: raise ValueError("REFUSED[FUTURE_EVIDENCE]")
        current.append(witness)
    return tuple(current),tuple(historical)
