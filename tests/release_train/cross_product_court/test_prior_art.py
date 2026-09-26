from __future__ import annotations

import unittest

from scripts.release_train.cross_product_court.prior_art import (
    PriorArtCandidate,
    PriorArtDecision,
    PriorArtDecisionCase,
    evaluate_prior_art,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64


def candidate(
    candidate_id: str,
    sha: str,
    covers: tuple[str, ...],
    *,
    gap: str | None = D3,
) -> PriorArtCandidate:
    return PriorArtCandidate(
        candidate_id=candidate_id,
        exact_subject=f"seanchatmangpt/{candidate_id}@{sha * 40}",
        semantic_contract_digest=D1,
        qualification_receipt_digest=D2,
        covers=covers,
        gap_falsifier_digest=gap,
    )


class PriorArtDecisionCourtTests(unittest.TestCase):
    def test_reuse_beats_every_other_disposition(self) -> None:
        case = PriorArtDecisionCase(
            case_id="reuse",
            required_semantics=("a", "b"),
            candidates=(
                candidate("partial", "a", ("a",)),
                candidate("complete", "b", ("a", "b")),
            ),
        )
        receipt = evaluate_prior_art(case)
        self.assertEqual(receipt.decision, PriorArtDecision.REUSE)
        self.assertEqual(receipt.selected_candidate_ids, ("complete",))
        self.assertEqual(receipt.residual_semantics, ())
        self.assertEqual(receipt.authority, "NONE")

    def test_compose_selects_minimal_deterministic_cover(self) -> None:
        case = PriorArtDecisionCase(
            case_id="compose",
            required_semantics=("a", "b", "c"),
            candidates=(
                candidate("alpha", "a", ("a", "b")),
                candidate("beta", "b", ("c",)),
                candidate("gamma", "c", ("b", "c")),
            ),
        )
        receipt = evaluate_prior_art(case)
        self.assertEqual(receipt.decision, PriorArtDecision.COMPOSE)
        self.assertEqual(receipt.selected_candidate_ids, ("alpha", "beta"))

    def test_extend_requires_residual_falsifier(self) -> None:
        base = dict(
            case_id="extend",
            required_semantics=("a", "b"),
            candidates=(candidate("alpha", "a", ("a",)),),
        )
        refused = evaluate_prior_art(PriorArtDecisionCase(**base))
        self.assertEqual(refused.decision, PriorArtDecision.REFUSED)
        self.assertIn("REFUSED:EXTEND_RESIDUAL_UNFALSIFIED", refused.refusals)

        admitted = evaluate_prior_art(
            PriorArtDecisionCase(**base, residual_falsifier_digest=D4)
        )
        self.assertEqual(admitted.decision, PriorArtDecision.EXTEND)
        self.assertEqual(admitted.covered_semantics, ("a",))
        self.assertEqual(admitted.residual_semantics, ("b",))
        self.assertEqual(admitted.falsifier_digest, D4)

    def test_invent_requires_every_prior_art_gap_to_be_falsified(self) -> None:
        missing_gap = PriorArtDecisionCase(
            case_id="invent-refused",
            required_semantics=("x",),
            candidates=(candidate("alpha", "a", ("a",), gap=None),),
            residual_falsifier_digest=D4,
        )
        refused = evaluate_prior_art(missing_gap)
        self.assertEqual(refused.decision, PriorArtDecision.REFUSED)
        self.assertIn(
            "REFUSED:INVENT_WITHOUT_PRIOR_ART_FALSIFIER",
            refused.refusals,
        )

        admitted = evaluate_prior_art(
            PriorArtDecisionCase(
                case_id="invent",
                required_semantics=("x",),
                candidates=(candidate("alpha", "a", ("a",), gap=D3),),
                residual_falsifier_digest=D4,
            )
        )
        self.assertEqual(admitted.decision, PriorArtDecision.INVENT)
        self.assertEqual(admitted.selected_candidate_ids, ())
        self.assertEqual(admitted.residual_semantics, ("x",))

    def test_no_prior_art_search_is_refused_not_called_novel(self) -> None:
        receipt = evaluate_prior_art(
            PriorArtDecisionCase(
                case_id="no-search",
                required_semantics=("x",),
                candidates=(),
                residual_falsifier_digest=D4,
            )
        )
        self.assertEqual(receipt.decision, PriorArtDecision.REFUSED)
        self.assertIn("REFUSED:PRIOR_ART_SEARCH_MISSING", receipt.refusals)

    def test_receipt_is_deterministic(self) -> None:
        case = PriorArtDecisionCase(
            case_id="deterministic",
            required_semantics=("a", "b"),
            candidates=(
                candidate("beta", "b", ("b",)),
                candidate("alpha", "a", ("a",)),
            ),
        )
        self.assertEqual(
            evaluate_prior_art(case).receipt_digest,
            evaluate_prior_art(case).receipt_digest,
        )


if __name__ == "__main__":
    unittest.main()
