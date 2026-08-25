from .admission import admit_realization
from .realization import realize_gain
from .budget import realize_budget
from .shapley import shapley_values
from .submodularity import submodularity_ratio
from .regret import observed_regret
from .census import deterministic_census
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project
def qualify(plan,outcomes,sensors,frontier,calibration,cusum,before_distributions,value_fn,realized_alternatives,parent_receipt=None,dependencies=()):
    admitted=admit_realization(plan,outcomes,sensors,frontier,calibration,cusum)
    after=[o.distribution for o in admitted]
    realization=realize_gain(plan.predicted_gain_bits,before_distributions,after)
    budget=realize_budget(plan,admitted)
    sv=shapley_values(plan.sensor_ids,value_fn); gamma=submodularity_ratio(plan.sensor_ids,value_fn)
    regret=observed_regret(plan.plan_id,realized_alternatives)
    census=deterministic_census(realization,budget,calibration,cusum,sv,gamma,regret)
    status=standing(census,dependencies)
    receipt=manufacture_receipt(plan.subject,plan,frontier,census,status,parent_receipt)
    return {"standing":status,"census":census,"receipt":receipt,"telemetry":project(plan,admitted,realization,status),"actuation_performed":False}
