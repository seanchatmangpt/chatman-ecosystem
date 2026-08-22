from .subject import Refused

def admit_cut(cut, current_epochs, observations):
    current={e.subject.repo:e for e in current_epochs}
    selected=cut.by_repo()
    for repo, epoch in selected.items():
        latest=current.get(repo)
        if latest is None:
            raise Refused("REFUSED[UNKNOWN_CUT_PRODUCER]")
        if epoch != latest:
            raise Refused("REFUSED[STALE_CUT_EPOCH]")
    for obs in observations:
        epoch=selected.get(obs.producer_epoch.subject.repo)
        if epoch is None:
            raise Refused("REFUSED[OBSERVATION_OUTSIDE_CUT]")
        if obs.producer_epoch != epoch:
            raise Refused("REFUSED[TORN_CUT_OBSERVATION]")
        if obs.observed_at < epoch.observed_at:
            raise Refused("REFUSED[OBSERVATION_PREDATES_EPOCH]")
    return tuple(sorted(observations))
