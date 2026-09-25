"""Requirement-graph admission: the committed graph admits; one refusing mutant per rule."""

from __future__ import annotations

import copy
import unittest

from _support import REPO, RELEASE, load

from scripts.release_train.root_crown.evidence import EVALUATORS
from scripts.release_train.root_crown.model import REQ_RULES, code_of
from scripts.release_train.root_crown.requirements import rfc_requirement_ids, validate_requirements

RELEASE_DIR = REPO / "release" / RELEASE
DOC = load(RELEASE_DIR / "requirements.json")
PINS = load(RELEASE_DIR / "pins.json")
RFC = (RELEASE_DIR / "imports/RFC-0004.md").read_text(encoding="utf-8")


def _row(doc, rid):
    return next(r for r in doc["requirements"] if r["id"] == rid)


def m_malformed(doc):
    del _row(doc, "AC-01")["acceptance"]


def m_duplicate(doc):
    doc["requirements"].append(copy.deepcopy(_row(doc, "AC-01")))


def m_coverage(doc):
    doc["requirements"] = [r for r in doc["requirements"] if r["id"] != "AC-07"]


def m_owner(doc):
    _row(doc, "AC-03")["owner_repo"] = "o/unknown"


def m_term(doc):
    _row(doc, "AC-01")["term"] = "Z"


def m_premise(doc):
    _row(doc, "AC-05")["premise_refs"] = ["§99"]


def m_kind(doc):
    _row(doc, "AC-06")["evidence_kind"] = "vibes"


MUTANTS = {
    "REQ_MALFORMED": m_malformed,
    "REQ_DUPLICATE_ID": m_duplicate,
    "REQ_COVERAGE_GAP": m_coverage,
    "REQ_OWNER_UNADMITTED": m_owner,
    "REQ_TERM_UNBOUND": m_term,
    "REQ_PREMISE_UNBOUND": m_premise,
    "REQ_KIND_UNKNOWN": m_kind,
}


class RequirementsTest(unittest.TestCase):
    def test_committed_graph_admits(self):
        self.assertEqual(validate_requirements(DOC, PINS, RFC, EVALUATORS), [])

    def test_premise_declares_19_acs_and_14_falsifiers(self):
        ids = rfc_requirement_ids(RFC)
        self.assertEqual(sum(i.startswith("AC-") for i in ids), 19)
        self.assertEqual(sum(i.startswith("F-") for i in ids), 14)
        self.assertEqual(ids, {r["id"] for r in DOC["requirements"]})

    def test_every_term_has_requirements(self):
        self.assertEqual({r["term"] for r in DOC["requirements"]}, {"C", "A", "R", "X", "F", "M"})

    def test_mutant_table_covers_every_rule(self):
        self.assertEqual(set(MUTANTS), set(REQ_RULES))

    def test_each_mutant_refuses_its_rule(self):
        for rule, mutate in MUTANTS.items():
            with self.subTest(rule=rule):
                doc = copy.deepcopy(DOC)
                mutate(doc)
                codes = {code_of(r) for r in validate_requirements(doc, PINS, RFC, EVALUATORS)}
                self.assertIn(rule, codes)

    def test_emptied_term_refuses(self):
        doc = copy.deepcopy(DOC)
        doc["requirements"] = [r for r in doc["requirements"] if r["term"] != "M"]
        refusals = validate_requirements(doc, PINS, RFC, EVALUATORS)
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:M:no-requirement", refusals)


if __name__ == "__main__":
    unittest.main()
