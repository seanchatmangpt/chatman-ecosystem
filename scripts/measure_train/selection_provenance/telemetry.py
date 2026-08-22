def project(selection, selected_candidate, drift_state, standing_value):
    return ({
        "activity": "measure_cut_selection",
        "consumer_repo": selection.consumer.repo,
        "consumer_sha": selection.consumer.sha,
        "selector_id": selection.selector_id,
        "strategy": selection.strategy.name,
        "strategy_fingerprint": selection.strategy.fingerprint,
        "candidate_set_digest": selection.candidate_set_digest,
        "selected_cut_id": selected_candidate.cut_id,
        "selected_generation": selected_candidate.generation,
        "selector_receipt": selection.selector_receipt,
        "drift": drift_state,
        "standing": standing_value,
        "time": selection.observed_at.isoformat(),
    },)
