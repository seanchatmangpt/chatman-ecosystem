import hashlib,json
def manufacture_receipt(subject, cohort, synchrony, census_rows, standing_value, parent=None):
    body={"schema":"chatman.measure-calibration-cohort/1","repo":subject.repo,"sha":subject.sha,
          "epochs":[{"source":e.source,"repo":e.subject.repo,"sha":e.subject.sha,"generation":e.generation,
                     "model":e.model_digest,"schema":e.schema.fingerprint,"window":[e.window.start.isoformat(),e.window.end.isoformat()],
                     "support":e.support,"state":e.state} for e in sorted(cohort.epochs)],
          "synchrony":{"common_micros":synchrony.common_micros,"overlap":[synchrony.overlap.numerator,synchrony.overlap.denominator],
                       "max_end_skew_micros":synchrony.max_end_skew_micros},
          "census":[list(x) for x in census_rows],"standing":standing_value,"parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
