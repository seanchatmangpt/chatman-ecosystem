from collections import defaultdict

def worst_stratum(rows):
    grouped = defaultdict(list)
    for name, failed in rows:
        grouped[name].append(bool(failed))
    if not grouped:
        return None, 0.0
    scored = [(sum(values) / len(values), name) for name, values in grouped.items()]
    rate, name = max(scored)
    return name, rate
