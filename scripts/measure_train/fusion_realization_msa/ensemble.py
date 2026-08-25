from .probability import aligned
from .entropy import shannon_bits
def barycenter(distributions):
    rows=aligned(distributions); n=len(rows)
    return tuple(sum(row[i] for row in rows)/n for i in range(len(rows[0])))
def generalized_js(distributions):
    rows=aligned(distributions); center=barycenter(rows)
    return shannon_bits(center)-sum(shannon_bits(r) for r in rows)/len(rows)
