from .blockers import transitive_blockers
from .fixed_point import fixed_point
from .methodology import require_methodologies
from .rails import require_rails
from .regions import require_tls_regions
from .failures import require_failures
from .reactor import require_correspondence
from .standing import compute_standing,require_receiptable
from .receipt import Receipt

def qualify(*, subject, epochs, methods, rails, regions, failures, correspondence, graph=None, failed_dependencies=()):
    blockers=transitive_blockers(graph or {},set(failed_dependencies))
    complete=True
    require_methodologies(methods)
    evidence_digest=require_rails(rails)
    require_tls_regions(regions)
    require_failures(failures)
    require_correspondence(*correspondence)
    standing=compute_standing(fixed=fixed_point(epochs),blockers=blockers,complete=complete)
    if standing in {"BLOCKED","BUILD_BROKEN","UNKNOWN"}:
        return {"standing":standing,"blockers":blockers,"receipt":None}
    require_receiptable(standing)
    receipt=Receipt(subject.key,standing,evidence_digest)
    return {"standing":standing,"blockers":blockers,"receipt":receipt}
