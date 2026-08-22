from .subject import Refused
def current_cut_frontier(cuts, supersessions=()):
    by_id={c.cut_id:c for c in cuts}
    superseded=set()
    for e in supersessions:
        if e.newer_cut_id not in by_id or e.older_cut_id not in by_id: raise Refused("REFUSED[ORPHAN_CUT_SUPERSESSION]")
        newer,older=by_id[e.newer_cut_id],by_id[e.older_cut_id]
        if newer.generation!=e.newer_generation or older.generation!=e.older_generation: raise Refused("REFUSED[CUT_SUPERSESSION_GENERATION_MISMATCH]")
        superseded.add(e.older_cut_id)
    current=[c for c in cuts if c.cut_id not in superseded]
    if not current: return None
    maxgen=max(c.generation for c in current)
    top=[c for c in current if c.generation==maxgen]
    if len(top)!=1: raise Refused("REFUSED[DIVERGENT_CURRENT_CUT]")
    return top[0]
