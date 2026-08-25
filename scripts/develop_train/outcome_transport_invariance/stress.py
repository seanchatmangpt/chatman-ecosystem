from dataclasses import dataclass
from .perturb import Delta, apply
from .support import analyze
from .geometry import tv
from .weights import make
from .errors import Refused

@dataclass(frozen=True)
class Stress:
    name: str
    overlap: float
    shift: float
    ess: float
    supported: bool

def erosion(source, target, cell, fraction):
    if not 0 <= fraction <= 1:
        raise Refused("INVALID_EROSION")
    mass = source.data()
    if cell not in mass:
        raise Refused("UNKNOWN_CELL")
    stressed = apply(source, [Delta(cell, -mass[cell] * fraction)])
    support = analyze(stressed, target)
    try:
        ess, supported = make(stressed, target).ess, True
    except Refused:
        ess, supported = 0, False
    return Stress("erosion", support.overlap, tv(stressed, target), ess, supported)

def shift(source, target, cell, delta):
    stressed = apply(target, [Delta(cell, delta)])
    support = analyze(source, stressed)
    try:
        ess, supported = make(source, stressed).ess, True
    except Refused:
        ess, supported = 0, False
    return Stress("target_shift", support.overlap, tv(source, stressed), ess, supported)
