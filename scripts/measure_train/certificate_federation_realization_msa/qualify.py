from .admission import admit
from .coverage import coverage
from .methodology import require
from .standing import standing
from .receipt import manufacture

def qualify(certificate, observations, calibration, required_transports, methods, dependency_states, now, worst_failure_rate=0.0):
    rows = admit(certificate, observations, now)
    transport_coverage = coverage(rows, required_transports)
    methodology_ok = require(methods)
    status = standing(calibration, dependency_states, transport_coverage == 1, methodology_ok, worst_failure_rate)
    receipt = None if status in {"BUILD_BROKEN", "BLOCKED"} else manufacture(certificate, calibration, status)
    telemetry = tuple({
        "activity": "certificate_federation_observation",
        "repo": certificate.subject.repo,
        "sha": certificate.subject.sha,
        "transport": row.transport_id,
        "state": row.state,
        "relation": row.relation,
        "standing": status,
    } for row in rows)
    return {"standing": status, "coverage": transport_coverage, "receipt": receipt, "telemetry": telemetry, "actuation_performed": False}
