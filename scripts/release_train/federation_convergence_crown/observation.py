from dataclasses import dataclass
from .refusal import refuse
@dataclass(frozen=True)
class Observation:
    subject:object; transport:str; state_digest:str; resolved:bool; unresolved:bool; timestamp:int
    def __post_init__(self):
        if self.resolved and self.unresolved: refuse("RESOLUTION_CONTRADICTION")
        if not self.transport or not self.state_digest: refuse("INVALID_OBSERVATION")
        if self.timestamp<0: refuse("INVALID_TIMESTAMP")
