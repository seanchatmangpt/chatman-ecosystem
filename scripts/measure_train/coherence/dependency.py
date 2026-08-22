from dataclasses import dataclass
from .coherence import Standing
from .subject import Subject, Refusal

@dataclass(frozen=True)
class NodeStanding:
    subject: Subject
    standing: Standing

def propagate(nodes: list[NodeStanding], edges: dict[str,set[str]]):
    by_repo={n.subject.repo:n for n in nodes}
    visiting=set(); visited=set(); out={}
    def visit(repo):
        if repo in visiting: raise Refusal("DEPENDENCY_CYCLE")
        if repo not in by_repo: raise Refusal("MISSING_DEPENDENCY_SUBJECT")
        if repo in visited: return out[repo]
        visiting.add(repo)
        deps=[visit(d) for d in sorted(edges.get(repo,set()))]
        own=by_repo[repo].standing
        if any(d in {Standing.BUILD_BROKEN,Standing.BLOCKED} for d in deps): value=Standing.BLOCKED
        elif any(d==Standing.UNKNOWN for d in deps) and own==Standing.PARTIAL_ALIVE: value=Standing.UNKNOWN
        else: value=own
        visiting.remove(repo); visited.add(repo); out[repo]=value; return value
    for repo in sorted(by_repo): visit(repo)
    return out
