import hashlib,json

def manufacture(subject,census,bounds,standing_value):
    body={
      "schema":"chatman.measure-manifest-reference-observability/1",
      "repo":subject.repo,
      "sha":subject.sha,
      "census":[list(r) for r in census],
      "currentness_lower":[bounds.lower.numerator,bounds.lower.denominator],
      "currentness_upper":[bounds.upper.numerator,bounds.upper.denominator],
      "standing":standing_value,
      "authority":"OBSERVE|VERIFY",
      "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
