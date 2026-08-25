from datetime import datetime, timezone
from .errors import Refused


def admit(certificate, observations):
    obs = tuple(observations)
    if not obs:
        raise Refused("EMPTY_CERTIFICATE_REALIZATION_SET")
    ids = [item.observation_id for item in obs]
    if len(ids) != len(set(ids)):
        raise Refused("DUPLICATE_CERTIFICATE_OBSERVATION")
    now = datetime.now(timezone.utc)
    for item in obs:
        if item.certificate_digest != certificate.certificate_digest:
            raise Refused("FOREIGN_CERTIFICATE_OBSERVATION")
        if item.certificate_generation != certificate.generation:
            raise Refused("FOREIGN_CERTIFICATE_GENERATION")
        if item.observed_at > now:
            raise Refused("FUTURE_CERTIFICATE_OBSERVATION")
    return tuple(sorted(obs, key=lambda item: (item.observed_at, item.observation_id)))
