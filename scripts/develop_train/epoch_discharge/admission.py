from __future__ import annotations
from .epoch import InvalidationEpoch
from .witness import Witness, WitnessKind

def admit_witness(epoch:InvalidationEpoch, witness:Witness, accepted:dict[tuple[str,str],Witness])->None:
    if witness.producer != epoch.producer: raise ValueError("REFUSED[FOREIGN_PRODUCER]")
    if witness.event_id != epoch.event_id: raise ValueError("REFUSED[FOREIGN_EVENT]")
    if witness.generation < epoch.generation: raise ValueError("REFUSED[STALE_INVALIDATION_EPOCH]")
    if witness.generation > epoch.generation: raise ValueError("REFUSED[FUTURE_INVALIDATION_EPOCH]")
    if witness.observed_at < epoch.observed_at: raise ValueError("REFUSED[WITNESS_PREDATES_EPOCH]")
    if witness.kind is WitnessKind.DELIVERY: return
    prior_kind = WitnessKind.DELIVERY if witness.kind is WitnessKind.ACK else WitnessKind.ACK
    prior=accepted.get((witness.consumer.value,prior_kind.value))
    if prior is None: raise ValueError("REFUSED[MISSING_CAUSAL_PARENT]")
    if witness.parent_receipt != prior.receipt_digest: raise ValueError("REFUSED[CAUSAL_RECEIPT_MISMATCH]")
    if witness.observed_at < prior.observed_at: raise ValueError("REFUSED[CAUSAL_TIME_INVERSION]")
