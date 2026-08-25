from .census import deterministic_census
from .drift import cusum
from .standing import standing
from .receipt import manufacture
from .telemetry import project

def qualify(subject, decisions, realized_losses, regret_values, dependencies=(), drift_target=0.0, drift_threshold=1.0):
    census=deterministic_census(decisions,realized_losses,dependencies)
    drift=cusum(regret_values,drift_target,drift_threshold)
    status=standing(census,drift.alarm,regret_values)
    receipt=manufacture(subject,census,status,regret_values,drift.alarm)
    return {"census":census,"drift":drift,"standing":status,"receipt":receipt,"telemetry":project(decisions,regret_values,status),"actuation_performed":False}
