from .errors import Refused


def current(calibrations):
    items = tuple(calibrations)
    if not items:
        raise Refused("NO_CERTIFICATE_CALIBRATION")
    generation = max(item.generation for item in items)
    latest = [item for item in items if item.generation == generation]
    if len({item.digest for item in latest}) != 1:
        raise Refused("SPLIT_CERTIFICATE_CALIBRATION_FRONTIER")
    return sorted(latest, key=lambda item: item.digest)[0]
