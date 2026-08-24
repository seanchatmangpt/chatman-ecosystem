from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from .errors import Refused
class Strategy(str,Enum): MAX_EFFECTIVE_GAIN='MAX_EFFECTIVE_GAIN'; MIN_CORRELATION='MIN_CORRELATION'; MIN_COST='MIN_COST'; COVERAGE_FIRST='COVERAGE_FIRST'
@dataclass(frozen=True)
class Candidate: transport_id:str; expected_gain:Fraction; max_abs_rho:Fraction; cost:Fraction; new_methodology:bool
def select(cs,strategy):
    cs=tuple(cs)
    if not cs: raise Refused('NO_SELECTION_CANDIDATES')
    if strategy==Strategy.MAX_EFFECTIVE_GAIN:return max(cs,key=lambda c:(c.expected_gain,-c.cost,c.transport_id))
    if strategy==Strategy.MIN_CORRELATION:return min(cs,key=lambda c:(c.max_abs_rho,c.cost,c.transport_id))
    if strategy==Strategy.MIN_COST:return min(cs,key=lambda c:(c.cost,-c.expected_gain,c.transport_id))
    if strategy==Strategy.COVERAGE_FIRST:return max(cs,key=lambda c:(c.new_methodology,c.expected_gain,-c.cost,c.transport_id))
    raise Refused('UNKNOWN_SELECTION_STRATEGY')
