from dataclasses import dataclass
@dataclass(frozen=True)
class EpistemicCapital:
    nominal:int; generalized_n:float; cluster_n:float; effective_n:float; duplication_ratio:float
def capitalize(eff,groups):
    cn=float(len(groups)); en=min(eff.generalized,cn); dup=1.0-en/max(1,eff.nominal)
    return EpistemicCapital(eff.nominal,eff.generalized,cn,en,dup)
