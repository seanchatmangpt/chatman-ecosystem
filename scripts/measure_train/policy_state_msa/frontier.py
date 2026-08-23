from .subject import Refused

def current_frontier(states):
    if not states: return None
    top=max(state.revision for state in states)
    rows=[state for state in states if state.revision==top]
    if len(set(rows))!=1: raise Refused("REFUSED[DIVERGENT_STATE_FRONTIER]")
    return rows[0]
