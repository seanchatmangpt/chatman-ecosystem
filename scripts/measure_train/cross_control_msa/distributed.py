from .refusal import Refused
def admit_distributed(lease_valid,frontier,effective_quorum,threshold,circuit_state,replay_root):
 if not lease_valid: raise Refused("REFUSED[STALE_DISTRIBUTED_LEASE]")
 if frontier not in {"equal","before","after","concurrent"}: raise Refused("REFUSED[INVALID_CAUSAL_FRONTIER]")
 if effective_quorum<threshold: raise Refused("REFUSED[INSUFFICIENT_EFFECTIVE_QUORUM]")
 if circuit_state=="open": raise Refused("REFUSED[OPEN_CIRCUIT]")
 if len(replay_root)!=64: raise Refused("REFUSED[INVALID_REPLAY_ROOT]")
 return True
