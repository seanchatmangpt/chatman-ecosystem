import hashlib, json
from .authority import ActionClass, admit
from .failures import require_failure_worlds
from .methods import require_methodologies
from .receipt import Receipt
from .standing import compute

class Qualification:
    def __init__(self, subject, generation, methodologies, failure_worlds, dependency_graph, dependency_root, evidence_summary, transport_summary):
        self.subject=subject; self.generation=generation; self.methodologies=methodologies; self.failure_worlds=failure_worlds; self.dependency_graph=dependency_graph; self.dependency_root=dependency_root; self.evidence_summary=evidence_summary; self.transport_summary=transport_summary
    def qualify(self):
        require_methodologies(self.methodologies); require_failure_worlds(self.failure_worlds); admit(ActionClass.SELECT)
        blockers=self.dependency_graph.blockers(self.dependency_root)
        states=[self.dependency_graph.standing.get(x,"UNKNOWN") for x in blockers]
        standing=compute(*states) if blockers else "PARTIAL_ALIVE"
        if standing in {"BUILD_BROKEN","BLOCKED"}: return standing, None
        ed=hashlib.sha256(json.dumps(self.evidence_summary,sort_keys=True,default=str).encode()).hexdigest()
        td=hashlib.sha256(json.dumps(self.transport_summary,sort_keys=True,default=str).encode()).hexdigest()
        r=Receipt(self.subject.key,self.generation,standing,ed,td)
        return standing,r
