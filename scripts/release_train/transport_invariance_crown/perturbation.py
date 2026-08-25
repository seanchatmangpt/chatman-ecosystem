from dataclasses import dataclass
from fractions import Fraction
from .population import Population
from .refusal import require

@dataclass(frozen=True)
class Perturbation:
    cell: str
    source_delta: Fraction = Fraction(0)
    target_delta: Fraction = Fraction(0)


def perturb(pop: Population, cell: str, delta: Fraction) -> Population:
    d=pop.as_dict(); require(cell in d, "UNKNOWN_POPULATION_CELL", cell)
    d[cell]+=delta
    require(d[cell] >= 0, "NEGATIVE_PERTURBED_MASS", cell)
    return Population.from_mapping(d)


def apply_pair(source: Population,target: Population,p: Perturbation) -> tuple[Population,Population]:
    return perturb(source,p.cell,p.source_delta), perturb(target,p.cell,p.target_delta)
