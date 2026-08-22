from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from .model import Refused
from .plan import PlanStep

SCHEMA = "chatman.provenance-promotion/1"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


@dataclass(frozen=True)
class PromotionReceipt:
    schema: str
    predecessor_sha: str
    subjects: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    steps: tuple[PlanStep, ...]
    digest_sha256: str


def manufacture_receipt(predecessor_sha: str, subjects: list[str], evidence_ids: list[str], steps: tuple[PlanStep, ...]) -> PromotionReceipt:
    core = {
        "schema": SCHEMA,
        "predecessor_sha": predecessor_sha,
        "subjects": sorted(subjects),
        "evidence_ids": sorted(evidence_ids),
        "steps": [asdict(step) for step in steps],
    }
    digest = hashlib.sha256(canonical(core)).hexdigest()
    return PromotionReceipt(SCHEMA, predecessor_sha, tuple(core["subjects"]), tuple(core["evidence_ids"]), steps, digest)


def replay(receipt: PromotionReceipt) -> None:
    if receipt.schema != SCHEMA:
        raise Refused("RECEIPT_SCHEMA_DRIFT", receipt.schema)
    expected = manufacture_receipt(receipt.predecessor_sha, list(receipt.subjects), list(receipt.evidence_ids), receipt.steps)
    if expected.digest_sha256 != receipt.digest_sha256:
        raise Refused("RECEIPT_TAMPERED")
