from .errors import Refused

class EvidenceGraph:
    def __init__(self, evidence):
        items = tuple(evidence)
        self.nodes = {e.evidence_id: e for e in items}
        if len(self.nodes) != len(items):
            raise Refused("DUPLICATE_EVIDENCE")
        for e in self.nodes.values():
            for parent in e.parents:
                if parent not in self.nodes:
                    raise Refused("MISSING_PARENT", parent)
        self._order = self._topological()

    def _topological(self):
        state = {}
        out = []
        def visit(key):
            if state.get(key) == 1:
                raise Refused("EVIDENCE_CYCLE", key)
            if state.get(key) == 2:
                return
            state[key] = 1
            for parent in self.nodes[key].parents:
                visit(parent)
            state[key] = 2
            out.append(key)
        for key in sorted(self.nodes):
            visit(key)
        return tuple(out)

    @property
    def order(self): return self._order

    def ancestors(self, evidence_id):
        if evidence_id not in self.nodes:
            raise Refused("UNKNOWN_EVIDENCE", evidence_id)
        seen = set()
        def walk(key):
            for parent in self.nodes[key].parents:
                if parent not in seen:
                    seen.add(parent); walk(parent)
        walk(evidence_id)
        return frozenset(seen)
