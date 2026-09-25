"""Terminality policy (``policy/v26.9.25/terminality.json``, ``policy.py``) and the owner rule.

RFC-0004 §48 "AC-02 all required subjects terminal" and "AC-15 ... has terminal standing",
§47 "3. A required subject remains UNKNOWN" and §55 "cloud_runtime_alive_or_typed_blocker"
are the only premises that admit a non-success terminal state. Every other requirement
needs its success state. The policy states this per row, and ``policy.py`` refuses a
policy that is missing, incomplete, relaxed without a literal RFC grounding, or stale
against the acceptance text.

Chicago style: the real committed policy, the real RFC import, the real release tree
(``alive_tree``) and the real evaluators and crown. Every negative case writes one real
edited policy file into a temp directory (``Context.policy_root``) or edits one real input.
"""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _support import CROWN_SHA, REPO, RELEASE, alive_observations, alive_tree, dump, load

from scripts.release_train.root_crown import binding, crown, evidence, policy
from scripts.release_train.root_crown.model import FAILURE_CLASS, TERMINALITY_RULES, code_of

POLICY = REPO / "scripts/release_train/root_crown/policy" / RELEASE / "terminality.json"
RFC = REPO / "release" / RELEASE / "imports/RFC-0004.md"
AMENDMENT = REPO / "release" / RELEASE / "hardening/amendments/AC-02-5fda5028.json"
TYPED = "AUTHORITY_FAILURE:operator-repo-rename;R_missing_authority"
RELAXED = {"AC-02", "AC-15", "F-03", "F-09"}
ALL_TYPED = ["SUPERSEDED", "BLOCKED", "UNSUPPORTED", "REFUSED"]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CommittedPolicyTest(unittest.TestCase):
    """The committed policy, read as data and judged by the real validator."""

    @classmethod
    def setUpClass(cls):
        cls.doc = load(POLICY)
        cls.rows = {r["id"]: r for r in cls.doc["rows"]}
        cls.reqs = load(REPO / "release" / RELEASE / "requirements.json")["requirements"]
        cls.rfc = RFC.read_text(encoding="utf-8")

    def test_one_row_per_requirement_33_rows(self):
        self.assertEqual(len(self.doc["rows"]), 33)
        self.assertEqual(set(self.rows), {r["id"] for r in self.reqs})
        for row in self.doc["rows"]:
            self.assertEqual(set(row), set(policy.ROW_FIELDS), row["id"])

    def test_committed_policy_is_admitted(self):
        loaded = policy.load_policy(RELEASE)
        imports = load(REPO / "release" / RELEASE / "imports/IMPORTS.json")["imports"][0]["sha256"]
        self.assertEqual(policy.validate(loaded, None, self.reqs, self.rfc, imports), [])

    def test_only_the_four_grounded_rows_admit_non_success(self):
        relaxed = {rid for rid, r in self.rows.items() if set(r["allowed_terminal_states"]) - {"ALIVE", "FINAL"}}
        self.assertEqual(relaxed, RELAXED)
        for rid in ("AC-02", "F-03", "AC-15"):
            self.assertEqual(self.rows[rid]["allowed_terminal_states"], ["ALIVE", "FINAL"] + ALL_TYPED, rid)
        self.assertEqual(self.rows["F-09"]["allowed_terminal_states"], ["ALIVE", "BLOCKED", "UNSUPPORTED"])
        for rid in set(self.rows) - RELAXED:
            self.assertEqual(self.rows[rid]["allowed_terminal_states"], ["ALIVE"], rid)
            self.assertEqual(self.rows[rid]["standing_ceiling"], "ALIVE", rid)
        for rid in RELAXED:
            self.assertEqual(self.rows[rid]["standing_ceiling"], "TERMINAL", rid)

    def test_relaxation_phrases_are_literal_substrings_of_the_pinned_rfc(self):
        expected = {
            "AC-02": ("§48", "all required subjects terminal"),
            "AC-15": ("§48", "has terminal standing"),
            "F-03": ("§47", "A required subject remains UNKNOWN"),
            "F-09": ("§55", "cloud_runtime_alive_or_typed_blocker"),
        }
        self.assertEqual(self.doc["rfc_import"]["sha256"], sha(self.rfc))
        for rid, (anchor, phrase) in expected.items():
            self.assertEqual((self.rows[rid]["rfc_anchor"], self.rows[rid]["rfc_phrase"]), (anchor, phrase))
            self.assertIn(phrase, self.rfc, rid)

    def test_acceptance_digests_match_requirements(self):
        for req in self.reqs:
            self.assertEqual(self.rows[req["id"]]["acceptance_sha256"], sha(req["acceptance"]), req["id"])

    def test_authority_required(self):
        self.assertEqual(self.rows["AC-19"]["authority_required"], "release-crown-environment")
        self.assertEqual({r["authority_required"] for rid, r in self.rows.items() if rid != "AC-19"}, {"NONE"})


