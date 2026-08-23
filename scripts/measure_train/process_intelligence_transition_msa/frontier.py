from .subject import Refused

def current_subject_frontier(epochs):
    by_repo = {}
    for epoch in epochs:
        previous = by_repo.get(epoch.subject.repo)
        if previous is None or epoch.generation > previous.generation:
            by_repo[epoch.subject.repo] = epoch
        elif epoch.generation == previous.generation and epoch.subject.sha != previous.subject.sha:
            raise Refused("REFUSED[DIVERGENT_SUBJECT_FRONTIER]")
    return tuple(sorted(by_repo.values()))
