from dataclasses import dataclass
from .population import Population
from .errors import Refused

@dataclass(frozen=True)
class Delta:
    cell: str
    amount: float

def apply(population, deltas):
    values = population.data()
    for delta in deltas:
        next_value = values.get(delta.cell, 0) + float(delta.amount)
        if next_value < 0:
            raise Refused("NEGATIVE_PERTURBED_MASS", delta.cell)
        values[delta.cell] = next_value
    return Population.make(population.name + "+stress", values)