class PolicyRefusalTest(unittest.TestCase):
    """Each refusal code, emitted by the real validator on one edited real policy file."""

    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)
        self._tmp = tempfile.TemporaryDirectory()
        self.policy_root = Path(self._tmp.name)
        self.doc = load(POLICY)

    def tearDown(self):
        self.tree.cleanup()
        self._tmp.cleanup()

    def write(self, doc=None, release=RELEASE):
        dump(self.policy_root / release / "terminality.json", self.doc if doc is None else doc)

    def row(self, rid):
        return next(r for r in self.doc["rows"] if r["id"] == rid)

    def ctx(self, obs=None):
        return evidence.Context(
            root=self.tree.root,
            release_dir=self.tree.release_dir,
            observations=self.obs if obs is None else obs,
            crown_sha=CROWN_SHA,
            inputs=self.tree.inputs(),
            policy_root=self.policy_root,
        )

    def evaluate(self, rid, obs=None):
        req = next(r for r in self.tree.inputs().requirements if r.id == rid)
        return evidence.EVALUATORS[req.evidence_kind](req, self.ctx(obs))

    def codes(self):
        return {code_of(r) for r in self.ctx().policy_refusals()}

    def crown_codes(self):
        verdict = crown.evaluate(self.tree.release_dir, self.obs, None, CROWN_SHA, root=self.tree.root, policy_root=self.policy_root)
        return verdict, {code_of(r) for r in verdict.refusals}

    def test_committed_copy_is_admitted_and_crown_alive(self):
        self.write()
        self.assertEqual(self.codes(), set())
        verdict, codes = self.crown_codes()
        self.assertEqual((verdict.standing, codes), ("ALIVE", set()))

    def test_missing_policy(self):
        """No policy file: every consulting evaluator and the crown refuse TERMINALITY_POLICY_MISSING."""
        for rid in ("AC-02", "F-03", "AC-15", "AC-07", "F-09"):
            with self.subTest(rid=rid):
                state = self.evaluate(rid)
                self.assertEqual((state.state, state.code), ("REFUSED", "TERMINALITY_POLICY_MISSING"))
        verdict, codes = self.crown_codes()
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("TERMINALITY_POLICY_MISSING", codes)

    def test_policy_for_another_release_or_unreadable_is_missing(self):
        self.write(dict(self.doc, release="v26.9.24"))
        self.assertEqual(self.codes(), {"TERMINALITY_POLICY_MISSING"})
        (self.policy_root / RELEASE / "terminality.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(self.codes(), {"TERMINALITY_POLICY_MISSING"})
        self.write(dict(self.doc, schema="https://example.invalid/other"))
        self.assertEqual(self.codes(), {"TERMINALITY_POLICY_MISSING"})

    def test_coverage_gap_missing_row(self):
        self.doc["rows"] = [r for r in self.doc["rows"] if r["id"] != "F-09"]
        self.write()
        self.assertIn("REFUSED:POLICY_COVERAGE_GAP:F-09:no-policy-row", self.ctx().policy_refusals())
        state = self.evaluate("F-09")
        self.assertEqual((state.state, state.code), ("REFUSED", "POLICY_COVERAGE_GAP"))
        _, codes = self.crown_codes()
        self.assertIn("POLICY_COVERAGE_GAP", codes)

    def test_coverage_gap_on_a_non_consulting_requirement_still_refuses_the_crown(self):
        """AC-01 (manifest_valid) never reads the policy; the crown's whole-document admission does."""
        self.doc["rows"] = [r for r in self.doc["rows"] if r["id"] != "AC-01"]
        self.write()
        verdict, codes = self.crown_codes()
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("REFUSED:POLICY_COVERAGE_GAP:AC-01:no-policy-row", verdict.refusals)

    def test_coverage_gap_duplicate_extra_and_malformed_rows(self):
        self.doc["rows"].append(copy.deepcopy(self.row("AC-07")))
        self.doc["rows"].append(dict(copy.deepcopy(self.row("AC-07")), id="AC-99"))
        self.row("AC-13")["evidence_required"] = ""
        self.write()
        refusals = self.ctx().policy_refusals()
        self.assertIn("REFUSED:POLICY_COVERAGE_GAP:AC-07:duplicate-row", refusals)
        self.assertIn("REFUSED:POLICY_COVERAGE_GAP:AC-99:not-a-requirement", refusals)
        self.assertIn("REFUSED:POLICY_COVERAGE_GAP:AC-13:malformed:evidence_required", refusals)
        self.assertEqual(self.evaluate("AC-07").code, "POLICY_COVERAGE_GAP")
        self.assertEqual(self.evaluate("AC-13").code, "POLICY_COVERAGE_GAP")

    def assert_ungrounded(self, rid, fragment):
        self.write()
        refusals = [r for r in self.ctx().policy_refusals() if f":{rid}" in r]
        self.assertTrue(any(r.startswith("REFUSED:POLICY_RELAXATION_UNGROUNDED:") for r in refusals), refusals)
        self.assertTrue(any(fragment in r for r in refusals), refusals)
        req = next(r for r in self.tree.inputs().requirements if r.id == rid)
        if req.evidence_kind in {"receipt_artifact", "closure_terminal", "typed_blocker_allowed"}:
            state = self.evaluate(rid)
            self.assertEqual((state.state, state.code), ("REFUSED", "POLICY_RELAXATION_UNGROUNDED"), state.detail)

    def relax(self, rid, **fields):
        row = self.row(rid)
        row.update({"allowed_terminal_states": ["ALIVE", "BLOCKED"], "standing_ceiling": "TERMINAL"} | fields)
        return row

    def test_relaxing_a_capability_row_with_its_own_phrase_is_ungrounded(self):
        """AC-07's own §48 line ("pinned TLA+ runtime court executes") names no terminality."""
        self.relax("AC-07")
        self.assert_ungrounded("AC-07", "names no terminality marker")

    def test_borrowing_another_requirements_terminal_phrase_is_ungrounded(self):
        """"has terminal standing" is AC-15's §48 line, not AC-07's."""
        self.relax("AC-07", rfc_phrase="has terminal standing")
        self.assert_ungrounded("AC-07", "not on AC-07's own §48 line")

    def test_section55_relaxation_not_naming_the_row_is_ungrounded(self):
        """§55 "normative_artifacts_terminal" carries a marker but its line names neither
        AC-07 nor AC-07's evaluator class (receipt_artifact): previously admitted."""
        self.relax("AC-07", rfc_anchor="§55", rfc_phrase="normative_artifacts_terminal")
        self.assert_ungrounded("AC-07", "no line names AC-07 or evaluator class receipt_artifact")

    def test_section38_relaxation_not_naming_the_row_is_ungrounded(self):
        """§38 closure rules name no requirement; a relaxation there cannot cite its own line."""
        self.relax("F-13", rfc_anchor="§38", rfc_phrase="BLOCKED(reason)")
        self.assert_ungrounded("F-13", "not on F-13's own §38 line")

    def test_f09_line_is_bound_through_its_evaluator_class_only(self):
        """F-09's §55 term is its own only via typed_blocker_allowed; another F row with a
        different evaluator borrowing the term alone (F-09 relaxed elsewhere) is ungrounded."""
        self.row("F-09")["rfc_phrase"] = "godslaw_migration_terminal"
        self.assert_ungrounded("F-09", "no line names F-09 or evaluator class typed_blocker_allowed")
        self.doc = load(POLICY)
        self.relax("F-13", rfc_anchor="§55", rfc_phrase="cloud_runtime_alive_or_typed_blocker")
        self.write()
        refusals = self.ctx().policy_refusals()
        self.assertTrue(any(r.startswith("REFUSED:POLICY_RELAXATION_UNGROUNDED:F-13:") and "own §55 line" in r
                            for r in refusals), refusals)
        self.assertFalse(any(r.startswith("REFUSED:POLICY_RELAXATION_UNGROUNDED:F-09:") for r in refusals), refusals)

    def test_own_lines_cover_every_anchor(self):
        section = "# 55. X\n  AND a_terminal\n  AND cloud_runtime_alive_or_typed_blocker\nAC-07 names it\n3. third\n"
        self.assertEqual(policy.own_lines("AC-07", "§55", section), ["AC-07 names it"])
        self.assertEqual(
            policy.own_lines("F-09", "§55", section, "typed_blocker_allowed"),
            ["  AND cloud_runtime_alive_or_typed_blocker"],
        )
        self.assertEqual(policy.own_lines("F-09", "§55", section, "receipt_artifact"), [])
        self.assertEqual(policy.own_lines("F-3", "§47", section), ["3. third"])
        self.assertEqual(policy.own_lines("AC-0", "§55", section), [], "AC-0 is not a token of AC-07")
        named = section + "  AND see F-13 here_terminal\n"
        self.assertEqual(policy.own_lines("F-13", "§55", named), ["  AND see F-13 here_terminal"])
        self.assertEqual(policy.own_lines("F-1", "§55", named), [], "F-1 is not a token of F-13")

    def test_phrase_absent_from_the_anchor_is_ungrounded(self):
        self.row("F-09")["rfc_phrase"] = "cloud_runtime_alive_or_any_blocker"
        self.assert_ungrounded("F-09", "not in §55")

    def test_absent_anchor_is_ungrounded(self):
        self.row("AC-15")["rfc_anchor"] = "§99"
        self.assert_ungrounded("AC-15", "anchor §99 absent")

    def test_rfc_import_digest_mismatch_is_ungrounded(self):
        self.doc["rfc_import"]["sha256"] = "0" * 64
        self.assert_ungrounded("AC-02", "rfc import sha256=")

    def test_relaxation_claiming_an_alive_ceiling_is_ungrounded(self):
        self.row("AC-15")["standing_ceiling"] = "ALIVE"
        self.assert_ungrounded("AC-15", "claims ceiling ALIVE")

    def test_success_row_claiming_a_terminal_ceiling_is_ungrounded(self):
        self.row("AC-08")["standing_ceiling"] = "TERMINAL"
        self.assert_ungrounded("AC-08", "success-only row claims ceiling TERMINAL")

    def test_non_terminal_state_is_never_admissible(self):
        self.row("AC-15")["allowed_terminal_states"].append("PARTIAL_ALIVE")
        self.assert_ungrounded("AC-15", "non-terminal states PARTIAL_ALIVE")

    def test_required_success_state_must_be_success_and_admitted(self):
        self.row("AC-16")["required_success_state"] = "BLOCKED"
        self.assert_ungrounded("AC-16", "required_success_state=BLOCKED")

    def test_one_grounding_cited_by_two_relaxations_is_ungrounded(self):
        self.relax("F-13", rfc_anchor="§55", rfc_phrase="cloud_runtime_alive_or_typed_blocker")
        self.write()
        self.assertIn(
            "REFUSED:POLICY_RELAXATION_UNGROUNDED:F-09,F-13:one grounding §55 "
            "'cloud_runtime_alive_or_typed_blocker' cited by several relaxations",
            self.ctx().policy_refusals(),
        )

    def test_acceptance_drift(self):
        """The acceptance text moved without the policy moving with it."""
        self.write()
        path = self.tree.release_dir / "requirements.json"
        doc = load(path)
        next(r for r in doc["requirements"] if r["id"] == "AC-15")["acceptance"] += " (restated)"
        dump(path, doc)
        state = self.evaluate("AC-15")
        self.assertEqual((state.state, state.code), ("REFUSED", "ACCEPTANCE_DRIFT"))
        self.assertIn("AC-15:acceptance sha256=", state.detail)
        self.assertIn("ACCEPTANCE_DRIFT", self.codes())

    def test_every_terminality_code_is_typed_and_emitted(self):
        """Anti-vacuity: each TERMINALITY_RULES code has a §39 class and is emitted by a real mutant."""
        for code in TERMINALITY_RULES:
            self.assertIn(code, FAILURE_CLASS)
        emitted = set()
        self.write()
        emitted |= self.codes()
        self.doc["rows"] = [r for r in self.doc["rows"] if r["id"] != "F-01"]
        self.relax("AC-07")
        self.row("AC-16")["acceptance_sha256"] = "0" * 64
        self.write()
        emitted |= self.codes()
        (self.policy_root / RELEASE / "terminality.json").unlink()
        emitted |= self.codes()
        obs = copy.deepcopy(self.obs)
        self.doc = load(POLICY)
        self.write()
        loc = next(r for r in self.tree.inputs().requirements if r.id == "AC-15").evidence_locator
        obs["artifacts"][loc]["json"].update(standing="BLOCKED", type=TYPED, owner="seanchatmangpt/xaas")
        emitted.add(self.evaluate("AC-15", obs).code)
        self.assertEqual(emitted, set(TERMINALITY_RULES))


class OwnerRuleTest(unittest.TestCase):
    """An explicit owner must equal the receipt's container repository, else OWNER_SPLIT."""

    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)

    def tearDown(self):
        self.tree.cleanup()

    def evaluate(self, rid, **fields):
        req = next(r for r in self.tree.inputs().requirements if r.id == rid)
        obs = copy.deepcopy(self.obs)
        obs["artifacts"][req.evidence_locator]["json"].update(fields)
        ctx = evidence.Context(self.tree.root, self.tree.release_dir, obs, CROWN_SHA, self.tree.inputs())
        return evidence.EVALUATORS[req.evidence_kind](req, ctx)

    def test_absent_owner_is_the_container(self):
        state = self.evaluate("AC-15", standing="BLOCKED", type=TYPED)
        self.assertEqual(state.state, "PASS", state.detail)
        self.assertIn("owner=seanchatmangpt/zoela owner_source=container", state.detail)

    def test_explicit_owner_equal_to_container(self):
        for key in evidence.OWNER_KEYS:
            with self.subTest(key=key):
                state = self.evaluate("AC-15", standing="BLOCKED", type=TYPED, **{key: "seanchatmangpt/zoela"})
                self.assertEqual(state.state, "PASS", state.detail)
                self.assertIn("owner_source=explicit", state.detail)

    def test_explicit_owner_of_another_repository_is_owner_split(self):
        for key in evidence.OWNER_KEYS:
            with self.subTest(key=key):
                state = self.evaluate("AC-15", standing="BLOCKED", type=TYPED, **{key: "seanchatmangpt/xaas"})
                self.assertEqual((state.state, state.code), ("REFUSED", "OWNER_SPLIT"), state.detail)
                self.assertIn("owner=seanchatmangpt/xaas container=seanchatmangpt/zoela", state.detail)

    def test_f09_owner_split(self):
        state = self.evaluate(
            "F-09", standing="BLOCKED", type="TRANSPORT_FAILURE:x;R_missing_consequence", repository="seanchatmangpt/zoela"
        )
        self.assertEqual((state.state, state.code), ("REFUSED", "OWNER_SPLIT"))

    def test_closure_row_owner_split_and_container_default(self):
        closure = load(self.tree.release_dir / "closure.json")
        row = next(r for r in closure["subjects"] if r["subject_id"] == "AFFIDAVIT")
        row.update(impl_standing="BLOCKED", impl_type="lane:x;R_missing_consequence;EVIDENCE_FAILURE", courts=[])
        dump(self.tree.release_dir / "closure.json", closure)
        req = next(r for r in self.tree.inputs().requirements if r.id == "AC-02")
        ctx = evidence.Context(self.tree.root, self.tree.release_dir, self.obs, CROWN_SHA, self.tree.inputs())
        self.assertEqual(evidence.closure_terminal(req, ctx).state, "PASS")
        row["owner"] = "seanchatmangpt/zoela"
        dump(self.tree.release_dir / "closure.json", closure)
        ctx = evidence.Context(self.tree.root, self.tree.release_dir, self.obs, CROWN_SHA, self.tree.inputs())
        state = evidence.closure_terminal(req, ctx)
        self.assertEqual((state.state, state.code), ("REFUSED", "OWNER_SPLIT"))
        self.assertIn("AFFIDAVIT:owner=seanchatmangpt/zoela container=seanchatmangpt/affidavit", state.detail)


