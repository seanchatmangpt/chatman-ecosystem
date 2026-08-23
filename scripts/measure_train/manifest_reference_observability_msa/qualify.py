from .admission import admit_observations
from .contradiction import require_consistent
from .census import component_census
from .dependency import dependency_graph,propagate
from .coverage import measure as coverage_measure
from .uncertainty import identify
from .standing import standing
from .receipt import manufacture
from .telemetry import project

def qualify(subject,components,observations,dependency_edges,now):
    components=tuple(components)
    admitted=admit_observations(components,tuple(observations),now)
    require_consistent(admitted)
    census=component_census(components,admitted)
    graph=dependency_graph([c.component_id for c in components],dependency_edges)
    propagated=propagate(census,graph)
    cov=coverage_measure(census)
    bounds=identify(census)
    status=standing(census,propagated)
    receipt=None if status in {"BUILD_BROKEN","BLOCKED"} else manufacture(subject,census,bounds,status)
    return {
      "census":census,
      "graph":graph,
      "propagated":propagated,
      "coverage":cov,
      "bounds":bounds,
      "standing":status,
      "receipt":receipt,
      "telemetry":project(subject,census,bounds,cov,status),
      "actuation_performed":False,
    }
