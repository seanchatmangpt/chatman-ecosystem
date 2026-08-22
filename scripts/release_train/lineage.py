from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

class LineageRefusal(ValueError):
    pass

@dataclass(frozen=True)
class Predecessor:
    key: str
    pr_url: str
    state: str
    head: Subject
    base_repo: str
    base_sha: str
    contained: bool = False

def admit_predecessor(expected_key: str, predecessor: Predecessor | None) -> str:
    if predecessor is None:
        return "LINEAGE_ROOT"
    if predecessor.key != expected_key:
        raise LineageRefusal("REFUSED[FOREIGN_SCHEDULE_LINEAGE]")
    if predecessor.state == "open":
        return predecessor.head.sha
    if predecessor.state == "merged" and predecessor.contained:
        return predecessor.head.sha
    if predecessor.state == "merged":
        raise LineageRefusal("BLOCKED[SCHEDULE_PR_LINEAGE_NOT_CONTAINED]")
    raise LineageRefusal("BLOCKED[SCHEDULE_PR_LINEAGE]")
