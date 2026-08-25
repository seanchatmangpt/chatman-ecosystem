from .refusal import Refused
def current_frontier(subjects):
    by={}
    for s in subjects:
        old=by.get(s.repo)
        if old is None or s.generation>old.generation: by[s.repo]=s
        elif s.generation==old.generation and s.sha!=old.sha: raise Refused("REFUSED[DIVERGENT_SUBJECT_FRONTIER]")
    return tuple(sorted(by.values()))
