from dataclasses import dataclass
from fractions import Fraction
from .trajectory import Trajectory

@dataclass(frozen=True)
class Hazard:
    discharge: Fraction
    regression: Fraction


def hazards(traj: Trajectory) -> Hazard:
    dis=reg=total=0
    for a,b in zip(traj.epochs,traj.epochs[1:]):
        amap,bmap=a.by_key(),b.by_key()
        for k in amap:
            total += 1
            if bmap[k].state < amap[k].state: dis += 1
            elif bmap[k].state > amap[k].state: reg += 1
    den=max(total,1)
    return Hazard(Fraction(dis,den), Fraction(reg,den))
