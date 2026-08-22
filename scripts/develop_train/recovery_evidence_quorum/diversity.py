from __future__ import annotations

from fractions import Fraction


def effective_source_diversity(clusters: tuple[tuple[str, ...], ...]) -> Fraction:
    counts = [len(cluster) for cluster in clusters if cluster]
    if not counts:
        return Fraction(0, 1)
    total = sum(counts)
    return Fraction(total * total, sum(count * count for count in counts))
