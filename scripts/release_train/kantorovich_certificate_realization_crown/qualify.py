from .admission import admit
from .feasibility import measure
from .differential import oracle_differential
from .independence import witness
from .calibration import calibrate
from .methodologies import require as require_methods
from .failures import require as require_failures
from .dependencies import blockers
from .standing import compute
from .receipt import Receipt
from .refusal import Refused
def qualify(subject, certificate, observations, graph, dependency_standing):
    obs=admit(certificate, observations)
    f=measure(certificate)
    if not f.exact: raise Refused('CERTIFICATE_NOT_EXACT')
    d=oracle_differential(obs)
    if d.max_gap: raise Refused('ORACLE_DIFFERENTIAL')
    witness(obs)
    cal=calibrate(certificate, obs)
    methods=require_methods(obs); failures=require_failures(obs)
    b=blockers(graph, dependency_standing)
    standing=compute(True,cal,b,methods,failures)
    if standing in {'BUILD_BROKEN','BLOCKED'}: return standing,None
    return standing, Receipt.make({'schema':'chatman.kantorovich-certificate-realization-crown/1','subject':subject.identity,'certificate':certificate.digest,'standing':standing,'authority':'SELECT'})
