from pathlib import Path
import re
import unittest


CONTRACT = Path("contracts/challenger-value.yaml")
STRATEGY = Path("chatman-ecosystem-LINKEDIN-REVOPS-STRATEGY.md")
EXPECTED_SUBJECTS = {
    "ggen-marketplace": "b54ef5ad0d2eebf4c9bca05efcb77b05884cc29e",
    "tcps": "18977d274ff05a7c8b96f9f64c25120835c94e52",
}
STRATEGY_SUBJECT = "3676b63f1f8c686dfdb4e6846d8fd956bc94e5cc"


class ChallengerValueContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT.read_text(encoding="utf-8")
        cls.strategy = STRATEGY.read_text(encoding="utf-8")

    def test_claim_standing_cannot_be_upgraded_by_presentation(self) -> None:
        for law in (
            "canonical_evidence_is_not_mutated_by_tailoring: true",
            "observed_fact_may_not_be_manufactured: true",
            "inferred_claim_must_remain_labeled: true",
            "hypothesis_must_remain_labeled: true",
            "customer_outcome_requires_verified_evidence: true",
            "metric_requires_source: true",
            "alive_requires_standing_evidence: true",
            "proof_requires_exact_subject: true",
            "message_arc_does_not_satisfy_revenue_process: true",
        ):
            self.assertIn(law, self.text)

    def test_message_arc_and_revenue_process_are_separate(self) -> None:
        self.assertIn(
            "phases: [TEACH, REFRAME, RATIONAL_IMPACT, NEW_WAY, PROOF, TAKE_CONTROL]",
            self.text,
        )
        self.assertIn(
            "phases: [TEACH, TAILOR, TAKE_CONTROL, DIAGNOSE, QUANTIFY, PROVE]",
            self.text,
        )
        self.assertIn("scope: pre-engagement-evidence-presentation", self.text)
        self.assertIn("scope: engagement-to-customer-value", self.text)
        self.assertIn("PROOF: exact evidence used to support a commercial message", self.text)
        self.assertIn(
            "PROVE: customer-specific falsifiable enterprise proof after diagnosis and quantification",
            self.text,
        )
        self.assertIn("proof_evidence_kind: VERIFIED", self.text)
        self.assertIn("take_control_is_diagnostic_intent_only: true", self.text)

    def test_strategy_doctrine_is_exact_subject_bound_and_present(self) -> None:
        self.assertRegex(STRATEGY_SUBJECT, r"^[0-9a-f]{40}$")
        self.assertIn(f"commit: {STRATEGY_SUBJECT}", self.text)
        self.assertIn(f"strategy_subject: {STRATEGY_SUBJECT}", self.text)
        self.assertIn("document: chatman-ecosystem-LINKEDIN-REVOPS-STRATEGY.md", self.text)
        self.assertIn("Teach -> Tailor -> TakeControl -> Diagnose -> Quantify -> Prove", self.strategy)
        self.assertIn("10,000 commits alone proves enterprise value", self.strategy)

    def test_dfcm_preserves_frontier_and_zero_irreversible_selection(self) -> None:
        self.assertIn("enumerate_bounded_narrative_candidates: true", self.text)
        self.assertIn("candidate_bound: 4096", self.text)
        self.assertIn("preserve_nondominated_frontier: true", self.text)
        self.assertIn("irreversible_selections: 0", self.text)

    def test_no_commercial_actuation_authority(self) -> None:
        self.assertIn("SELECT: reversible-presentation", self.text)
        self.assertIn("CONSTRUCT: brief-only", self.text)
        self.assertIn("DO: none", self.text)
        self.assertIn("actuation: false", self.text)

    def test_receipt_and_replay_are_bound(self) -> None:
        self.assertIn("canonical_json_digest: sha256", self.text)
        self.assertIn("deterministic_replay_required: true", self.text)
        for part in ("protocol", "audience", "candidate_frontier", "recommendation", "brief", "authority"):
            self.assertIn(part, self.text)

    def test_exact_integration_subjects(self) -> None:
        for owner, head in EXPECTED_SUBJECTS.items():
            self.assertRegex(head, r"^[0-9a-f]{40}$")
            block = re.search(
                rf"^  {re.escape(owner)}:\n(?P<body>(?:    .*\n)+)",
                self.text,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(block, owner)
            self.assertIn(f"head: {head}", block.group("body"))

    def test_refusal_surface_names_high_risk_sales_claims(self) -> None:
        for refusal in (
            "UNSUPPORTED_CLAIM",
            "PROOF_WITHOUT_EXACT_SUBJECT",
            "METRIC_WITHOUT_SOURCE",
            "ALIVE_WITHOUT_STANDING",
            "OUTCOME_AS_FACT",
            "CANDIDATE_BOUND_EXCEEDED",
        ):
            self.assertIn(f"- {refusal}", self.text)


if __name__ == "__main__":
    unittest.main()
