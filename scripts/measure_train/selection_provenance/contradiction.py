def contradictions(selections):
    grouped = {}
    for item in selections:
        key = (item.consumer, item.selector_id, item.observed_at, item.strategy.fingerprint)
        grouped.setdefault(key, set()).add((item.selected_cut_id, item.selector_receipt))
    return tuple(sorted(
        (key[0].repo, key[0].sha, key[1], key[2].isoformat(), tuple(sorted(values)))
        for key, values in grouped.items()
        if len(values) > 1
    ))
