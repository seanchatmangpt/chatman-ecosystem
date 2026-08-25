from .certificate import Certificate
from .refusal import Refused
from .transport import Observation, TransportState

def admit_observations(certificate: Certificate, observations: list[Observation]) -> tuple[Observation, ...]:
    seen=set()
    out=[]
    for obs in observations:
        if obs.subject != certificate.subject:
            raise Refused("FOREIGN_SUBJECT")
        if obs.generation != certificate.generation:
            raise Refused("FOREIGN_GENERATION")
        if obs.transport_id in seen:
            raise Refused("DUPLICATE_TRANSPORT", obs.transport_id)
        seen.add(obs.transport_id)
        if obs.state == TransportState.RESOLVED:
            if obs.certificate_digest != certificate.certificate_digest:
                raise Refused("CERTIFICATE_DIGEST_MISMATCH")
            if obs.semantic_digest != certificate.semantic_digest:
                raise Refused("SEMANTIC_DIGEST_MISMATCH")
        out.append(obs)
    if not out:
        raise Refused("EMPTY_OBSERVATION_SET")
    return tuple(sorted(out, key=lambda o: o.transport_id))
