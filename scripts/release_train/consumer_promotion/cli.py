import json, sys
from datetime import datetime
from .subject import Subject
from .evidence import ProducerEvidence
from .lease import EvidenceLease
from .claim import ConsumptionClaim
from .candidate import Candidate
from .engine import manufacture_plan
from .receipt import replay
def main()->int:
    d=json.load(sys.stdin)
    consumer=Subject(d["consumer"]["repo"],d["consumer"]["sha"]); producer=Subject(d["producer"]["repo"],d["producer"]["sha"])
    lease=EvidenceLease(datetime.fromisoformat(d["lease"]["issued_at"]),datetime.fromisoformat(d["lease"]["expires_at"]))
    ev=ProducerEvidence(producer,d["receipt"],d["schema"],d["producer_standing"],d["witness_scope"])
    claim=ConsumptionClaim(consumer,producer,d["component"],d["receipt"],d["schema"],d["required_scope"],lease)
    candidates=[Candidate(**x) for x in d["candidates"]]
    plan,receipt=manufacture_plan(claim=claim,evidence=ev,current_receipt=d["current_receipt"],current_schema=d["current_schema"],
        now=datetime.fromisoformat(d["now"]),deps={k:set(v) for k,v in d["deps"].items()},standing=d["standing"],candidates=candidates)
    out={"plan":plan,"receipt":{"schema":receipt.schema,"payload":receipt.payload,"digest":receipt.digest},"replay":replay(receipt)}
    print(json.dumps(out,sort_keys=True,separators=(",",":"))); return 0
if __name__=="__main__": raise SystemExit(main())
