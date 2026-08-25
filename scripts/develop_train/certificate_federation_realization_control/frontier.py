from .errors import Refused

def current(calibrations):
    values = tuple(calibrations)
    if not values:
        raise Refused("NO_FEDERATION_CALIBRATION")
    generation = max(c.generation for c in values)
    latest = [c for c in values if c.generation == generation]
    digests = {c.digest for c in latest}
    if len(digests) != 1:
        raise Refused("SPLIT_FEDERATION_CALIBRATION")
    return sorted(latest, key=lambda c: c.digest)[0]
