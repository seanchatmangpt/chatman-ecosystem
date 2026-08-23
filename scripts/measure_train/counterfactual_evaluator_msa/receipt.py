import hashlib,json

def manufacture_receipt(subject,frontier_digest,consensus,census,standing_value,parent=None):
    body={"schema":"chatman.measure-counterfactual-evaluator-msa/1","repo":subject.repo,"sha":subject.sha,"frontier_digest":frontier_digest,"consensus":{k:str(v) for k,v in consensus.items()},"census":census,"standing":standing_value,"parent":parent,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
