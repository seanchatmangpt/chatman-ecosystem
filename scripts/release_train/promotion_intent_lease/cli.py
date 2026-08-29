import json, sys
from datetime import datetime
from .subject import Subject
from .cut import CutIdentity
from .strategy import StrategyBinding
from .intent import PromotionIntent
from .lease import IntentLease
from .frontier import PromotionFrontier
from .dependency import DependencyGraph
from .candidate import PersistenceNeed
from .engine import qualify

def run(data: dict) -> dict:
    producers=tuple(Subject.parse(x) for x in data['producers'])
    cut=CutIdentity(data['cut_id'],data['cut_generation'],producers)
    strategy=StrategyBinding.from_name(data['strategy'], tuple((k,str(v)) for k,v in data.get('strategy_parameters',{}).items()))
    intent=PromotionIntent(Subject.parse(data['consumer']),cut,strategy,data['policy_digest'],data['nonce'])
    lease=IntentLease(datetime.fromisoformat(data['not_before']),datetime.fromisoformat(data['expires_at']))
    frontier=PromotionFrontier(cut,strategy,data['policy_digest'])
    edges=tuple((Subject.parse(a),Subject.parse(b)) for a,b in data.get('edges',[]))
    q=qualify(intent,lease,frontier,datetime.fromisoformat(data['now']),DependencyGraph(edges),tuple(data['outcomes']),PersistenceNeed(**data.get('persistence',{})))
    return {'standing':q.standing,'store':q.store,'phases':list(q.plan.phases),'receipt_digest':q.receipt.digest,'replay':q.receipt.replay(),'actuation_performed':False}

def main():
    print(json.dumps(run(json.load(sys.stdin)),sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
