import hashlib
import json

def manufacture_receipt(epoch, census, discharges, regressions, standing_value, parent=None):
    body = {
        "schema": "chatman.measure-process-intelligence-transition/1",
        "repo": epoch.subject.repo,
        "sha": epoch.subject.sha,
        "generation": epoch.generation,
        "census": [list(row) for row in census],
        "discharges": [
            [d.obligation_id, d.before_state, d.after_state, list(d.proof_source_ids)]
            for d in discharges
        ],
        "regressions": [
            [r.obligation_id, r.before_state, r.after_state, r.severity]
            for r in regressions
        ],
        "standing": standing_value,
        "parent": parent,
        "authority": "OBSERVE|VERIFY",
        "actuation_performed": False,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return {"body": body, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
