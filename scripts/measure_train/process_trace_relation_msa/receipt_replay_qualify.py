import hashlib,json
from .census import deterministic_census
from .standing import standing
from .subject import Refused

def manufacture(subject, calibrations, perturbations, dependency_states=()):
    status=standing(calibrations,dependency_states)
    body={
        "schema":"chatman.measure-process-trace-relation-msa/1",
        "repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,
        "census":[list(r) for r in deterministic_census(calibrations,perturbations)],
        "standing":status,"authority":"OBSERVE|VERIFY","actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}

def replay(receipt):
    body=receipt.get("body",{})
    if body.get("authority")!="OBSERVE|VERIFY":
        raise Refused("REFUSED[AUTHORITY_DRIFT]")
    if body.get("actuation_performed") is not False:
        raise Refused("REFUSED[ACTUATION_IN_MEASUREMENT_RECEIPT]")
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    if hashlib.sha256(raw.encode()).hexdigest()!=receipt.get("sha256"):
        raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"

def qualify(subject, calibrations, perturbations, dependency_states=()):
    receipt=manufacture(subject,calibrations,perturbations,dependency_states)
    telemetry=tuple({"activity":"trace_relation_calibration","relation":c.relation.value,
                     "support":c.support,"state":c.state,"repo":subject.repo,"sha":subject.sha}
                    for c in calibrations)
    return {"standing":receipt["body"]["standing"],"receipt":receipt,
            "telemetry":telemetry,"actuation_performed":False}
