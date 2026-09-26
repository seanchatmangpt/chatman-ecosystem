"""RFC-0005 §8 crown self-attack: one fault per §39 class variant, run against the real court."""

from __future__ import annotations

import re
import unittest
from dataclasses import replace

from _autonomic_support import AUTONOMY, committed_inputs

from scripts.release_train.autonomic_crown import faults
from scripts.release_train.autonomic_crown.model import CODES, RECOVERABILITY
from scripts.release_train.root_crown.model import FAILURE_CLASSES
from scripts.release_train.root_crown.requirements import premise_sections

_ROW = re.compile(r"^\| ([A-Z_]+) \| ([^|]+) \| ([RU]) \|", re.MULTILINE)


class FaultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._inputs = None

    def setUp(self):
        if FaultsTest._inputs is None:
            FaultsTest._inputs = committed_inputs(self)
            FaultsTest._report = faults.run(FaultsTest._inputs)
        self.inputs = FaultsTest._inputs
        self.report = FaultsTest._report["faults"]

    def test_recoverability_table_is_the_rfc_table(self):
        text = (AUTONOMY / "imports" / "RFC-0005.md").read_text(encoding="utf-8")
        rows = {(c, v.strip()): r for c, v, r in _ROW.findall(premise_sections(text)["§8"])}
        self.assertEqual(rows, RECOVERABILITY)
        self.assertEqual({c for c, _ in rows}, set(FAILURE_CLASSES))

    def test_catalog_covers_every_variant_once(self):
        catalog = faults.faults(self.inputs)
        self.assertEqual(sorted((f.failure_class, f.variant) for f in catalog), sorted(RECOVERABILITY))
        for f in catalog:
            self.assertEqual(CODES[f.code][0], f.failure_class, f.name)

    def test_recoverable_faults_repair_and_reverify_to_baseline(self):
        for name, row in self.report.items():
            if row["recoverability"] != "R":
                continue
            with self.subTest(fault=name):
                self.assertTrue(row["typed"], row)
                self.assertTrue(row["repaired"], row)
                self.assertNotEqual(row["attempt_input_digest"], row["repair_input_digest"])
                self.assertTrue(row["hypothesis"])
                self.assertTrue(row["ok"])

    def test_unrecoverable_faults_are_typed_and_contained(self):
        for name, row in self.report.items():
            if row["recoverability"] != "U":
                continue
            with self.subTest(fault=name):
                self.assertTrue(row["typed"], row)
                self.assertFalse(row["repaired"])
                self.assertNotIn("repair_input_digest", row)
                self.assertTrue(row["independent_unchanged"], row)
                self.assertTrue(row["ok"])

    def test_authority_fault_is_refused_never_repaired(self):
        from scripts.release_train.autonomic_crown.court import evaluate

        fault = next(f for f in faults.faults(self.inputs) if f.failure_class == "AUTHORITY_FAILURE")
        self.assertIsNone(fault.repair)
        ev = evaluate(fault.inject(self.inputs), self_attack=False)
        self.assertEqual(ev.authority, "REFUSED")
        self.assertTrue(ev.refused)

    def test_transport_failure_is_not_rewritten_as_subject_failure(self):
        from scripts.release_train.autonomic_crown.court import evaluate

        fault = next(f for f in faults.faults(self.inputs) if f.failure_class == "TRANSPORT_FAILURE")
        ev = evaluate(fault.inject(self.inputs), self_attack=False)
        self.assertEqual(ev.execution, {"state": "BLOCKED", "type": "TRANSPORT_FAILURE"})
        self.assertNotIn("SUBJECT_SPLIT", ev.codes)

    def test_unchanged_retry_is_refused(self):
        stale = next(f for f in faults.faults(self.inputs) if f.name == "evidence-stale")
        lazy = replace(stale, repair=lambda i: i)  # retries the faulted input unchanged
        row = faults.run(self.inputs, (lazy,))["faults"]["evidence-stale"]
        self.assertEqual(row["detail"], "REFUSED:UNCHANGED_RETRY")
        self.assertFalse(row["ok"])

    def test_a_fault_the_court_does_not_type_fails(self):
        """Anti-vacuity: an injection the court ignores cannot count as a handled fault."""
        noop = faults.Fault("noop", "CAPABILITY_GAP", "any", "UNSUPPORTED_EVIDENCE_KIND", lambda i: i, None)
        row = faults.run(self.inputs, (noop,))["faults"]["noop"]
        self.assertFalse(row["typed"])
        self.assertFalse(row["ok"])

    def test_a_repair_that_does_not_restore_baseline_fails(self):
        stale = next(f for f in faults.faults(self.inputs) if f.name == "evidence-stale")
        wrong = replace(stale, repair=lambda i: replace(i, hypothesis="guess; change nothing real"))
        row = faults.run(self.inputs, (wrong,))["faults"]["evidence-stale"]
        self.assertFalse(row["repaired"])
        self.assertFalse(row["ok"])


if __name__ == "__main__":
    unittest.main()
