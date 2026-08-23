import math

def entropy(probabilities):
    values=[p for p in probabilities if p>0]
    total=sum(values)
    if total <= 0:
        return 0.0
    return -sum((p/total)*math.log2(p/total) for p in values)

def realized_information_gain(before, after):
    return entropy(before)-entropy(after)
