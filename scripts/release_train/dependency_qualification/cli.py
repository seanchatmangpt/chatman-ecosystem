import json, sys
from . import DependencySubject
from .candidate import Candidate
from .planner import plan
from .policy import DependencyPolicy
from .receipt import canonical, replay

def main(argv=None):
    data=json.load(sys.stdin); policy=DependencyPolicy(frozenset(data['allowed_repos']),frozenset(data['allowed_licenses']))
    candidates=[Candidate(DependencySubject(c['repo'],c['sha']),c['criticality'],c['blockers_removed'],c['evidence']) for c in data['candidates']]
    payload, receipt=plan(policy,candidates,{k:tuple(v) for k,v in data['edges'].items()}); replay(receipt); print(canonical({'plan':payload,'receipt':receipt})); return 0
if __name__=='__main__': raise SystemExit(main())
