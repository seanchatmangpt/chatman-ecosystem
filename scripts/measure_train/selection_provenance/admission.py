from .subject import Refused
from .drift import classify_drift

def admit_selection(selection, frontier, candidates, now):
    if now.tzinfo is None or now.utcoffset() is None:
        raise Refused("REFUSED[NAIVE_NOW]")
    if selection.observed_at > now:
        raise Refused("REFUSED[FUTURE_SELECTION_EVIDENCE]")
    candidate_map = {c.cut_id: c for c in candidates}
    if set(selection.candidate_ids) != set(candidate_map):
        raise Refused("REFUSED[CANDIDATE_EVIDENCE_MISMATCH]")
    for candidate in candidates:
        if candidate.consumer != selection.consumer:
            raise Refused("REFUSED[FOREIGN_CANDIDATE_SUBJECT]")
    selected = candidate_map[selection.selected_cut_id]
    if not selected.complete:
        raise Refused("REFUSED[INCOMPLETE_SELECTED_CUT]")
    drift = classify_drift(selection, frontier)
    if drift != "CURRENT":
        raise Refused(f"REFUSED[{drift}]")
    return selected
