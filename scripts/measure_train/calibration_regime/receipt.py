import hashlib, json

def manufacture_receipt(subject, source_id, model, generation, drift_vector, drift_state, standing, parent=None):
    body={
      "schema":"chatman.measure-calibration-regime/1",
      "repo":subject.repo,"sha":subject.sha,"source_id":source_id,
      "model_id":model.model_id,"window_start":model.window.start.isoformat(),"window_end":model.window.end.isoformat(),
      "generation":generation,
      "drift":{"tpr":[drift_vector.delta_tpr.numerator,drift_vector.delta_tpr.denominator],
               "fpr":[drift_vector.delta_fpr.numerator,drift_vector.delta_fpr.denominator],
               "brier":[drift_vector.delta_brier.numerator,drift_vector.delta_brier.denominator]},
      "drift_state":drift_state,"standing":standing,"parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
