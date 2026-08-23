def project_transition(before_epoch, after_epoch, after_census, discharges, regressions):
    events = [{
        "activity": "subject_transition",
        "repo": after_epoch.subject.repo,
        "before_sha": before_epoch.subject.sha,
        "after_sha": after_epoch.subject.sha,
        "generation": after_epoch.generation,
    }]
    for d in discharges:
        events.append({
            "activity": "obligation_discharged",
            "repo": after_epoch.subject.repo,
            "sha": after_epoch.subject.sha,
            "obligation_id": d.obligation_id,
            "sources": list(d.proof_source_ids),
        })
    for r in regressions:
        events.append({
            "activity": "obligation_regressed",
            "repo": after_epoch.subject.repo,
            "sha": after_epoch.subject.sha,
            "obligation_id": r.obligation_id,
            "severity": r.severity,
        })
    return tuple(events)
