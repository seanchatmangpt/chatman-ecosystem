import hashlib,json
from .refusal import Refused

def manufacture_receipt(subject,policy,census,standing,parent=None):
    body={"schema":"chatman.measure-sequential-policy-msa/1",
          "repo":subject.repo,"sha":subject.sha,
          "policy_id":policy.policy_id,"policy_generation":policy.generation,
          "policy_digest":policy.digest,"strategy":policy.strategy,
          "census":census,"standing":standing,"parent":parent,
          "authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),default=str)
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}

def replay(receipt):
    body=receipt.get("body",{})
    if body.get("authority")!="OBSERVE|VERIFY":
        raise Refused("REFUSED[AUTHORITY_MISMATCH]")
    if body.get("actuation_performed") is not False:
        raise Refused("REFUSED[ACTUATION_IN_MEASUREMENT_RECEIPT]")
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),default=str)
    if hashlib.sha256(raw.encode()).hexdigest()!=receipt.get("sha256"):
        raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"
