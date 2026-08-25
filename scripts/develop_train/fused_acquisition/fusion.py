from fractions import Fraction
from statistics import median
from .sensor import Sensor, Observation
from .refusals import Refused

def robust_current_score(sensors: list[Sensor], observations: list[Observation], admitted_ids: set[str]) -> Fraction:
    sensor_map={s.sensor_id:s for s in sensors}
    scores=[]
    seen=set()
    for obs in observations:
        if obs.sensor_id in seen: raise Refused("DUPLICATE_OBSERVATION")
        seen.add(obs.sensor_id)
        if obs.sensor_id not in admitted_ids: continue
        sensor=sensor_map.get(obs.sensor_id)
        if sensor is None or obs.generation != sensor.calibration.generation: raise Refused("STALE_CALIBRATION_BINDING")
        sign={"CURRENT":1,"STALE":-1,"AMBIGUOUS":0}[obs.verdict]
        reliability=max(Fraction(0), Fraction(1)-sensor.calibration.error_mass)
        scores.append(Fraction(sign) * obs.confidence * reliability)
    if len(scores)<2: raise Refused("INSUFFICIENT_INDEPENDENT_OBSERVATIONS")
    return Fraction(median(scores))
