import hashlib,json

def manufacture(subject, pair_census, calibration, standing_value):
    body={
      "schema":"chatman.measure-dependence-structure-msa/1",
      "repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,
      "pairs":[list(row) for row in sorted(pair_census)],
      "calibration":{
        "support":calibration.support,
        "false_independent":[calibration.false_independent_rate.numerator,calibration.false_independent_rate.denominator],
        "false_dependent":[calibration.false_dependent_rate.numerator,calibration.false_dependent_rate.denominator],
        "state":calibration.state,
      },
      "standing":standing_value,
      "authority":"OBSERVE|VERIFY",
      "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
