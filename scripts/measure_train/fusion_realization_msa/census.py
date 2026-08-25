def deterministic_census(realization,budget,calibration,cusum,shapley,submodularity_ratio_value,regret):
    rows=(
      ("predicted_gain_bits",round(realization.predicted_bits,12)),("realized_gain_bits",round(realization.realized_bits,12)),
      ("gain_error_bits",round(realization.error_bits,12)),("cost",round(budget.total_cost,12)),("latency_ms",budget.max_latency_ms),
      ("within_budget",budget.within_budget),("calibration",calibration.status),("drifted",cusum.drifted),
      ("submodularity_ratio",round(submodularity_ratio_value,12)),("observed_regret",round(regret,12)),
      ("shapley",tuple((k,round(v,12)) for k,v in shapley)),
    )
    return tuple(rows)
