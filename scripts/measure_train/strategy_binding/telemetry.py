def project(proof, policy, selected, frontier_digest):
    return ({"activity":"measure_strategy_binding","consumer_repo":proof.consumer.repo,"consumer_sha":proof.consumer.sha,
             "selected_cut_id":selected.cut_id,"cut_generation":selected.generation,"strategy":policy.strategy,
             "strategy_digest":policy.digest,"frontier_digest":frontier_digest,"proof_id":proof.proof_id},)
