from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Telemetry:
    subject:str
    generation:int
    strategy:str|None
    standing:str
    receipt_digest:str
    actuation_performed:bool
def project(r): return Telemetry(r.subject,r.policy_generation,r.selected_strategy,r.standing,r.digest,r.actuation_performed)
