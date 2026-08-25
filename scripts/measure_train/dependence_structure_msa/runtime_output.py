import json
from .subject import Refused

def admit_runtime_output(raw, expected_worker_sha=None):
    if isinstance(raw, bytes):
        raw=raw.decode("utf-8",errors="strict")
    if not isinstance(raw,str) or not raw.strip():
        raise Refused("REFUSED[EMPTY_RUNTIME_OUTPUT]")
    try:
        payload=json.loads(raw)
    except (json.JSONDecodeError,TypeError,UnicodeDecodeError) as exc:
        raise Refused("REFUSED[INVALID_RUNTIME_JSON]") from exc
    if not isinstance(payload,dict):
        raise Refused("REFUSED[INVALID_RUNTIME_PAYLOAD]")
    if expected_worker_sha is not None:
        observed=(payload.get("subject") or {}).get("sha") or payload.get("worker_sha")
        if observed is not None and observed != expected_worker_sha:
            raise Refused("REFUSED[FOREIGN_RUNTIME_WORKER]")
    result=payload.get("result") or {}
    evidence=payload.get("evidence") or {}
    if payload.get("standing") != "ALIVE":
        raise Refused("REFUSED[RUNTIME_NOT_ALIVE]")
    if result.get("solved") is not True:
        raise Refused("REFUSED[RUNTIME_UNSOLVED]")
    if evidence.get("replay_verified") is not True:
        raise Refused("REFUSED[RUNTIME_REPLAY_UNVERIFIED]")
    return payload
