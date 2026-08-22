def project(subject,witnesses,estimates,seq):
    cal={e.source_id:e for e in estimates}
    events=[]
    for w in sorted(witnesses):
        e=cal.get(w.source_id)
        events.append({"activity":"calibrated_evidence","repo":subject.repo,"sha":subject.sha,
            "cluster_id":w.cluster_id,"source_id":w.source_id,"outcome":w.outcome,
            "evidence_id":w.evidence_id,"calibration_n":None if e is None else e.n,
            "time":w.observed_at.isoformat()})
    events.append({"activity":"sequential_likelihood","repo":subject.repo,"sha":subject.sha,
                   "log_lr":round(seq.log_lr,12),"decision":seq.decision})
    return tuple(events)
