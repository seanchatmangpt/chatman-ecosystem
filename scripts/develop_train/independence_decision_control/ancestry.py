from dataclasses import dataclass

from .errors import Refused


@dataclass(frozen=True)
class EvidenceNode:
    id: str
    parents: tuple[str, ...] = ()


class EvidenceGraph:
    def __init__(self, nodes):
        nodes = tuple(nodes)
        self.nodes = {node.id: node for node in nodes}
        if len(self.nodes) != len(nodes):
            raise Refused("DUPLICATE_EVIDENCE")
        for node in self.nodes.values():
            if node.id in node.parents:
                raise Refused("EVIDENCE_CYCLE")
            if any(parent not in self.nodes for parent in node.parents):
                raise Refused("MISSING_PARENT")
        self._validate_acyclic()

    def _validate_acyclic(self):
        seen = set()
        active = set()

        def visit(identifier):
            if identifier in active:
                raise Refused("EVIDENCE_CYCLE")
            if identifier in seen:
                return
            active.add(identifier)
            for parent in self.nodes[identifier].parents:
                visit(parent)
            active.remove(identifier)
            seen.add(identifier)

        for identifier in self.nodes:
            visit(identifier)

    def ancestors(self, identifier):
        output = set()
        stack = list(self.nodes[identifier].parents)
        while stack:
            current = stack.pop()
            if current not in output:
                output.add(current)
                stack.extend(self.nodes[current].parents)
        return frozenset(output)

    def overlap(self, left, right):
        return self.ancestors(left) & self.ancestors(right)
