"""RFC-0004 alignment: *terminal* acceptance criteria vs *capability* acceptance criteria.

RFC §48 phrases AC-02 ("all required subjects terminal") and AC-15 ("GodsLaw semantic
migration has terminal standing") as terminality claims; RFC §5/§38 define the terminal
dispositions, and a typed BLOCKED/SUPERSEDED/UNSUPPORTED/REFUSED disposition is one of
them. Every other AC ("court passes", "executes", "validates", "enforced", "succeeds")
is a capability claim that still needs PASS evidence on an exact merged SHA.

Chicago style: the real committed release tree (``alive_tree``), the real release
closure court and the real evaluators; every test mutates one real input file or one
real observation record and asserts on the returned state.
"""

from __future__ import annotations

import copy
import unittest

from _support import CROWN_SHA, REPO, alive_observations, alive_tree, dump, load

from scripts.release_train.root_crown import crown, evidence

TYPED = "lane:court-unharvested;R_missing_consequence;EVIDENCE_FAILURE"


class TerminalAlignmentTest(unittest.TestCase):
    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)

    def tearDown(self):
        self.tree.cleanup()

    def ctx(self, obs=None):
        return evidence.Context(
            root=self.tree.root,
            release_dir=self.tree.release_dir,
            observations=self.obs if obs is None else obs,
            crown_sha=CROWN_SHA,
            inputs=self.tree.inputs(),
        )

    def evaluate(self, rid, obs=None):
        req = next(r for r in self.tree.inputs().requirements if r.id == rid)
        return evidence.EVALUATORS[req.evidence_kind](req, self.ctx(obs))

    def closure_row(self, **fields):
        closure = load(self.tree.release_dir / "closure.json")
        row = next(r for r in closure["subjects"] if r["subject_id"] == "AFFIDAVIT")
        row.update(fields)
        for key, value in list(row.items()):
            if value is None:
                del row[key]
        dump(self.tree.release_dir / "closure.json", closure)

    def remote(self, rid, **json_fields):
        obs = copy.deepcopy(self.obs)
        locator = next(r for r in self.tree.inputs().requirements if r.id == rid).evidence_locator
        obs["artifacts"][locator]["json"].update(json_fields)
        return obs

    # --- AC-02 / F-03: closure terminality ---------------------------------------------
    def test_typed_blocked_closure_row_is_terminal(self):
        """RFC §38: "Every normative artifact SHALL terminate as one of: FINAL,
        SUPERSEDED(successor), BLOCKED(reason), UNSUPPORTED(capability_gap), REFUSED(type)".
        A BLOCKED row carrying type + broken_term + §39 class + owner therefore satisfies
        AC-02 ("all required subjects terminal") and does not fire F-03."""
        self.closure_row(impl_standing="BLOCKED", impl_type=TYPED, courts=[])
        for rid in ("AC-02", "F-03"):
            state = self.evaluate(rid)
            self.assertEqual(state.state, "PASS", state.detail)
            self.assertIn("1 typed non-ALIVE", state.detail)

    def test_committed_closure_rows_are_all_typed_terminal(self):
        """RFC §37: "Every relevant repository MUST have a terminal disposition." The real
        committed closure.json rows are typed terminal dispositions, so AC-02 PASSes on them."""
        dump(self.tree.release_dir / "closure.json", load(REPO / "release/v26.9.25/closure.json"))
        state = self.evaluate("AC-02")
        self.assertEqual(state.state, "PASS", state.detail)

    def test_untyped_blocked_closure_row_is_refused(self):
        """RFC §39: "Failure SHALL be typed." A BLOCKED row whose reason names neither a
        Chatman broken_term nor a §39 failure class is not terminal: AC-02 REFUSES."""
        self.closure_row(impl_standing="BLOCKED", impl_type="waiting on something", courts=[])
        state = self.evaluate("AC-02")
        self.assertEqual((state.state, state.code), ("REFUSED", "SUBJECT_NOT_TERMINAL"))
        self.assertIn("missing=broken_term+failure_class", state.detail)

    def test_blocked_without_any_type_is_refused(self):
        """RFC §38: "BLOCKED(reason)" -- a BLOCKED row without a reason is not terminal."""
        self.closure_row(impl_standing="BLOCKED", impl_type=None, courts=[])
        state = self.evaluate("AC-02")
        self.assertEqual((state.state, state.code), ("REFUSED", "SUBJECT_NOT_TERMINAL"))

    def test_unknown_required_row_is_refused(self):
        """RFC §5: "A required release subject MUST NOT remain `UNKNOWN`." (§47 falsifier 3)."""
        self.closure_row(impl_standing="UNKNOWN", impl_type=None, courts=[])
        for rid in ("AC-02", "F-03"):
            state = self.evaluate(rid)
            self.assertEqual((state.state, state.code), ("REFUSED", "SUBJECT_NOT_TERMINAL"))

    def test_partial_alive_row_is_not_terminal(self):
        """RFC §38: "A draft without disposition SHALL block closure if it is required for the
        release." PARTIAL_ALIVE is a §5 state but not a §38 disposition: BLOCKED, not PASS."""
        self.closure_row(impl_standing="PARTIAL_ALIVE", impl_type=None)
        state = self.evaluate("AC-02")
        self.assertEqual((state.state, state.code), ("BLOCKED", "CLOSURE_PARTIAL"))
        self.assertIn("AFFIDAVIT:impl=PARTIAL_ALIVE", state.detail)

    # --- AC-15: terminal receipt standing ------------------------------------------------
    def test_typed_blocked_receipt_satisfies_terminal_ac(self):
        """RFC §48: "AC-15 GodsLaw semantic migration has terminal standing"; RFC §38 lists
        BLOCKED(reason) as terminal. Shape of the real zoela godslaw-migration receipt."""
        obs = self.remote(
            "AC-15",
            standing="BLOCKED",
            type="AUTHORITY_FAILURE:operator-repo-rename",
            broken_term="R_missing_authority",
        )
        state = self.evaluate("AC-15", obs)
        self.assertEqual(state.state, "PASS", state.detail)
        self.assertIn("terminal BLOCKED", state.detail)

    def test_structured_refused_receipt_is_terminal_when_typed(self):
        """RFC §38 "REFUSED(type)" in the Chatman receipt form {value, derived_from, broken_term}."""
        obs = self.remote(
            "AC-15",
            standing={"value": "REFUSED(MODEL_COUNTEREXAMPLE)", "derived_from": "x", "broken_term": "mu_unlawful"},
        )
        self.assertEqual(self.evaluate("AC-15", obs).state, "PASS")

    def test_untyped_terminal_receipt_is_refused(self):
        """RFC §39: "Failure SHALL be typed." A terminal AC receipt BLOCKED without a
        broken_term/§39 class is refused, not accepted as terminal."""
        obs = self.remote("AC-15", standing="BLOCKED", type="operator-repo-rename")
        state = self.evaluate("AC-15", obs)
        self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))

    def test_unknown_terminal_receipt_is_refused(self):
        """RFC §5: "A required release subject MUST NOT remain `UNKNOWN`." """
        state = self.evaluate("AC-15", self.remote("AC-15", standing="UNKNOWN"))
        self.assertEqual((state.state, state.code), ("REFUSED", "REQUIRED_UNKNOWN"))

    def test_terminal_receipt_still_needs_a_merged_subject(self):
        """RFC §6/§45: exact subjects. A typed terminal receipt on a diverged SHA is REFUSED."""
        obs = self.remote("AC-15", standing="BLOCKED", type=TYPED)
        locator = next(r for r in self.tree.inputs().requirements if r.id == "AC-15").evidence_locator
        obs["artifacts"][locator]["subject_compare"] = "diverged"
        state = self.evaluate("AC-15", obs)
        self.assertEqual((state.state, state.code), ("REFUSED", "ARTIFACT_SUBJECT_SPLIT"))

    # --- capability ACs are not relaxed --------------------------------------------------
    def test_typed_blocked_on_capability_ac_stays_blocked(self):
        """RFC §48: "AC-08 BRCE zero-unreceipted-actuation court passes"; RFC §5: "`ALIVE` SHALL
        mean: observed execution of the exact admitted subject". A fully typed BLOCKED receipt
        is terminal but is not a passing court: capability ACs stay BLOCKED."""
        for rid in ("AC-07", "AC-08", "AC-13", "AC-14", "AC-16", "F-05"):
            with self.subTest(rid=rid):
                obs = self.remote(rid, standing="BLOCKED", type=TYPED, broken_term="R_missing_consequence")
                state = self.evaluate(rid, obs)
                self.assertEqual((state.state, state.code), ("BLOCKED", "ARTIFACT_BLOCKED"))

    def test_capability_ac_crown_is_blocked_not_alive(self):
        """RFC §44: the crown evaluates "TLA_runtime_court"; a typed BLOCKED TLC receipt keeps F BLOCKED."""
        obs = self.remote("AC-07", standing="BLOCKED", type=TYPED)
        verdict = crown.evaluate(self.tree.release_dir, obs, None, CROWN_SHA, root=self.tree.root)
        self.assertEqual(verdict.standing, "BLOCKED")
        self.assertEqual(verdict.terms["F"], "BLOCKED")

    def test_structured_local_receipt_standing(self):
        """RFC §19 (AC-10 "reversible migration court passes"): the Chatman topology receipt
        records standing as {value, derived_from}; value ALIVE PASSes, BLOCKED:<reason> does not."""
        path = self.tree.release_dir / "observations/TOPOLOGY-RECEIPT.json"
        dump(path, {"standing": {"value": "ALIVE", "derived_from": "verify exit 0"}, "m_term": {"holds": True}})
        self.assertEqual(self.evaluate("AC-10").state, "PASS")
        dump(path, {"standing": {"value": "BLOCKED:owner-signoff", "derived_from": "verify exit 1"}})
        state = self.evaluate("AC-10")
        self.assertEqual((state.state, state.code), ("BLOCKED", "ARTIFACT_BLOCKED"))


if __name__ == "__main__":
    unittest.main()
