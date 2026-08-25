from dataclasses import dataclass
import hashlib, json
from .observation import admit as admit_observations
from .propensity import profile, require_support
from .missingness import classify, require_observed
from .risk import self_normalized
from .calibration import calibrate
from .confidence import empirical_bernstein
from .coverage import require_methodologies
from .receipt import Receipt

_HARD = {"BUILD_BROKEN","BLOCKED"}

@dataclass(frozen=True)
class Qualification:
    standing: str
    risk: float
    risk_upper: float
    calibration_gap: float
    receipt: Receipt | None

def qualify(subject, policy, observations, dependencies=()):
    obs = admit_observations(observations, policy.generation)
    hard = next((d for d in dependencies if d in _HARD), None)
    if hard:
        return Qualification(hard, float("inf"), float("inf"), float("inf"), None)

    require_methodologies(obs)
    require_support(profile(obs))
    require_observed(classify(obs))
    risk = self_normalized(policy, obs)
    cal = calibrate(obs, policy.generation, hashlib.sha256(str(policy.generation).encode()).hexdigest())
    bound = empirical_bernstein(
        [0.0 if o.truth_independent == (o.decision.value == "INDEPENDENT") else 1.0
         for o in obs if o.truth_independent is not None],
        value_range=1.0,
    )
    standing = "PARTIAL_ALIVE" if cal.admitted() and bound.upper <= 1.5 else "UNKNOWN"
    payload = {
        "subject": subject.key, "generation":policy.generation, "risk":round(risk,12),
        "risk_upper":round(bound.upper,12), "calibration_gap":round(cal.mean_gap,12),
        "observations":[o.observation_id for o in obs]
    }
    evidence_digest = hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    receipt = Receipt(subject.key, policy.generation, standing, evidence_digest)
    return Qualification(standing, risk, bound.upper, cal.mean_gap, receipt)
