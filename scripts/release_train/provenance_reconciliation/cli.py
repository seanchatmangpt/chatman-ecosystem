from __future__ import annotations

import json
import sys

from .authority import AuthorityContext
from .claims import EvidenceClaim
from .dependency import DependencyEdge
from .engine import manufacture
from .lineage import EvidenceEdge
from .model import ExactSubject, Refused
from .provenance import EvidenceRecord
from .window import ObservationWindow


def _subject(value: dict[str, str]) -> ExactSubject:
    return ExactSubject(value["repo"], value["sha"])


def run(payload: dict) -> dict:
    window = ObservationWindow(payload["window"]["start"], payload["window"]["end"])
    records = [EvidenceRecord(subject=_subject(item.pop("subject")), **item) for item in [dict(row) for row in payload["records"]]]
    claims = [EvidenceClaim(subject=_subject(item.pop("subject")), evidence_ids=tuple(item.pop("evidence_ids")), **item) for item in [dict(row) for row in payload["claims"]]]
    subjects = [_subject(item) for item in payload["subjects"]]
    dependencies = [DependencyEdge(_subject(item["upstream"]), _subject(item["downstream"])) for item in payload.get("dependencies", [])]
    evidence_edges = [EvidenceEdge(item["predecessor"], item["successor"]) for item in payload.get("evidence_edges", [])]
    result = manufacture(predecessor_sha=payload["predecessor_sha"], window=window, records=records, evidence_edges=evidence_edges, claims=claims, subjects=subjects, dependencies=dependencies, authority=AuthorityContext(payload.get("authority_owner", "schedule")))
    return {"standing": "PARTIAL_ALIVE", "ordered_subjects": result.ordered_subjects, "steps": [step.__dict__ for step in result.steps], "receipt": result.receipt.__dict__ | {"steps": [step.__dict__ for step in result.receipt.steps]}}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        print(json.dumps(run(payload), sort_keys=True, separators=(",", ":")))
        return 0
    except (KeyError, TypeError, Refused, ValueError) as exc:
        print(json.dumps({"standing": "BLOCKED", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
