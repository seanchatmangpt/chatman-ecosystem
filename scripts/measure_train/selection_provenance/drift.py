def classify_drift(selection, frontier):
    if selection.strategy.name != frontier.strategy.name:
        return "STRATEGY_DRIFT"
    if selection.strategy.policy_digest != frontier.strategy.policy_digest:
        return "POLICY_DRIFT"
    if selection.strategy.fingerprint != frontier.strategy.fingerprint:
        return "PARAMETER_DRIFT"
    if tuple(sorted(selection.candidate_ids)) != tuple(sorted(frontier.current_candidate_ids)):
        return "CANDIDATE_FRONTIER_DRIFT"
    if selection.selected_cut_id != frontier.current_selected_cut_id:
        return "SELECTED_CUT_DRIFT"
    return "CURRENT"
