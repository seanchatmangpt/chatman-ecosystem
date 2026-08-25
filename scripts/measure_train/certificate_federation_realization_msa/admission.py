from .subject import Refused

def admit(certificate, observations, now):
    seen = {}
    for observation in observations:
        if observation.certificate != certificate:
            raise Refused("REFUSED[FOREIGN_CERTIFICATE]")
        if observation.observed_at > now:
            raise Refused("REFUSED[FUTURE_EVIDENCE]")
        previous = seen.get(observation.transport_id)
        if previous is not None and previous != observation:
            raise Refused("REFUSED[CONTRADICTORY_TRANSPORT_OBSERVATION]")
        seen[observation.transport_id] = observation
    return tuple(sorted(seen.values(), key=lambda row: row.transport_id))
