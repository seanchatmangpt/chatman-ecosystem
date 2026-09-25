from __future__ import annotations

import unittest

from scripts.release_train.cross_product_court import (
    CrossProductCase,
    EvidenceRecord,
    EvidenceResult,
    Formalism,
    MutantExpectation,
    RelationRequirement,
    Standing,
    SubjectBinding,
    evaluate,
)

SUBJECTS = {
    "seanchatmangpt/autofde-lab": "a" * 40,
    "seanchatmangpt/ash_a2a": "b" * 40,
    "seanchatmangpt/gymact": "c" * 40,
    "seanchatmangpt/wasm4pm": "d" * 40,
    "seanchatmangpt/affidavit": "e" * 40,
}
DIGEST = "sha256:" + "1" * 64
VALIDATOR = "sha256:" + "2" * 64
CE = "sha256:" + "3" * 64


def ev(
    repo: str,
    formalism: Formalism,
    claim: str,
    *,
    result: EvidenceResult = EvidenceResult.PASS,
    suffix: str = "",
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=f"{formalism.value}:{claim}:{repo}:{suffix or result.value}",
        repository=repo,
        subject_sha=SUBJECTS[repo],
        formalism=formalism,
        claim_id=claim,
        artifact_digest=DIGEST,
        validator=f"validator-{formalism.value}",
        validator_digest=VALIDATOR,
        result=result,
        counterexample_digest=(
            CE if result is EvidenceResult.COUNTEREXAMPLE else None
        ),
    )


def healthy_case() -> CrossProductCase:
    evidence = (
        ev(
            "seanchatmangpt/ash_a2a",
            Formalism.HDDL,
            "authority-conservation",
        ),
        ev(
            "seanchatmangpt/autofde-lab",
            Formalism.FOND,
            "authority-conservation",
        ),
        ev(
            "seanchatmangpt/autofde-lab",
            Formalism.TLA,
            "authority-conservation",
        ),
        ev(
            "seanchatmangpt/wasm4pm",
            Formalism.POWL,
            "execution-conformance",
        ),
        ev(
            "seanchatmangpt/gymact",
            Formalism.OCEL,
            "execution-conformance",
        ),
        ev(
            "seanchatmangpt/ash_a2a",
            Formalism.BRCE,
            "receipted-do",
        ),
        ev(
            "seanchatmangpt/affidavit",
            Formalism.RECEIPT,
            "receipted-do",
        ),
        ev(
            "seanchatmangpt/autofde-lab",
            Formalism.TLA,
            "mutant-double-writer",
            result=EvidenceResult.COUNTEREXAMPLE,
            suffix="mutant",
        ),
    )
    return CrossProductCase(
        case_id="XPROD-001",
        semantic_subject_id="urn:chatman:xprod:orthogonal-swarm:001",
        subjects=tuple(
            SubjectBinding(repo, sha)
            for repo, sha in SUBJECTS.items()
        ),
        required_formalisms=(
            Formalism.HDDL,
            Formalism.FOND,
            Formalism.TLA,
            Formalism.POWL,
            Formalism.OCEL,
            Formalism.BRCE,
            Formalism.RECEIPT,
        ),
        evidence=evidence,
        relations=(
            RelationRequirement(
                "HDDLxTLA",
                Formalism.HDDL,
                Formalism.TLA,
                "authority-conservation",
            ),
            RelationRequirement(
                "FONDxTLA",
                Formalism.FOND,
                Formalism.TLA,
                "authority-conservation",
            ),
            RelationRequirement(
                "OCELxPOWL",
                Formalism.OCEL,
                Formalism.POWL,
                "execution-conformance",
            ),
            RelationRequirement(
                "BRCExReceipt",
                Formalism.BRCE,
                Formalism.RECEIPT,
                "receipted-do",
            ),
        ),
        mutants=(
            MutantExpectation(
                "double-writer",
                Formalism.TLA,
                "mutant-double-writer",
                EvidenceResult.COUNTEREXAMPLE,
            ),
        ),
    )


