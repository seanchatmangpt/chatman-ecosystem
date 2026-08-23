def census(observations,member):
    rows=tuple(sorted(observations,key=lambda r:r.observation_id))
    return tuple({"id":r.observation_id,"kind":r.model.kind,"radius":[r.model.radius.numerator,r.model.radius.denominator],"covered":bool(member(r)),"realized_loss":[r.realized_loss.numerator,r.realized_loss.denominator],"predicted_worst_loss":[r.predicted_worst_loss.numerator,r.predicted_worst_loss.denominator],"methodology":r.methodology,"engine":r.engine,"region":r.region,"evidence_root":r.evidence_root} for r in rows)
