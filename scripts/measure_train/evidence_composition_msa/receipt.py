import hashlib,json
def manufacture(subject, calibration, cut, standing_value):
    body={"schema":"chatman.measure-evidence-composition-msa/1","repo":subject.repo,"sha":subject.sha,
          "semantic_digest":subject.semantic_digest,"support":calibration.support,
          "coverage":[calibration.coverage.numerator,calibration.coverage.denominator],
          "miss_rate":[calibration.miss_rate.numerator,calibration.miss_rate.denominator],
          "blocking_cut":list(cut),"standing":standing_value,
          "authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
