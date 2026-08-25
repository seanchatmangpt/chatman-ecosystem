from .subject import Refused

def admit_trajectory(transitions):
    rows = tuple(transitions)
    if not rows:
        return ()
    seen = set()
    for i, t in enumerate(rows):
        if t.transition_id in seen:
            raise Refused("REFUSED[DUPLICATE_TRANSITION]")
        seen.add(t.transition_id)
        if i:
            prev = rows[i-1]
            if prev.after != t.before:
                raise Refused("REFUSED[TORN_SUBJECT_TRAJECTORY]")
    return rows
