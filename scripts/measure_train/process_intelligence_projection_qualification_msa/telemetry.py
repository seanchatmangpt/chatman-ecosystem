def project(subject,observations,standing_value):
    events=[{"activity":"pi_projection_observed","repo":subject.repo,"sha":subject.sha,"projection_id":o.projection.projection_id,"methodology":o.projection.methodology,"engine":o.projection.engine,"state":o.state} for o in observations]
    events.append({"activity":"pi_projection_qualified","repo":subject.repo,"sha":subject.sha,"standing":standing_value}); return tuple(events)
