from __future__ import annotations
from dataclasses import dataclass
from .epoch import InvalidationEpoch
from .witness import Witness, WitnessKind, DischargeResult
from .admission import admit_witness

@dataclass(frozen=True, slots=True)
class ConsumerState:
    consumer:str
    state:str
    result:str|None


def current_frontier(epoch:InvalidationEpoch, consumers:tuple[str,...], witnesses:tuple[Witness,...])->tuple[ConsumerState,...]:
    accepted:dict[tuple[str,str],Witness]={}
    for w in sorted(witnesses,key=lambda x:(x.observed_at,x.witness_id)):
        admit_witness(epoch,w,accepted)
        accepted[(w.consumer.value,w.kind.value)] = w
    out=[]
    for c in sorted(consumers):
        d=accepted.get((c,WitnessKind.DELIVERY.value)); a=accepted.get((c,WitnessKind.ACK.value)); s=accepted.get((c,WitnessKind.DISCHARGE.value))
        if d is None: out.append(ConsumerState(c,"PENDING_DELIVERY",None))
        elif a is None: out.append(ConsumerState(c,"PENDING_ACK",None))
        elif s is None: out.append(ConsumerState(c,"PENDING_DISCHARGE",None))
        else: out.append(ConsumerState(c,s.result.value if isinstance(s.result,DischargeResult) else str(s.result),s.result.value if s.result else None))
    return tuple(out)
