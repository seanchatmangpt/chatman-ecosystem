from dataclasses import dataclass
import hashlib,json
from .subject import Subject
from .refusal import Refused
@dataclass(frozen=True)
class Receipt:
    subject:Subject; generation:int; standing:str; evidence_ids:tuple[str,...]; parent_digests:tuple[str,...]; authority:str='SELECT'; actuation_performed:bool=False
    def body(self):
        if self.actuation_performed: raise Refused("UNRECEIPTED_ACTUATION_REPORTED")
        return {'schema':'chatman.process-evidence-crown/1','subject':self.subject.key,'generation':self.generation,'standing':self.standing,'evidence_ids':sorted(self.evidence_ids),'parents':sorted(self.parent_digests),'authority':self.authority,'actuation_performed':False}
    @property
    def digest(self): return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
