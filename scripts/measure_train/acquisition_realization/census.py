from collections import defaultdict
from statistics import mean

def policy_census(rows):
    grouped=defaultdict(list)
    for strategy, realization, brier, efficiency, regret in rows:
        grouped[strategy].append((realization,brier,efficiency,regret))
    out=[]
    for strategy, vals in sorted(grouped.items()):
        out.append({
            "strategy":strategy,
            "support":len(vals),
            "mean_realized_gain":mean(v[0].realized_gain for v in vals),
            "mean_abs_gain_error":mean(abs(v[0].gain_error) for v in vals),
            "mean_brier":float(mean(float(v[1]) for v in vals)),
            "mean_gain_per_cost":mean(v[2].gain_per_cost for v in vals),
            "mean_regret":mean(v[3] for v in vals),
        })
    return tuple(out)
