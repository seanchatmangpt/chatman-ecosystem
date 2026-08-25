from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True, order=True)
class Event:
    activity:str; object_id:str; lifecycle:str="complete"
    def __post_init__(self):
        if not self.activity or not self.object_id or not self.lifecycle: raise Refused("INVALID_EVENT")
