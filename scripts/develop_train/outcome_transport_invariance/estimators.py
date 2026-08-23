from .errors import Refused

def pairs(losses, weights):
    mapping = dict(weights.items)
    values = [(float(losses[k]), mapping[k]) for k in sorted(set(losses) & set(mapping))]
    if not values:
        raise Refused("NO_WEIGHTED_OUTCOMES")
    return values

def ht(losses, weights):
    values = pairs(losses, weights)
    return sum(loss * weight for loss, weight in values) / len(values)

def sn(losses, weights):
    values = pairs(losses, weights)
    total = sum(weight for _, weight in values)
    if total <= 0:
        raise Refused("ZERO_WEIGHT")
    return sum(loss * weight for loss, weight in values) / total

def gap(losses, weights):
    return abs(ht(losses, weights) - sn(losses, weights))
