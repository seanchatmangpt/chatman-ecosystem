from .subject import Refused
def current_frontier(epochs):
    by_source={}
    for e in epochs:
        p=by_source.get(e.source)
        if p is None or e.generation>p.generation: by_source[e.source]=e
        elif e.generation==p.generation and e!=p: raise Refused("REFUSED[DIVERGENT_CURRENT_REGIME]")
    return tuple(sorted(by_source.values()))
