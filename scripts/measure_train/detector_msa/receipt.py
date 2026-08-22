import hashlib
import json
from .subject import Refused

def manufacture_receipt(subject, frontier, consensus_result, standing, parent=None):
    body = {
        "schema": "chatman.measure-detector-msa/1",
        "repo": subject.repo,
        "sha": subject.sha,
        "frontier": [
            {
                "detector_id": policy.detector_id,
                "policy": policy.fingerprint,
                "generation": policy.generation,
                "calibration_generation": calibration.generation,
                "calibration_state": calibration.state,
                "support": calibration.support,
                "false_alarm_rate": str(calibration.false_alarm_rate),
                "miss_rate": str(calibration.miss_rate),
                "median_delay_seconds": str(calibration.median_delay_seconds),
            }
            for policy, calibration in frontier
        ],
        "consensus": consensus_result,
        "standing": standing,
        "parent": parent,
        "actuation_performed": False,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return {"body": body, "sha256": hashlib.sha256(raw.encode()).hexdigest()}

def replay(receipt):
    body = receipt.get("body", {})
    if body.get("actuation_performed") is not False:
        raise Refused("REFUSED[ACTUATION_IN_MEASUREMENT_RECEIPT]")
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(raw.encode()).hexdigest() != receipt.get("sha256"):
        raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"
