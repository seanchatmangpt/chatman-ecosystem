import hashlib,json

def manufacture(subject, census, standing_value, regret_values, drift_alarm):
    c=census["calibration"]
    body={
      "schema":"chatman.measure-trace-relation-selector-realization/1",
      "repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,
      "decision_count":census["decision_count"],
      "selector_generations":[list(x) for x in census["selector_generations"]],
      "churn":[census["churn"].numerator,census["churn"].denominator],
      "calibration":{"support":c.support,"mae_ppm":[c.mean_abs_error_ppm.numerator,c.mean_abs_error_ppm.denominator],"state":c.state},
      "regret_values":list(regret_values),"drift_alarm":bool(drift_alarm),"standing":standing_value,
      "authority":"OBSERVE|VERIFY","actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
