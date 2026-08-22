import hashlib
import json

def manufacture_receipt(subject, current, historical, standing_value, parent=None):
    def row(item):
        return {
            "kind": item.kind,
            "scope": item.scope,
            "source_id": item.source_id,
            "outcome": item.outcome,
            "epoch_sequence": item.epoch.sequence,
            "observed_at": item.epoch.observed_at.isoformat(),
        }
    body = {
        "schema": "chatman.measure-supersession/1",
        "repo": subject.repo,
        "sha": subject.sha,
        "current": [row(item) for item in sorted(current)],
        "historical": [row(item) for item in sorted(historical)],
        "standing": standing_value,
        "parent": parent,
        "actuation_performed": False,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return {"body": body, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
