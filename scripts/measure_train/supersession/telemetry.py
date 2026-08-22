def project(subject, current, historical):
    events = []
    for state, items in (("CURRENT", current), ("SUPERSEDED", historical)):
        for item in sorted(items):
            events.append({
                "activity": "measure_supersession",
                "repo": subject.repo,
                "sha": subject.sha,
                "source_id": item.source_id,
                "kind": item.kind,
                "scope": item.scope,
                "outcome": item.outcome,
                "epoch_sequence": item.epoch.sequence,
                "evidence_state": state,
                "time": item.epoch.observed_at.isoformat(),
            })
    return tuple(events)
