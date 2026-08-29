from __future__ import annotations

from dataclasses import dataclass

from .model import ExactSubject, Refused
from .provenance import EvidenceRecord


@dataclass(frozen=True)
class ReconciledEvidence:
    repo: str
    current_subject: ExactSubject
    current_ids: tuple[str, ...]
    superseded_ids: tuple[str, ...]


def reconcile_repo(records: list[EvidenceRecord]) -> ReconciledEvidence:
    if not records:
        raise Refused("EMPTY_RECONCILIATION")
    repos = {record.subject.repo for record in records}
    if len(repos) != 1:
        raise Refused("CROSS_REPO_RECONCILIATION")
    by_sha: dict[str, list[EvidenceRecord]] = {}
    for record in records:
        by_sha.setdefault(record.subject.sha, []).append(record)
    newest_time = max(record.observed_at for record in records)
    newest = [record for record in records if record.observed_at == newest_time]
    newest_shas = {record.subject.sha for record in newest}
    if len(newest_shas) != 1:
        raise Refused("CONFLICTING_CURRENT_SUBJECT", ",".join(sorted(newest_shas)))
    current_sha = next(iter(newest_shas))
    current = ExactSubject(next(iter(repos)), current_sha)
    current_ids = tuple(sorted(record.evidence_id for record in by_sha[current_sha]))
    superseded = tuple(sorted(record.evidence_id for sha, items in by_sha.items() if sha != current_sha for record in items))
    return ReconciledEvidence(current.repo, current, current_ids, superseded)
