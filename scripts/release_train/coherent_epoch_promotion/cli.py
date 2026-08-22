from __future__ import annotations
import json, sys
from datetime import datetime
from .cut import EvidenceCut
from .dependency import DependencyGraph
from .engine import qualify
from .epoch import EpochStamp
from .observation import Observation, Outcome, Scope
from .subject import Subject

def _dt(v: str) -> datetime: return datetime.fromisoformat(v.replace('Z','+00:00'))
def main() -> int:
    raw=json.load(sys.stdin)
    root=Subject.parse(raw['root'])
    epochs=[]; frontier={}
    for item in raw['epochs']:
        e=EpochStamp(Subject.parse(item['producer']),int(item['generation']),item['event_id'],item['receipt'],_dt(item['observed_at']))
        epochs.append(e); frontier[e.producer.repo]=e
    graph=DependencyGraph()
    for c,p in raw.get('dependencies',[]): graph.add(Subject.parse(c),Subject.parse(p))
    graph.edges.setdefault(root,set())
    observations=[]
    epoch_by_repo={e.producer.repo:e for e in epochs}
    for item in raw['observations']:
        epoch=epoch_by_repo[item['producer_repo']]
        observations.append(Observation(Subject.parse(item['consumer']),epoch,Scope(item['scope']),Outcome(item['outcome']),item['evidence_id'],_dt(item['observed_at'])))
    cut=EvidenceCut(_dt(raw['cut_at']),tuple(epochs),tuple(observations))
    out=qualify(root,graph,cut,frontier,bool(raw.get('require_transactional')))
    json.dump(out,sys.stdout,sort_keys=True,separators=(',',':')); sys.stdout.write('\n'); return 0
if __name__=='__main__': raise SystemExit(main())
