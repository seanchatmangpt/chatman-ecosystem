from .authority import admit_action
from .candidate import select
from .graph import dependency_closure
from .receipt import manufacture

def plan(policy, candidates, edges):
    admit_action(policy,'SELECT'); winner=select(candidates); closure=dependency_closure(winner.subject.repo,edges); admit_action(policy,'CONSTRUCT')
    payload={'selected':winner.subject.key,'score':winner.score,'closure':closure,'standing':'PARTIAL_ALIVE'}
    return payload, manufacture(payload)
