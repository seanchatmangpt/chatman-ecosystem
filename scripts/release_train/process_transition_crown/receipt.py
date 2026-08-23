from dataclasses import dataclass
import hashlib, json
from .subject import SubjectEpoch
from .refusal import Refused

@dataclass(frozen=True)
class Receipt:
    subject: SubjectEpoch
    kind: str
    parents: tuple[str,...]
    payload: dict
    actuation_performed: bool=False

    def body(self):
        if self.actuation_performed:
            raise Refused("UNRECEIPTED_AMBIENT_ACTUATION")
        return {"subject":{"repo":self.subject.repo,"sha":self.subject.sha,"generation":self.subject.generation,"semantic_digest":self.subject.semantic_digest},"kind":self.kind,"parents":sorted(self.parents),"payload":self.payload,"actuation_performed":False}

    def digest(self):
        raw=json.dumps(self.body(),sort_keys=True,separators=(",",":"),default=str).encode()
        return hashlib.sha256(raw).hexdigest()
