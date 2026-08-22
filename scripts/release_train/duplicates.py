from __future__ import annotations
from collections import defaultdict
from typing import Iterable
from .evidence import Evidence

class DuplicateRefusal(ValueError):
    pass

def reconcile(rows: Iterable[Evidence]) -> tuple[Evidence, ...]:
    groups: dict[tuple[str, str, str], list[Evidence]] = defaultdict(list)
    for row in rows:
        groups[(row.key, row.subject.repo, row.subject.sha)].append(row)
    admitted: list[Evidence] = []
    for _, group in sorted(groups.items()):
        signatures = {(r.status, r.source, r.observed_at) for r in group}
        if len(signatures) > 1:
            raise DuplicateRefusal("REFUSED[CONFLICTING_DUPLICATE_EVIDENCE]")
        admitted.append(sorted(group)[0])
    return tuple(sorted(admitted))