class CrossProductCourtTests(unittest.TestCase):
    def test_complete_cross_repo_case_is_alive_but_has_zero_authority(
        self,
    ) -> None:
        receipt = evaluate(healthy_case())
        self.assertEqual(receipt.standing, Standing.ALIVE)
        self.assertEqual(receipt.authority, "NONE")
        self.assertEqual(
            receipt.claim_ceiling,
            "COMPOSITIONAL_CORRESPONDENCE_ONLY",
        )
        self.assertEqual(len(receipt.subject_bindings), len(SUBJECTS))
        self.assertEqual(len(receipt.relations_checked), 4)
        self.assertEqual(receipt.mutants_checked, ("double-writer",))

    def test_receipt_is_deterministic(self) -> None:
        first = evaluate(healthy_case())
        second = evaluate(healthy_case())
        self.assertEqual(first.receipt_digest, second.receipt_digest)

    def test_missing_dimension_blocks_without_inventing_evidence(self) -> None:
        case = healthy_case()
        evidence = tuple(
            x for x in case.evidence
            if x.formalism is not Formalism.POWL
        )
        receipt = evaluate(
            CrossProductCase(
                case.case_id,
                case.semantic_subject_id,
                case.subjects,
                case.required_formalisms,
                evidence,
                case.relations,
                case.mutants,
            )
        )
        self.assertEqual(receipt.standing, Standing.BLOCKED)
        self.assertIn(
            "BLOCKED:MISSING_DIMENSION:POWL",
            receipt.refusals,
        )
        self.assertIn(
            "BLOCKED:RELATION_EVIDENCE_MISSING:OCELxPOWL",
            receipt.refusals,
        )

    def test_per_repo_subject_identity_split_is_refused(self) -> None:
        case = healthy_case()
        bad = EvidenceRecord(
            evidence_id="split",
            repository="seanchatmangpt/gymact",
            subject_sha="f" * 40,
            formalism=Formalism.OCEL,
            claim_id="execution-conformance",
            artifact_digest=DIGEST,
            validator="ocel-validator",
            validator_digest=VALIDATOR,
            result=EvidenceResult.PASS,
        )
        receipt = evaluate(
            CrossProductCase(
                case.case_id,
                case.semantic_subject_id,
                case.subjects,
                case.required_formalisms,
                case.evidence + (bad,),
                case.relations,
                case.mutants,
            )
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertTrue(
            any(
                x.startswith(
                    "REFUSED:SUBJECT_IDENTITY_SPLIT:"
                    "seanchatmangpt/gymact"
                )
                for x in receipt.refusals
            )
        )

    def test_unbound_repository_is_refused(self) -> None:
        case = healthy_case()
        rogue = EvidenceRecord(
            evidence_id="rogue",
            repository="seanchatmangpt/rogue",
            subject_sha="9" * 40,
            formalism=Formalism.OCEL,
            claim_id="execution-conformance",
            artifact_digest=DIGEST,
            validator="rogue-validator",
            validator_digest=VALIDATOR,
            result=EvidenceResult.PASS,
        )
        receipt = evaluate(
            CrossProductCase(
                case.case_id,
                case.semantic_subject_id,
                case.subjects,
                case.required_formalisms,
                case.evidence + (rogue,),
                case.relations,
                case.mutants,
            )
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertIn(
            "REFUSED:UNBOUND_EVIDENCE_REPOSITORY:"
            "seanchatmangpt/rogue",
            receipt.refusals,
        )

    def test_projection_cannot_smuggle_authority(self) -> None:
        with self.assertRaisesRegex(ValueError, "carry no authority"):
            EvidenceRecord(
                evidence_id="bad-authority",
                repository="seanchatmangpt/autofde-lab",
                subject_sha=SUBJECTS["seanchatmangpt/autofde-lab"],
                formalism=Formalism.TLA,
                claim_id="authority-conservation",
                artifact_digest=DIGEST,
                validator="tlc",
                validator_digest=VALIDATOR,
                result=EvidenceResult.PASS,
                authority="DO",
            )

    def test_mutant_that_passes_is_refused(self) -> None:
        case = healthy_case()
        evidence = tuple(
            ev(
                "seanchatmangpt/autofde-lab",
                Formalism.TLA,
                "mutant-double-writer",
                result=EvidenceResult.PASS,
                suffix="survived",
            )
            if item.claim_id == "mutant-double-writer"
            else item
            for item in case.evidence
        )
        receipt = evaluate(
            CrossProductCase(
                case.case_id,
                case.semantic_subject_id,
                case.subjects,
                case.required_formalisms,
                evidence,
                case.relations,
                case.mutants,
            )
        )
        self.assertEqual(receipt.standing, Standing.REFUSED)
        self.assertTrue(
            any(
                x.startswith(
                    "REFUSED:MUTANT_SURVIVED:double-writer"
                )
                for x in receipt.refusals
            )
        )


if __name__ == "__main__":
    unittest.main()
