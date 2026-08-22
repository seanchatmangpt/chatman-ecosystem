import hashlib,json
from .subject import Refused

def manufacture_receipt(intent, belief, selected, standing):
    body={
      "schema":"chatman.measure-evidence-voi/1",
      "repo":intent.subject.repo,"sha":intent.subject.sha,
      "belief":{"p_alive":str(belief.p_alive),"generation":belief.generation},
      "candidate_ids":list(intent.candidate_ids),
      "frontier_digest":intent.frontier_digest,"strategy":intent.strategy,
      "standing":standing,"authority":"SELECT","actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}

def replay(receipt):
    body=receipt.get("body",{})
    if body.get("authority")!="SELECT" or body.get("actuation_performed") is not False:
        raise Refused("REFUSED[AUTHORITY_OR_ACTUATION_TAMPER]")
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    if hashlib.sha256(raw.encode()).hexdigest()!=receipt.get("sha256"):
        raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"
