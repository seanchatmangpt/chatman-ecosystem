from pathlib import Path
import unittest


CONTRACT = Path("contracts/dfcm-dd-ui.yaml")


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
        self.assertIn("reject_digest_mismatch: true", self.text)
        self.assertIn("reject_unprojected_action: true", self.text)

    def test_ownership_boundaries_are_explicit(self) -> None:
        for owner in ("ggen-marketplace", "gymact", "castle", "wasm4pm"):
            self.assertIn(f"  {owner}:", self.text)


if __name__ == "__main__":
    unittest.main()
