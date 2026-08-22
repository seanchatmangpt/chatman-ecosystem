import json,sys
from datetime import datetime
from .engine import qualify
from .event import InvalidationEvent,InvalidationKind
from .frontier import AckFrontier
from .persistence import StoreRequirements
from .strategy import Strategy
from .subject import Subject
from .topology import ConsumerNode,DependencyTopology
def main():
 p=json.load(sys.stdin);producer=Subject(p['producer']['repo'],p['producer']['sha'])
 e=InvalidationEvent(producer,InvalidationKind(p['event']['kind']),p['event']['id'],datetime.fromisoformat(p['event']['occurred_at']),p['event'].get('replacement_receipt'))
 nodes=[ConsumerNode(Subject(x['repo'],x['sha']),bool(x.get('critical'))) for x in p['consumers']]
 g=DependencyTopology(producer,nodes,[tuple(x) for x in p['edges']]);f=AckFrontier.from_consumers([(n.subject,n.critical) for n in nodes])
 for x in p.get('discharged',[]):f.record(Subject(x['repo'],x['sha']),x['receipt'])
 q=qualify(producer=producer,event=e,topology=g,frontier=f,strategy=Strategy(p['strategy']),requirements=StoreRequirements(**p.get('store',{})),evidence=p.get('evidence',{}))
 print(json.dumps({'complete':q.complete,'standing':q.standing,'store':q.store,'receipt_digest':q.receipt_digest,'actuation_performed':False},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
