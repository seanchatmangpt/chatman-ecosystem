import hashlib,json
from dataclasses import dataclass
from .subject import Subject
from .event import Event
from .errors import Refused
@dataclass(frozen=True)
class Trace:
    subject:Subject; engine:str; events:tuple[Event,...]
    generation:int=0
    def __post_init__(self):
        if not self.engine: raise Refused("EMPTY_ENGINE")
        if self.generation<0: raise Refused("NEGATIVE_GENERATION")
        if not self.events: raise Refused("EMPTY_TRACE")
    @property
    def body(self): return {"subject":self.subject.value,"engine":self.engine,"generation":self.generation,"events":[e.__dict__ for e in self.events]}
    @property
    def digest(self): return hashlib.sha256(json.dumps(self.body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
