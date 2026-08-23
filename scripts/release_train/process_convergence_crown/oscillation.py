from .trajectory import Trajectory

def oscillating_keys(t: Trajectory) -> tuple[str,...]:
    keys=[]
    for key in t.current.universe:
        seq=[e.states[key] for e in t.epochs]
        if len(seq)>=3 and seq[-1]==seq[-3] and seq[-2]!=seq[-1]: keys.append(key)
    return tuple(sorted(keys))
