from .admission import admit
from .coverage import empirical_coverage
from .loss import calibrate_loss
from .witness import calibrate_witness
from .frontier import current_models
from .methodology import coverage as methodology_coverage
from .census import census
from .standing import standing
from .receipt import manufacture
from .telemetry import project
def qualify(subject,observations,models,now,member,dependencies=()):
    rows=admit(subject,observations,now); current=current_models(models); cov=empirical_coverage(rows,member); loss=calibrate_loss(rows); witness=calibrate_witness(rows,require_observed=True); methods=methodology_coverage(r.methodology for r in rows); status=standing(cov,loss,witness,methods["complete"],dependencies); rows_census=census(rows,member); receipt=None if status in {"BUILD_BROKEN","BLOCKED"} else manufacture(subject,current,rows_census,status)
    return {"coverage":cov,"loss_calibration":loss,"witness_calibration":witness,"methodology":methods,"models":current,"census":rows_census,"standing":status,"receipt":receipt,"telemetry":project(subject,cov,loss,witness,status),"actuation_performed":False}
