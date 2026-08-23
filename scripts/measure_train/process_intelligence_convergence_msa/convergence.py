from dataclasses import dataclass
from fractions import Fraction
from .potential import closure_potential
from .oscillation import obligation_oscillations
from .hazard import transition_hazards

@dataclass(frozen=True)
class ConvergenceResult:
    direction: str
    initial_potential: Fraction
    final_potential: Fraction
    net_delta: Fraction
    oscillating_obligations: tuple[str, ...]
    discharge_hazard: Fraction
    regression_hazard: Fraction

def analyze(epochs):
    if not epochs:
        return ConvergenceResult("UNKNOWN",Fraction(0),Fraction(0),Fraction(0),(),Fraction(0),Fraction(0))
    initial=closure_potential(epochs[0]); final=closure_potential(epochs[-1]); delta=final-initial
    osc=obligation_oscillations(epochs)
    oscillating=tuple(sorted(k for k,v in osc.items() if v["oscillating"]))
    hazards=transition_hazards(epochs)
    if oscillating: direction="OSCILLATING"
    elif delta < 0 and hazards["discharge_hazard"] >= hazards["regression_hazard"]: direction="CONVERGING"
    elif delta > 0: direction="REGRESSING"
    elif delta == 0: direction="STALLED"
    else: direction="UNKNOWN"
    return ConvergenceResult(direction,initial,final,delta,oscillating,hazards["discharge_hazard"],hazards["regression_hazard"])
