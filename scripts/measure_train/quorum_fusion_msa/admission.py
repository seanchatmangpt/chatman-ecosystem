from .subject import Refused
def admit(sensors, calibrations, current_sensors, max_fcr=0.1, max_fsr=0.1, max_ambiguity=0.2):
    current={s.sensor_id:s for s in current_sensors}
    admitted=[]
    for s,c in zip(sensors,calibrations):
        if current.get(s.sensor_id)!=s: raise Refused("REFUSED[STALE_SENSOR_CALIBRATION]")
        if c.support<5: raise Refused("REFUSED[UNDER_SUPPORTED_SENSOR]")
        if c.false_current_rate>max_fcr: raise Refused("REFUSED[FALSE_CURRENT_EXCESS]")
        if c.false_stale_rate>max_fsr: raise Refused("REFUSED[FALSE_STALE_EXCESS]")
        if c.ambiguity_rate>max_ambiguity: raise Refused("REFUSED[AMBIGUITY_EXCESS]")
        admitted.append(c)
    return tuple(admitted)
