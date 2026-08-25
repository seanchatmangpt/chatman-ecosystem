from .association import associations
from .correlation import matrix,require_bounds
from .effective_sample import effective_sample
from .clusters import clusters
from .capital import capitalize
from .methodology import require_complete
from .standing import standing
from .receipt import manufacture
def qualify(subject,rows,calibration,dependency_states=()):
    a=associations(rows); ids=sorted({r.transport.transport_id for r in rows}); m=matrix(ids,a); require_bounds(m); cap=capitalize(effective_sample(m),clusters(ids,a)); require_complete({r.methodology for r in rows}); status=standing(calibration,cap,dependency_states); rec=None if status in {"BUILD_BROKEN","BLOCKED"} else manufacture(subject,cap,calibration,status); return {"associations":a,"capital":cap,"standing":status,"receipt":rec,"actuation_performed":False}
