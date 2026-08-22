def project_events(subject, claims, edges):
    events=[]
    for c in sorted(claims):
        events.append({"activity":"observe","repo":subject.repo,"sha":subject.sha,
                       "evidence_id":c.evidence_id,"source":c.source.kind,
                       "outcome":c.outcome,"time":c.observed_at.isoformat()})
    for child,parent,relation in sorted((e.child_id,e.parent_id,e.relation) for e in edges):
        events.append({"activity":"provenance","repo":subject.repo,"sha":subject.sha,
                       "child":child,"parent":parent,"relation":relation})
    return tuple(events)
