import json,hashlib
def manufacture_receipt(subject,quorum,observability,model,standing,parent=None):
    body={"schema":"chatman.measure-replica-quorum-msa/1","repo":subject.repo,"sha":subject.sha,
          "quorum":quorum,"observability":{"coverage":str(observability["coverage"]),"quorum_covered":observability["quorum_covered"],
          "entropy_bits":round(observability["entropy_bits"],12)},"calibration_generation":model.generation if model else None,
          "calibration_digest":model.model_digest if model else None,"standing":standing,"parent":parent,
          "authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
