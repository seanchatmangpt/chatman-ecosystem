def project(subject, sensors, calibrations, fusion, standing):
    return tuple({"activity":"measure_quorum_fusion","repo":subject.repo,"sha":subject.sha,
                  "sensor_id":s.sensor_id,"generation":s.generation,"support":c.support,
                  "false_current_rate":c.false_current_rate,"false_stale_rate":c.false_stale_rate,
                  "ambiguity_rate":c.ambiguity_rate,"fusion_state":fusion["state"],"standing":standing}
                 for s,c in sorted(zip(sensors,calibrations),key=lambda x:x[0].sensor_id))
