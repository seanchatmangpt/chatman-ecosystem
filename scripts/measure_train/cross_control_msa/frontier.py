from .refusal import Refused
def current_frontier(rows):
 by={}
 for r in rows:
  old=by.get(r.control.family)
  if old is None or r.subject.generation>old.subject.generation: by[r.control.family]=r
  elif r.subject.generation==old.subject.generation and r.result_digest!=old.result_digest: raise Refused("REFUSED[DIVERGENT_CONTROL_FRONTIER]")
 return tuple(by[k] for k in sorted(by))
