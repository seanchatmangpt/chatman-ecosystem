from dataclasses import dataclass
from fractions import Fraction
from .population import Population
from .refusal import require

@dataclass(frozen=True)
class SupportWitness:
    target_cells: int
    supported_cells: int
    minimum_source_mass: Fraction
    overlap: Fraction


def admit_support(source: Population, target: Population, minimum_source_mass: Fraction = Fraction(1,1000)) -> SupportWitness:
    s=source.as_dict(); t=target.as_dict()
    target_positive={k:v for k,v in t.items() if v>0}
    missing=[k for k in target_positive if s.get(k, Fraction(0)) < minimum_source_mass]
    require(not missing, "POSITIVITY_VIOLATION", ",".join(sorted(missing)))
    overlap=sum((min(s.get(k,Fraction(0)), t.get(k,Fraction(0))) for k in set(s)|set(t)), Fraction(0))
    mins=min((s[k] for k in target_positive), default=Fraction(0))
    return SupportWitness(len(target_positive), len(target_positive)-len(missing), mins, overlap)
