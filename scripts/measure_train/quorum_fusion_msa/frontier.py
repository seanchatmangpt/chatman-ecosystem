from .subject import Refused
def current_frontier(sensors):
    by_id={}
    for s in sensors:
        old=by_id.get(s.sensor_id)
        if old is None or s.generation>old.generation: by_id[s.sensor_id]=s
        elif s.generation==old.generation and s.calibration_digest!=old.calibration_digest:
            raise Refused("REFUSED[DIVERGENT_SENSOR_FRONTIER]")
    return tuple(sorted(by_id.values()))
