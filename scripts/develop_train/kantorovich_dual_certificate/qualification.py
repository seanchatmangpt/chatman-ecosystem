from dataclasses import dataclass
import hashlib, json
from .primal import solve_primal
from .dual import derive_dual
from .certificate import verify_certificate
from .methods import require_methods
from .correspondence import require_engines, require_oracles
from .failure import require_failures
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing: str
    transport_cost: object
    dual_gap: object
    receipt: Receipt | None
def _digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
def qualify(subject, source, target, metric, calibration, methods, engines, oracles, failures, dependencies=()):
    hard = next((item for item in dependencies if item in {"BUILD_BROKEN","BLOCKED"}), None)
    if hard:
        return Qualification(hard, None, None, None)
    plan = solve_primal(source, target, metric); dual = derive_dual(plan, source, target, metric); cert = verify_certificate(source, target, metric, plan, dual)
    require_methods(methods); require_engines(engines); require_oracles(oracles, "powl"); require_oracles(oracles, "ocel"); require_failures(failures)
    standing = "PARTIAL_ALIVE" if calibration.admitted() and cert.gap == 0 else "UNKNOWN"
    receipt = Receipt(subject.key, standing, _digest(plan.flows), _digest({"source":dual.source,"target":dual.target}), _digest(cert.__dict__))
    return Qualification(standing, cert.primal_value, cert.gap, receipt)
