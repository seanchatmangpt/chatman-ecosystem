import hashlib
import json

def manufacture(subject, model, status, capability, effective):
    body = {
        "schema": "chatman.measure-federation-convergence-kinetics/1",
        "repo": subject.repo,
        "sha": subject.sha,
        "semantic_digest": subject.semantic_digest,
        "generation": subject.generation,
        "model_generation": model.generation,
        "model_digest": model.digest,
        "standing": status,
        "on_time": [capability.successes, capability.support],
        "effective_episodes": effective.effective,
        "authority": "OBSERVE|VERIFY",
        "actuation_performed": False,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return {"body": body, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
