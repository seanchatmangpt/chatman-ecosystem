import hashlib
import json

def manufacture_receipt(selection, selected_candidate, drift_state, standing_value, parent=None):
    body = {
        "schema": "chatman.measure-selection-provenance/1",
        "consumer_repo": selection.consumer.repo,
        "consumer_sha": selection.consumer.sha,
        "selector_id": selection.selector_id,
        "strategy": selection.strategy.name,
        "strategy_fingerprint": selection.strategy.fingerprint,
        "policy_digest": selection.strategy.policy_digest,
        "candidate_set_digest": selection.candidate_set_digest,
        "selected_cut_id": selected_candidate.cut_id,
        "selected_generation": selected_candidate.generation,
        "selector_receipt": selection.selector_receipt,
        "drift": drift_state,
        "standing": standing_value,
        "parent": parent,
        "actuation_performed": False,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return {"body": body, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
