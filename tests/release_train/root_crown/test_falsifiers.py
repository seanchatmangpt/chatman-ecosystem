"""RFC-0004 §47 falsifier table: F-01..F-14 each refused by the real evaluator it is bound to.

Anti-vacuity: the table keys must equal the F ids in requirements.json, and every mutant
starts from an ALIVE tree whose evaluator PASSes the same requirement.
"""

from __future__ import annotations

import unittest

from _support import CROWN_SHA, alive_observations, alive_tree, dump, load

from scripts.release_train.root_crown import evidence
from scripts.release_train.root_crown.requirements import rfc_requirement_ids


def _artifact(field, value):
    def mutate(tree, obs, req):
        obs["artifacts"][req.evidence_locator]["json"][field] = value

    return mutate


def f02(tree, obs, req):
    closure = load(tree.release_dir / "closure.json")
    closure["subjects"][0]["rfc_id"] = "RFC-0004-OTHER"  # zero FINAL_SPEC owners for RFC-0004
    dump(tree.release_dir / "closure.json", closure)


def f03(tree, obs, req):
    closure = load(tree.release_dir / "closure.json")
    closure["subjects"][2]["impl_standing"] = "UNKNOWN"
    dump(tree.release_dir / "closure.json", closure)


def f04(tree, obs, req):
    pins = load(tree.release_dir / "pins.json")
    pins["repos"]["ggen-marketplace"]["sha"] = "02c13c468892c040c8abfd5023db4c1a19fa4820"
    dump(tree.release_dir / "pins.json", pins)


def f06(tree, obs, req):
    path = tree.release_dir / "berthier.json"
    graph = load(path)
    graph["edges"][0]["compiled_from"] = "0" * 64  # a dependent compiled from a premise that no longer exists
    dump(path, graph)


def f07(tree, obs, req):
    path = tree.root / "docs/jira/v26.9.25/xprod-cases/XPROD-001.json"
    case = load(path)
    case["mutants"] = [{"mutant_id": "M-1", "formalism": "TLA+", "claim_id": "CLAIM-1", "expected": "COUNTEREXAMPLE"}]
    dump(path, case)  # the TLA+ evidence still PASSes under a violating mutant: MUTANT_SURVIVED


def f09(tree, obs, req):
    obs["artifacts"][req.evidence_locator]["json"].pop("execution_receipt")


def f10(tree, obs, req):
    obs["local_worktrees"]["worktrees"] = [{"repo": "xaas", "path": "/Users/sac/xaas/.claude/worktrees/ex4pm"}]


def f14(tree, obs, req):
    obs["tag"]["sha"] = "1" * 40


def f11(tree, obs, req):
    dump(
        tree.release_dir / "observations/TOPOLOGY-RECEIPT.json", {"standing": "REFUSED", "type": "UNREVERSIBLE_CLEANUP"}
    )


TABLE = {
    "F-01": (_artifact("standing", "REFUSED"), "ARTIFACT_REFUSED"),
    "F-02": (f02, "ORIGIN_AUTHORITY_NOT_UNIQUE"),
    "F-03": (f03, "SUBJECT_NOT_TERMINAL"),
    "F-04": (f04, "TRANSIENT_DEPENDENCY"),
    "F-05": (_artifact("standing", "REFUSED"), "ARTIFACT_REFUSED"),
    "F-06": (f06, "BERTHIER_COURT_FAILED"),
    "F-07": (f07, "XPROD_REFUSED"),
    "F-08": (_artifact("standing", "REFUSED"), "ARTIFACT_REFUSED"),
    "F-09": (f09, "CLAIM_WITHOUT_RECEIPT"),
    "F-10": (f10, "UNAUTHORIZED_WORKTREE"),
    "F-11": (f11, "ARTIFACT_REFUSED"),
    "F-12": (_artifact("standing", "REFUSED"), "ARTIFACT_REFUSED"),
    "F-13": (_artifact("standing", "REFUSED"), "ARTIFACT_REFUSED"),
    "F-14": (f14, "TAG_SHA_SPLIT"),
}


class FalsifierTableTest(unittest.TestCase):
    def test_table_covers_exactly_the_premise_and_requirements(self):
        tree = alive_tree()
        try:
            inputs = tree.inputs()
            declared = {r.id for r in inputs.requirements if r.kind == "FALSIFIER"}
            premise = {i for i in rfc_requirement_ids(inputs.rfc_text) if i.startswith("F-")}
            self.assertEqual(set(TABLE), declared)
            self.assertEqual(set(TABLE), premise)
        finally:
            tree.cleanup()

    def test_each_falsifier_passes_alive_and_refuses_its_mutant(self):
        for fid, (mutate, code) in TABLE.items():
            with self.subTest(falsifier=fid):
                tree = alive_tree()
                try:
                    obs = alive_observations(tree)
                    req = next(r for r in tree.inputs().requirements if r.id == fid)
                    fn = evidence.EVALUATORS[req.evidence_kind]

                    def ctx():
                        return evidence.Context(tree.root, tree.release_dir, obs, CROWN_SHA, tree.inputs())

                    self.assertEqual(fn(req, ctx()).state, "PASS")
                    mutate(tree, obs, req)
                    state = fn(req, ctx())
                    self.assertEqual((state.state, state.code), ("REFUSED", code), state.detail)
                finally:
                    tree.cleanup()

    def test_f09_typed_blocker_is_lawful(self):
        """RFC §55 "cloud_runtime_alive_or_typed_blocker": a typed (type + broken_term + §39 class
        + owner) BLOCKED receipt bound to a merged subject is lawful; a type without a Chatman
        broken_term is not typed (RFC §39 "Failure SHALL be typed"), and no type at all is refused."""
        tree = alive_tree()
        try:
            obs = alive_observations(tree)
            req = next(r for r in tree.inputs().requirements if r.id == "F-09")
            subject = obs["artifacts"][req.evidence_locator]["json"]["subject_sha"]

            def evaluate(receipt):
                obs["artifacts"][req.evidence_locator]["json"] = receipt
                return evidence.typed_blocker_allowed(
                    req, evidence.Context(tree.root, tree.release_dir, obs, CROWN_SHA, tree.inputs())
                )

            typed = {"standing": "BLOCKED", "type": "TRANSPORT_FAILURE:live-cloud-leg", "subject_sha": subject}
            state = evaluate(typed | {"broken_term": "R_missing_consequence"})
            self.assertEqual(state.state, "PASS", state.detail)
            self.assertIn("terminal BLOCKED(TRANSPORT_FAILURE:live-cloud-leg) (RFC §55", state.detail)
            state = evaluate(typed)
            self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))
            self.assertTrue(state.detail.endswith(":BLOCKED:missing=broken_term"), state.detail)
            state = evaluate({"standing": "BLOCKED"})
            self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))
        finally:
            tree.cleanup()

if __name__ == "__main__":
    unittest.main()
