"""U-07 semantic mutants: every mutant killed, and the harness itself can report a survivor."""

from __future__ import annotations

import unittest

from _autonomic_support import committed_inputs

from scripts.release_train.autonomic_crown import mutants


class MutantsTest(unittest.TestCase):
    def setUp(self):
        self.inputs = committed_inputs(self)

    def test_every_mutant_is_killed_against_a_clean_control(self):
        report = mutants.run(self.inputs)
        self.assertEqual(report["survivors"], [], report)
        self.assertEqual(report["killed"], report["total"])
        self.assertGreaterEqual(report["total"], 20)
        for name, row in report["mutants"].items():
            with self.subTest(mutant=name):
                self.assertTrue(row["emitted"])
                self.assertFalse(row["control_emitted"])

    def test_a_mutant_the_court_cannot_see_survives(self):
        """Anti-vacuity of the harness: a no-op mutation is reported as a survivor."""
        blind = mutants.Mutant("noop", "EDGE_MALFORMED", lambda i: i)
        report = mutants.run(self.inputs, (blind,))
        self.assertEqual(report["survivors"], ["noop"])

    def test_an_expected_code_already_on_the_control_is_not_a_kill(self):
        """U-04 is already blocked on the committed inventory: re-emitting it proves nothing."""
        leak = mutants.Mutant("leak", "EVIDENCE_NOT_EXACT", lambda i: i)
        row = mutants.run(self.inputs, (leak,))["mutants"]["leak"]
        self.assertTrue(row["control_emitted"])
        self.assertFalse(row["killed"])

    def test_a_crashing_build_is_a_typed_survivor(self):
        def boom(_):
            raise KeyError("no such edge")

        report = mutants.run(self.inputs, (mutants.Mutant("crash", "EDGE_MALFORMED", boom),))
        self.assertIn("SURVIVED: court raised KeyError", report["mutants"]["crash"]["detail"])
        self.assertEqual(report["survivors"], ["crash"])


if __name__ == "__main__":
    unittest.main()
