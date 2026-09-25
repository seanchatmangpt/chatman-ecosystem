"""The committed release/v26.9.25 tree: projection current, graph admitted, crown test green."""

from __future__ import annotations

import unittest

from _support import REPO, RELEASE, load

from scripts.release_train.release_closure_court.court import evaluate as closure_evaluate
from scripts.release_train.root_crown import evidence, projector
from scripts.release_train.root_crown.requirements import validate_requirements

RELEASE_DIR = REPO / "release" / RELEASE


@unittest.skipUnless((RELEASE_DIR / "requirements.json").is_file(), "release/v26.9.25 not committed")
class CommittedReleaseTest(unittest.TestCase):
    def test_projection_is_current(self):
        self.assertEqual(projector.check(RELEASE_DIR), [])

    def test_requirements_admitted(self):
        inputs = projector.load_inputs(RELEASE_DIR)
        self.assertEqual(
            validate_requirements(inputs.requirements_doc, inputs.pins, inputs.rfc_text, evidence.EVALUATORS), []
        )

    def test_import_is_byte_identical_to_its_declared_digest(self):
        entry = load(RELEASE_DIR / "imports/IMPORTS.json")["imports"][0]
        self.assertEqual(evidence.sha256_bytes((RELEASE_DIR / entry["path"]).read_bytes()), entry["sha256"])

    def test_closure_is_terminal_not_refused(self):
        verdict = closure_evaluate(load(RELEASE_DIR / "closure.json"))
        self.assertIn(verdict.standing, {"ALIVE", "PARTIAL_ALIVE"}, verdict.refusals)

    def test_rfc9_crown_test_on_committed_graph(self):
        ok, detail = evidence.crown_test(projector.load_inputs(RELEASE_DIR))
        self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main()
