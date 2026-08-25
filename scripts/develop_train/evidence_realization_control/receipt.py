from dataclasses import dataclass
import hashlib,json
@dataclass(frozen=True)
class Receipt:
    subject:str; generation:int; standing:str; evidence_ids:tuple; selector:str; authority:str='SELECT'; actuation_performed:bool=False
    def body(self):
        return {'schema':'chatman.develop-evidence-realization-control/1','subject':self.subject,'generation':self.generation,'standing':self.standing,'evidence_ids':sorted(self.evidence_ids),'selector':self.selector,'authority':self.authority,'actuation_performed':self.actuation_performed}
    def digest(self):
        return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
