from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .evaluator import evaluate
from .model import (
    CrossProductCase,
    EvidenceRecord,
    EvidenceResult,
    Formalism,
    MutantExpectation,
    RelationRequirement,
    SubjectBinding,
)


def load_case(path: str | Path) -> CrossProductCase:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    subjects = tuple(
        SubjectBinding(
            repository=item["repository"],
            subject_sha=item["subject_sha"],
        )
        for item in raw["subjects"]
    )
    evidence = tuple(
        EvidenceRecord(
            evidence_id=item["evidence_id"],
            repository=item["repository"],
            subject_sha=item["subject_sha"],
            formalism=Formalism(item["formalism"]),
            claim_id=item["claim_id"],
            artifact_digest=item["artifact_digest"],
            validator=item["validator"],
            validator_digest=item["validator_digest"],
            result=EvidenceResult(item["result"]),
            authority=item.get("authority", "NONE"),
            counterexample_digest=item.get("counterexample_digest"),
        )
        for item in raw["evidence"]
    )
    relations = tuple(
        RelationRequirement(
            relation_id=item["relation_id"],
            left=Formalism(item["left"]),
            right=Formalism(item["right"]),
            claim_id=item["claim_id"],
        )
        for item in raw.get("relations", [])
    )
    mutants = tuple(
        MutantExpectation(
            mutant_id=item["mutant_id"],
            formalism=Formalism(item["formalism"]),
            claim_id=item["claim_id"],
            expected=EvidenceResult(item["expected"]),
        )
        for item in raw.get("mutants", [])
    )
    return CrossProductCase(
        case_id=raw["case_id"],
        semantic_subject_id=raw["semantic_subject_id"],
        subjects=subjects,
        required_formalisms=tuple(
            Formalism(value)
            for value in raw["required_formalisms"]
        ),
        evidence=evidence,
        relations=relations,
        mutants=mutants,
    )


def receipt_dict(case: CrossProductCase) -> dict[str, Any]:
    receipt = evaluate(case)
    data = asdict(receipt)
    data["standing"] = receipt.standing.value
    return data


def write_receipt(
    case_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    data = receipt_dict(load_case(case_path))
    Path(output_path).write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return data
