import hashlib,json

def manufacture(subject, convergence, cut, standing_value):
    body={
        "schema":"chatman.measure-process-intelligence-convergence/1",
        "repo":subject.repo,
        "sha":subject.sha,
        "generation":subject.generation,
        "direction":convergence.direction,
        "initial_potential":[convergence.initial_potential.numerator,convergence.initial_potential.denominator],
        "final_potential":[convergence.final_potential.numerator,convergence.final_potential.denominator],
        "net_delta":[convergence.net_delta.numerator,convergence.net_delta.denominator],
        "oscillating_obligations":list(convergence.oscillating_obligations),
        "blocking_cut":list(cut),
        "standing":standing_value,
        "authority":"OBSERVE|VERIFY",
        "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
