from collections import defaultdict
from fractions import Fraction


def group(observations):
    groups = defaultdict(list)
    for item in observations:
        key = (item.methodology, item.engine, item.region, item.evidence_root)
        groups[key].append(item)
    return {key: tuple(value) for key, value in sorted(groups.items())}


def false_safe_rate(items) -> Fraction:
    values = tuple(items)
    if not values:
        return Fraction(0,1)
    misses = sum(item.predicted_consequence_bound < item.realized_consequence for item in values)
    return Fraction(misses, len(values))


def worst_stratum(observations):
    groups = group(observations)
    if not groups:
        return None
    scored = [(false_safe_rate(items), key) for key, items in groups.items()]
    return max(scored, key=lambda pair: (pair[0], pair[1]))
