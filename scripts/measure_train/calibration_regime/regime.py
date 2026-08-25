from dataclasses import dataclass
from .distance import classify_distance
from .subject import Refused

@dataclass(frozen=True, order=True)
class CalibrationRegime:
    generation: int
    model_id: str
    state: str
    def __post_init__(self):
        if self.generation < 0: raise Refused("REFUSED[INVALID_REGIME_GENERATION]")
        if self.state not in {"STABLE","DRIFT"}: raise Refused("REFUSED[INVALID_REGIME_STATE]")

def segment_models(models, threshold):
    if not models: return ()
    ordered=sorted(models,key=lambda m:(m.window.end,m.model_id))
    generation=0; baseline=ordered[0]; out=[CalibrationRegime(generation,baseline.model_id,"STABLE")]
    for model in ordered[1:]:
        state=classify_distance(baseline,model,threshold)
        if state=="DRIFT":
            generation += 1; baseline=model
        out.append(CalibrationRegime(generation,model.model_id,state))
    return tuple(out)
