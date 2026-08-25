from dataclasses import dataclass
from enum import StrEnum
import re
from .errors import Refused
class PolicyFamily(StrEnum):
    CURRENT='CURRENT'; LOWER_BOUND='LOWER_BOUND'; MIN_WIDTH='MIN_WIDTH'; MAX_BREAKDOWN='MAX_BREAKDOWN'; CONSERVATIVE_DR='CONSERVATIVE_DR'
@dataclass(frozen=True, slots=True)
class PolicyIdentity:
    generation:int; digest:str; family:PolicyFamily
    def __post_init__(self):
        if self.generation < 0 or not re.fullmatch(r'[0-9a-f]{64}', self.digest): raise Refused('REFUSED_POLICY_IDENTITY')
