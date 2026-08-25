from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class RobustWitness:
    nominal:Fraction; worst:Fraction; radius:Fraction; witness_digest:str
    def __post_init__(self):
        if Fraction(self.worst)<Fraction(self.nominal): raise Refused("NON_MONOTONE_ROBUST_OBJECTIVE")
        if Fraction(self.radius)<0 or len(self.witness_digest)<8: raise Refused("INVALID_ROBUST_WITNESS")
