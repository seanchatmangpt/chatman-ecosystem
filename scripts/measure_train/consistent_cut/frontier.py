from .subject import Refused

def current_frontier(epochs):
    by_repo={}
    for e in epochs:
        previous=by_repo.get(e.subject.repo)
        if previous is None or e.generation > previous.generation:
            by_repo[e.subject.repo]=e
        elif e.generation == previous.generation and e != previous:
            raise Refused("REFUSED[DIVERGENT_CURRENT_EPOCH]")
    return tuple(sorted(by_repo.values()))
