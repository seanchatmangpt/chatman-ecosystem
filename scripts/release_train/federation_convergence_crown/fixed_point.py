from .refusal import refuse
def fixed_point(epochs,dwell=3):
    if dwell<2: refuse("INVALID_DWELL")
    epochs=list(epochs)
    if len(epochs)<dwell: return False
    tail=epochs[-dwell:]
    return len({e.state_digest for e in tail})==1 and all(e.blockers==0 and e.error_ppm==0 for e in tail)
