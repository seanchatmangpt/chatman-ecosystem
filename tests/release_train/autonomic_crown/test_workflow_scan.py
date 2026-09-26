"""U-13 / U-16 / U-17 scan against the real root-crown.yml (current tree and tag-time subject)."""

from __future__ import annotations

import re
import unittest

from _autonomic_support import WORKFLOW, committed_evaluation

from scripts.release_train.autonomic_crown import workflow_scan


class WorkflowScanTest(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.scan = workflow_scan.scan(self.text)

    def test_current_root_crown_is_pinned_except_hosted_runner_images(self):
        kinds = {v.split(":", 1)[0] for v in self.scan.violations}
        self.assertEqual(kinds, {"HOSTED_RUNNER_IMAGE_MUTABLE"})
        self.assertEqual(len(self.scan.violations), 3)  # crown, autonomic, tag jobs

    def test_schedulers_and_triggers(self):
        self.assertEqual(self.scan.schedulers, 1)
        self.assertEqual(set(self.scan.triggers), {"schedule", "workflow_dispatch", "push", "pull_request"})
        self.assertTrue(self.scan.triggers["push"]["paths"])
        self.assertEqual(self.scan.independent_triggers, [])
        self.assertTrue(self.scan.warns_on_blocked)

    def test_autonomic_job_uses_the_crown_pins(self):
        crown = self.text[self.text.index("  crown:") : self.text.index("  autonomic:")]
        auto = self.text[self.text.index("  autonomic:") : self.text.index("  tag:")]

        def pins(block):
            return set(re.findall(r"uses: (\S+@[0-9a-f]{40})", block))

        crown_pins = {p for p in pins(crown) if "upload-artifact" not in p}
        self.assertTrue(crown_pins and crown_pins <= pins(auto), (crown_pins, pins(auto)))
        self.assertIn("python-version: '3.12.14'", auto)
        self.assertIn("needs: crown", auto)
        self.assertRegex(auto, r"permissions:\n\s+contents: read\n\s+actions: read\n")
        self.assertIn('3) echo "::warning title=autonomic crown NOT_AUTONOMIC', auto)
        self.assertIn('*) echo "::error title=autonomic crown REFUSED', auto)

    def test_violations_are_detected(self):
        bad = (
            "on:\n  schedule:\n    - cron: '1 * * * *'\n  push:\n    branches: [main]\n"
            "jobs:\n  a:\n    runs-on: ubuntu-latest\n    container: node:20\n    steps:\n"
            "      - uses: actions/checkout@v4\n      - uses: ./local-action\n"
            "      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1\n"
            "        with:\n          python-version: '3.12'\n"
        )
        s = workflow_scan.scan(bad)
        self.assertEqual(
            sorted(v.split(":", 1)[0] for v in s.violations),
            ["FLOATING_RUNNER", "INEXACT_TOOLCHAIN", "UNPINNED_ACTION", "UNPINNED_CONTAINER"],
        )
        self.assertEqual(s.independent_triggers, ["push"])
        self.assertFalse(s.warns_on_blocked)

    def test_evaluated_subject_is_the_tag_time_workflow(self):
        """The committed receipt scans root-crown.yml at the crown subject that ran (68bacd8d)."""
        ev = committed_evaluation(self)
        g = {x.id: x for x in ev.gates}
        self.assertEqual(g["U-13"].state, "BLOCKED")
        self.assertIn("UNPINNED_ACTION", {f.split(":", 1)[0] for f in g["U-13"].findings})
        self.assertEqual(g["U-16"].code, "BLOCKED_ONLY_WARNS")
        self.assertEqual((g["U-17"].code, g["U-17"].measured), ("SINGLE_SCHEDULER", True))
        self.assertTrue(
            ev.input_digests["workflow"]["locator"].startswith("git:seanchatmangpt/chatman-ecosystem@68bacd8d")
        )


if __name__ == "__main__":
    unittest.main()
