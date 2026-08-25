import hashlib,json
def manufacture_receipt(subject, frontier, fusion, consensus, standing, parent=None):
    body={"schema":"chatman.measure-quorum-fusion-msa/1","repo":subject.repo,"sha":subject.sha,
          "frontier":[{"sensor_id":s.sensor_id,"generation":s.generation,"digest":s.calibration_digest} for s in frontier],
          "fusion_state":fusion["state"],"fusion_center":list(fusion["center"]),"consensus_score":consensus["score"],
          "independent_pairs":[list(x) for x in consensus["pairs"]],"standing":standing,"parent":parent,
          "authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
