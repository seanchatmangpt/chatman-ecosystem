from dataclasses import dataclass
from .refusal import refuse
@dataclass(frozen=True)
class Epoch: generation:int; state_digest:str; blockers:int; error_ppm:int
def admit_trajectory(epochs):
    epochs=list(epochs)
    if not epochs: refuse("EMPTY_TRAJECTORY")
    for a,b in zip(epochs,epochs[1:]):
        if b.generation!=a.generation+1: refuse("TORN_GENERATION")
    return tuple(epochs)
