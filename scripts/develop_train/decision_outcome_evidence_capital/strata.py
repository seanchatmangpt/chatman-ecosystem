from collections import defaultdict

def key(o):
    return (o.methodology, o.engine, o.region, o.evidence_root)

def group(observations):
    out = defaultdict(list)
    for o in observations:
        out[key(o)].append(o)
    return {k: tuple(v) for k, v in sorted(out.items())}

def worst_stratum(risks):
    if not risks:
        return None
    return max(risks.items(), key=lambda kv: (kv[1], kv[0]))
