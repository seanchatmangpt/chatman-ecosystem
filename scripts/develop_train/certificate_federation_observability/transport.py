from dataclasses import dataclass
from enum import Enum
from .errors import Refused
class TransportState(str,Enum): RESOLVED="RESOLVED"; TIMEOUT="TIMEOUT"; DNS="DNS"; HTTP_ERROR="HTTP_ERROR"
@dataclass(frozen=True)
class Transport:
    transport_id:str; implementation:str; model:str; domain:str
    def __post_init__(self):
        if not all((self.transport_id,self.implementation,self.model,self.domain)): raise Refused("INCOMPLETE_TRANSPORT_IDENTITY")
