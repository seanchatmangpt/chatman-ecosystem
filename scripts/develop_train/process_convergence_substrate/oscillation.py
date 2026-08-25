from .trajectory import Trajectory


def oscillating_keys(traj: Trajectory) -> frozenset[str]:
    keys=traj.epochs[0].by_key().keys()
    out=set()
    for k in keys:
        seq=[e.by_key()[k].state for e in traj.epochs]
        for a,b,c in zip(seq,seq[1:],seq[2:]):
            if a == c and a != b:
                out.add(k); break
    return frozenset(out)
