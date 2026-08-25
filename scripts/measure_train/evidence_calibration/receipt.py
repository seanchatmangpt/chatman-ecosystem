import json,hashlib
def manufacture_receipt(subject, estimates, seq, standing_value, undercalibrated, parent=None):
    body={
      "schema":"chatman.measure-evidence-calibration/1",
      "repo":subject.repo,"sha":subject.sha,
      "calibration":[{"source_id":e.source_id,"n":e.n,"tpr":round(e.true_positive_rate,12),
                      "fpr":round(e.false_positive_rate,12),"brier":round(e.brier_score,12),
                      "lower_precision_bound":round(e.lower_precision_bound,12)} for e in sorted(estimates,key=lambda x:x.source_id)],
      "log_lr":round(seq.log_lr,12),"decision":seq.decision,
      "undercalibrated":list(sorted(undercalibrated)),
      "standing":standing_value,"parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
