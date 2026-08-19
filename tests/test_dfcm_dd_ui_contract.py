from pathlib import Path
import re
import unittest


CONTRACT = Path("contracts/dfcm-dd-ui.yaml")
EXPECTED_SUBJECTS = {
    "wasm4pm": "8d48e784a4215857c8428c09bb09a91c05a8be97",
    "ggen-marketplace": "67a47966bc0c391cef06251b0d0f52f65e13c363",
    "gymact": "09d98f94c7d690f54853369cf680775d9e8f2dc3",
    "castle": "14d549069019cec78746cd4df41ece4f3dd379e1",
}


class DfcmDdUiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT.read_text(encoding="utf-8")

    def test_zero_irreversible_selection(self) -> None:
        self.assertIn("irreversible_ui_selections: 0", self.text)

    def test_rendering_has_no_actuation_authority(self) -> None:
        self.assertIn("rendering_actuation_authority: false", self.text)
        self.assertIn("runtime_ai_render_authority: false", self.text)

    def test_select_construct_do_are_separate(self) -> None:
        self.assertIn("SELECT: reversible-presentation", self.text)
        self.assertIn("CONSTRUCT: explicit-admission", self.text)
        self.assertIn("DO: BRCE-only", self.text)

    def test_receipts_bind_replay_context(self) -> None:
        for value in ("grammar", "world", "input", "presentation_frontier", "screen"):
            self.assertIn(value, self.text)
        self.assertIn("integration_subjects_bound: true", self.text)
        self.assertIn("reject_digest_mismatch: true", self.text)
        self.assertIn("reject_unprojected_action: true", self.text)

    def test_ownership_boundaries_are_explicit(self) -> None:
        for owner in EXPECTED_SUBJECTS:
            self.assertIn(f"  {owner}:", self.text)

    def test_every_integration_subject_is_exact_sha_bound(self) -> None:
        for owner, head in EXPECTED_SUBJECTS.items():
            self.assertRegex(head, r"^[0-9a-f]{40}$")
            block = re.search(
                rf"^  {re.escape(owner)}:\n(?P<body>(?:    .*\n)+)",
                self.text,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(block, owner)
            self.assertIn(f"head: {head}", block.group("body"))


if __name__ == "__main__":
    unittest.main()
