import hashlib, json

def manufacture(certificate, calibration, standing_value):
    body = {
        "schema": "chatman.measure-certificate-federation-realization/1",
        "repo": certificate.subject.repo,
        "sha": certificate.subject.sha,
        "certificate_digest": certificate.digest,
        "generation": certificate.generation,
        "support": calibration.support,
        "false_current": [calibration.false_current_rate.numerator, calibration.false_current_rate.denominator],
        "standing": standing_value,
        "authority": "OBSERVE|VERIFY",
        "actuation_performed": False,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return {"body": body, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
