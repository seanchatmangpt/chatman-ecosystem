ORDER={'ALIVE':0,'PARTIAL_ALIVE':1,'UNKNOWN':2,'UNSUPPORTED':3,'BUILD_BROKEN':4}
def combine(states):
    states=tuple(states)
    if not states: return 'UNKNOWN'
    return max(states,key=lambda s:ORDER[s])
