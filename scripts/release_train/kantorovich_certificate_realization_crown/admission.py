from .refusal import Refused
def admit(certificate, observations):
    certificate.validate()
    seen=set(); out=[]
    for o in observations:
        o.validate()
        if o.observation_id in seen: raise Refused("DUPLICATE_OBSERVATION")
        if o.certificate_digest != certificate.digest: raise Refused("FOREIGN_CERTIFICATE")
        if o.generation != certificate.generation: raise Refused("FOREIGN_GENERATION")
        seen.add(o.observation_id); out.append(o)
    if not out: raise Refused("EMPTY_OBSERVATIONS")
    return tuple(out)
