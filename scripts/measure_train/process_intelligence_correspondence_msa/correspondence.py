from .subject import Refused
def admit_correspondence(subject, rails):
    rows=tuple(rails)
    if not rows: raise Refused("REFUSED[EMPTY_RAIL_SET]")
    ids=set(); sem=set()
    for r in rows:
        if r.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT_RAIL]")
        if r.rail_id in ids: raise Refused("REFUSED[DUPLICATE_RAIL]")
        ids.add(r.rail_id); sem.add(r.semantic_digest)
    if len(sem)!=1: raise Refused("REFUSED[SEMANTIC_IDENTITY_DRIFT]")
    return tuple(sorted(rows))
