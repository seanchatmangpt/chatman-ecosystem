import hashlib, json

def manufacture_receipt(consumer, before, after, proof, admission, standing_value, parent=None):
    body={"schema":"chatman.measure-recovery-witness/1",
          "consumer_repo":consumer.repo,"consumer_sha":consumer.sha,
          "before":before.digest,"after":after.digest,
          "proof":proof.digest,"strategy":proof.strategy,
          "witness_id":None if proof.witness is None else proof.witness.witness_id,
          "admission":admission,"standing":standing_value,"parent":parent,
          "actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
