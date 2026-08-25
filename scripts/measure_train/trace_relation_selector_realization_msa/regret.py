from dataclasses import dataclass
from .alternatives import require_observed_counterfactual

@dataclass(frozen=True)
class Regret:
    chosen_loss: int
    best_observed_loss: int
    regret: int
    observed_relations: tuple

def observed_only_regret(decision, realizations, loss_fn):
    observed=tuple(sorted({r.relation for r in realizations}))
    losses={}
    for relation in decision.candidates:
        if relation in observed:
            rows=[r for r in realizations if r.relation==relation]
            losses[relation]=loss_fn(relation,rows)
    for chosen in decision.chosen:
        require_observed_counterfactual(chosen,observed)
    chosen_loss=min(losses[r] for r in decision.chosen)
    best=min(losses.values())
    return Regret(chosen_loss,best,chosen_loss-best,observed)