class AmendmentReceiptTest(unittest.TestCase):
    """hardening/amendments/AC-02-5fda5028.json: the AC-02 relaxation, recorded, not reverted."""

    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        cls.rfc = RFC.read_text(encoding="utf-8")
        cls.ac02 = next(
            r for r in load(REPO / "release" / RELEASE / "requirements.json")["requirements"] if r["id"] == "AC-02"
        )

    def test_texts_and_digests_recompute(self):
        self.assertEqual(self.doc["before_sha256"], sha(self.doc["before_text"]))
        self.assertEqual(self.doc["after_sha256"], sha(self.doc["after_text"]))
        self.assertNotEqual(self.doc["before_text"], self.doc["after_text"])

    def test_after_text_is_the_committed_acceptance_not_restored(self):
        self.assertEqual(self.doc["after_text"], self.ac02["acceptance"])
        self.assertFalse(self.doc["text_restored"])
        self.assertEqual(self.doc["policy"]["acceptance_sha256"], load(POLICY)["rows"][1]["acceptance_sha256"])
        self.assertEqual(load(POLICY)["rows"][1]["id"], "AC-02")

    def test_grounding(self):
        self.assertEqual(self.doc["rfc_import"]["sha256"], sha(self.rfc))
        self.assertEqual((self.doc["rfc_anchor"], self.doc["rfc_phrase"]), ("§48", "all required subjects terminal"))
        self.assertIn(self.doc["premise"], self.rfc)
        self.assertIn(self.doc["rfc_phrase"], self.doc["premise"])
        self.assertEqual(self.doc["derivation"], "before ⊋ premise, after = premise")
        self.assertIn("closure court evaluates ALIVE", self.doc["before_text"])
        self.assertEqual(self.doc["standing"], "FINAL")

    def test_identity_and_durable_locators(self):
        self.assertEqual(self.doc["commit"], "5fda5028591652635583b0dfa6704cdf443012ad")
        self.assertEqual(self.doc["parent"], "8321663d02b849cbb7879b3eaf548d5bdca7a7e9")
        for key in ("before_locator", "after_locator"):
            self.assertRegex(self.doc[key], r"^git:seanchatmangpt/chatman-ecosystem@[0-9a-f]{40}:release/v26\.9\.25/requirements\.json$")
        self.assertIn(self.doc["parent"], self.doc["before_locator"])
        self.assertIn(self.doc["commit"], self.doc["after_locator"])


