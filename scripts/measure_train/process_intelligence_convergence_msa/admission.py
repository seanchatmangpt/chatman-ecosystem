from .subject import Refused
from .trajectory import admit_trajectory
from .freshness import epoch_freshness

def admit(epochs, now, ttl_seconds):
    rows=admit_trajectory(epochs)
    if not rows: raise Refused("REFUSED[EMPTY_TRAJECTORY]")
    if epoch_freshness(rows[-1],now,ttl_seconds) != "FRESH": raise Refused("REFUSED[STALE_CURRENT_EPOCH]")
    ids0={o.obligation_id for o in rows[0].obligations}
    for row in rows[1:]:
        if {o.obligation_id for o in row.obligations} != ids0:
            raise Refused("REFUSED[OBLIGATION_UNIVERSE_DRIFT]")
    return rows
