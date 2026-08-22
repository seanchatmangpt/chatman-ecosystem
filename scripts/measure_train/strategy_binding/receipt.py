import hashlib, json

def manufacture_receipt(proof, selected, standing_value, parent=None):
    body={"schema":"chatman.measure-strategy-binding/1","consumer_repo":proof.consumer.repo,"consumer_sha":proof.consumer.sha,
          "selected_cut_id":selected.cut_id,"cut_generation":selected.generation,"strategy_digest":proof.strategy_digest,
          "frontier_digest":proof.frontier_digest,"proof_id":proof.proof_id,"standing":standing_value,
          "parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