class HistoricalReplayUnchangedTest(unittest.TestCase):
    """The tag-time observations, re-evaluated by the hardened evaluators over the committed
    payload: the terminality policy refuses nothing (AC-15 and F-09 stay typed with the
    container as owner); the evidence binding (PR-4) is what moves the ceiling.

    Without the observed subject->container deltas every producer receipt read at a
    descendant head is REFUSED EVIDENCE_LINEAGE_MISSING; with the committed delta observations
    (hardening/inputs/delta-observations.json) the receipt-only affidavit delta is admitted and
    every other producer is typed BLOCKED EVIDENCE_DELTA_UNBOUNDED."""

    HIST = REPO / "release" / RELEASE / "hardening/receipts/run-36161744816"
    PREV = REPO / "release" / RELEASE / "hardening/receipts/run-36160116076"
    DELTAS = REPO / "release" / RELEASE / "hardening/inputs/delta-observations.json"
    PRODUCERS = {
        "AC-03", "AC-04", "AC-07", "AC-08", "AC-13", "AC-14", "AC-15", "AC-16",
        "F-01", "F-02", "F-05", "F-08", "F-09", "F-12", "F-13",
    }  # fmt: skip

    def _evaluate(self, obs):
        prev = load(self.PREV / "crown-receipt.json")
        return crown.evaluate(
            REPO / "release" / RELEASE, obs, prev, "68bacd8dcc9ae12e4e97727a284c14abdc7520c5", root=REPO
        )

    @unittest.skipUnless((HIST / "observations.json").is_file(), "tag-time observations not committed")
    def test_tag_time_inputs_refuse_only_unproven_lineage(self):
        verdict = self._evaluate(load(self.HIST / "observations.json"))
        self.assertEqual({code_of(r) for r in verdict.refusals}, {"EVIDENCE_LINEAGE_MISSING"})
        self.assertEqual({r.split(":")[2] for r in verdict.refusals}, self.PRODUCERS)

    @unittest.skipUnless(DELTAS.is_file(), "delta observations not committed")
    def test_tag_time_inputs_with_observed_deltas(self):
        obs = binding.overlay_deltas(load(self.HIST / "observations.json"), load(self.DELTAS))
        verdict = self._evaluate(obs)
        self.assertEqual((verdict.standing, verdict.refusals), ("BLOCKED", ()), verdict.remaining)
        reqs = verdict.receipt["requirements"]
        self.assertEqual({k for k in ("AC-08", "F-05") if reqs[k]["state"] == "PASS"}, {"AC-08", "F-05"})
        unbounded = {rid for rid, r in reqs.items() if r["code"] == "EVIDENCE_DELTA_UNBOUNDED"}
        self.assertEqual(unbounded, self.PRODUCERS - {"AC-08", "F-05"})
        self.assertIn("scripts/release_tlc_court_receipt.py", reqs["AC-07"]["detail"])
        self.assertIn("release/v26.9.25/receipts/replay/origin_probe.exs", reqs["AC-03"]["detail"])
        self.assertIn("release/v26.9.25/receipts/manufacture.py", reqs["AC-13"]["detail"])
        self.assertIn("release/v26.9.25/receipts/godslaw-gate-witness.py", reqs["AC-15"]["detail"])
        # Policy + owner courts refuse nothing on history: the typed dispositions still reach binding.
        self.assertFalse({"OWNER_SPLIT", "BLOCKED_WITHOUT_TYPE", "ARTIFACT_BLOCKED"} & {r["code"] for r in reqs.values()})

if __name__ == "__main__":
    unittest.main()
