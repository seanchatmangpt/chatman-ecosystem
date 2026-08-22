from dataclasses import dataclass,asdict
import hashlib,json
@dataclass(frozen=True, slots=True)
class AcquisitionReceipt:
    schema:str; subject:str; frontier_digest:str; strategy:str; candidate_ids:tuple; standing:str; authority:str='SELECT'; actuation_performed:bool=False
    def body(self): return asdict(self)
    def digest(self): return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def issue(subject,frontier_digest,strategy,candidate_ids,standing): return AcquisitionReceipt('chatman.develop-evidence-acquisition/1',subject.key,frontier_digest,strategy.value,candidate_ids,standing)
def replay(receipt,expected_digest): return receipt.schema=='chatman.develop-evidence-acquisition/1' and not receipt.actuation_performed and receipt.authority=='SELECT' and receipt.digest()==expected_digest
