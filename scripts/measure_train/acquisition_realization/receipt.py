import hashlib, json

def manufacture_receipt(subject, policy_generation, frontier_digest, census_rows, standing_value, parent=None):
    body={
        "schema":"chatman.measure-acquisition-realization/1",
        "repo":subject.repo,
        "sha":subject.sha,
        "policy_generation":policy_generation,
        "frontier_digest":frontier_digest,
        "census":list(census_rows),
        "standing":standing_value,
        "parent":parent,
        "authority":"OBSERVE|VERIFY",
        "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
