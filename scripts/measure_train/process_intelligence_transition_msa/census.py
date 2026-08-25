def evidence_census(obligations, evidence):
    by_obligation = {o.obligation_id: [] for o in obligations}
    for row in evidence:
        by_obligation[row.obligation_id].append(row.state)

    census = []
    for obligation in sorted(obligations):
        states = set(by_obligation[obligation.obligation_id])
        if not states:
            state = "UNKNOWN"
        elif "FAIL" in states:
            state = "FAIL"
        elif "REFUSED" in states:
            state = "REFUSED"
        elif "PENDING" in states or "UNKNOWN" in states:
            state = "UNKNOWN"
        elif states == {"UNSUPPORTED"}:
            state = "UNSUPPORTED"
        elif states == {"PASS"}:
            state = "PASS"
        else:
            state = "CONTRADICTED"
        census.append((obligation.obligation_id, obligation.kind, obligation.required, state))
    return tuple(census)
