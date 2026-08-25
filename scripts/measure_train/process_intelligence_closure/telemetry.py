def project(subject,evidence,census):
    events=[]
    for e in sorted(evidence):
        events.append({"activity":"observe_process_rail","repo":subject.repo,"sha":subject.sha,"rail":e.rail,"engine":e.engine,
                       "semantic_digest":e.semantic_digest,"outcome":e.outcome,"evidence_id":e.evidence_id,"time":e.observed_at.isoformat()})
    for obligation in census["obligations"]:
        events.append({"activity":"process_closure_obligation","repo":subject.repo,"sha":subject.sha,"obligation":obligation})
    return tuple(events)
