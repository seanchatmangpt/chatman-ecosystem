from .subject import Refused

def current_witness_frontier(witnesses):
    by_pair={}
    for w in witnesses:
        key=(w.before.subject.repo,w.after.subject.repo,w.kind)
        prev=by_pair.get(key)
        if prev is None or (w.after.generation,w.observed_at,w.witness_id) > (prev.after.generation,prev.observed_at,prev.witness_id):
            by_pair[key]=w
        elif (w.after.generation,w.observed_at)==(prev.after.generation,prev.observed_at) and w != prev:
            raise Refused("REFUSED[DIVERGENT_WITNESS_FRONTIER]")
    return tuple(sorted(by_pair.values()))
