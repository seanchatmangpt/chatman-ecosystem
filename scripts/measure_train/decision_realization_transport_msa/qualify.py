from .population import distribution
from .overlap import support_overlap
from .weights import importance_weights,effective_sample_size
from .transport import transported_risk
from .calibration import transport_calibration_gap
from .simpson import simpson_reversal
from .standing import standing
from .receipt import manufacture
from .telemetry import project
def qualify(subject,source,target,model,dependency_states=()):
    sd=distribution(source); td=distribution(target)
    ov=support_overlap(sd,td); w=importance_weights(sd,td); ess=effective_sample_size(source,w)
    risk=transported_risk(source,w); gap=transport_calibration_gap(source,target); sim=simpson_reversal(source,target)
    status=standing(model,ov["fraction"],float(ess),float(gap),sim,dependency_states)
    metrics={"overlap":ov["fraction"],"ess":float(ess),"transported_risk":float(risk),"calibration_gap":float(gap),"simpson_reversal":sim}
    r=manufacture(subject,model,status,metrics)
    return {"standing":status,"metrics":metrics,"receipt":r,"telemetry":project(subject,model,status,metrics),"actuation_performed":False}
