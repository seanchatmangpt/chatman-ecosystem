def detect_torn_cut(cut, observations):
    selected=cut.by_repo()
    torn=[]
    for obs in observations:
        expected=selected.get(obs.producer_epoch.subject.repo)
        if expected is None or expected != obs.producer_epoch:
            torn.append(obs.evidence_id)
    return tuple(sorted(torn))
