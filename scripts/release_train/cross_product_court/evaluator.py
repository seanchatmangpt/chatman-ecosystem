from __future__ import annotations

from dataclasses import replace

from .model import (
    CrossProductCase,
    CrossProductReceipt,
    EvidenceResult,
    Formalism,
    Standing,
    canonical_digest,
    formalism_names,
)

_SCHEMA = "https://chatman.dev/cross-product-court/receipt/v1"
_CLAIM_CEILING = "COMPOSITIONAL_CORRESPONDENCE_ONLY"


def _index(case: CrossProductCase) -> dict[tuple[Formalism, str], list]:
    result: dict[tuple[Formalism, str], list] = {}
    for item in case.evidence:
        result.setdefault((item.formalism, item.claim_id), []).append(item)
    return result


def evaluate(case: CrossProductCase) -> CrossProductReceipt:
    refusals: list[str] = []
    evidence_ids = tuple(sorted(item.evidence_id for item in case.evidence))
    if len(evidence_ids) != len(set(evidence_ids)):
        refusals.append("REFUSED:DUPLICATE_EVIDENCE_ID")

    admitted_subjects = {
        item.repository: item.subject_sha
        for item in case.subjects
    }
    for item in case.evidence:
        expected_sha = admitted_subjects.get(item.repository)
        if expected_sha is None:
            refusals.append(
                f"REFUSED:UNBOUND_EVIDENCE_REPOSITORY:{item.repository}"
            )
        elif expected_sha != item.subject_sha:
            refusals.append(
                f"REFUSED:SUBJECT_IDENTITY_SPLIT:{item.repository}:"
                f"expected={expected_sha}:observed={item.subject_sha}"
            )

    valid_evidence = tuple(
        item
        for item in case.evidence
        if admitted_subjects.get(item.repository) == item.subject_sha
    )
    present = {item.formalism for item in valid_evidence}
    missing = tuple(
        sorted(f.value for f in set(case.required_formalisms) - present)
    )
    if missing:
        refusals.append("BLOCKED:MISSING_DIMENSION:" + ",".join(missing))

    index = _index(case)
    checked_relations: list[str] = []
    for relation in case.relations:
        left = index.get((relation.left, relation.claim_id), [])
        right = index.get((relation.right, relation.claim_id), [])
        if not left or not right:
            refusals.append(
                f"BLOCKED:RELATION_EVIDENCE_MISSING:{relation.relation_id}"
            )
            continue
        if any(
            admitted_subjects.get(item.repository) != item.subject_sha
            for item in left + right
        ):
            refusals.append(
                f"REFUSED:RELATION_SUBJECT_SPLIT:{relation.relation_id}"
            )
            continue
        if any(item.result is not EvidenceResult.PASS for item in left + right):
            refusals.append(
                f"REFUSED:RELATION_NOT_PASS:{relation.relation_id}"
            )
            continue
        checked_relations.append(relation.relation_id)

    checked_mutants: list[str] = []
    for mutant in case.mutants:
        matches = index.get((mutant.formalism, mutant.claim_id), [])
        if not matches:
            refusals.append(
                f"BLOCKED:MUTANT_EVIDENCE_MISSING:{mutant.mutant_id}"
            )
            continue
        if len(matches) != 1:
            refusals.append(
                f"REFUSED:MUTANT_EVIDENCE_AMBIGUOUS:{mutant.mutant_id}"
            )
            continue
        if admitted_subjects.get(matches[0].repository) != matches[0].subject_sha:
            refusals.append(
                f"REFUSED:MUTANT_SUBJECT_SPLIT:{mutant.mutant_id}"
            )
            continue
        observed = matches[0].result
        if observed is not mutant.expected:
            refusals.append(
                f"REFUSED:MUTANT_SURVIVED:{mutant.mutant_id}:"
                f"expected={mutant.expected.value}:observed={observed.value}"
            )
            continue
        checked_mutants.append(mutant.mutant_id)

    hard_refusal = any(item.startswith("REFUSED:") for item in refusals)
    blocked = any(item.startswith("BLOCKED:") for item in refusals)
    if hard_refusal:
        standing = Standing.REFUSED
    elif blocked:
        standing = Standing.BLOCKED
    elif (
        len(checked_relations) != len(case.relations)
        or len(checked_mutants) != len(case.mutants)
    ):
        standing = Standing.PARTIAL_ALIVE
    else:
        standing = Standing.ALIVE

    receipt = CrossProductReceipt(
        schema=_SCHEMA,
        case_id=case.case_id,
        semantic_subject_id=case.semantic_subject_id,
        subject_bindings=tuple(sorted(item.identity for item in case.subjects)),
        standing=standing,
        claim_ceiling=_CLAIM_CEILING,
        authority="NONE",
        dimensions_present=formalism_names(present),
        relations_checked=tuple(sorted(checked_relations)),
        mutants_checked=tuple(sorted(checked_mutants)),
        refusals=tuple(sorted(set(refusals))),
        evidence_ids=evidence_ids,
        receipt_digest="sha256:" + "0" * 64,
    )
    return replace(
        receipt,
        receipt_digest=canonical_digest(receipt.canonical_payload()),
    )
