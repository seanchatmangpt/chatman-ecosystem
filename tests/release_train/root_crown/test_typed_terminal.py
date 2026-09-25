"""Typed terminal dispositions: the five audit survivors, each killed by a named test.

RFC-0004 §38 lists the terminal dispositions FINAL | SUPERSEDED(successor) | BLOCKED(reason) |
UNSUPPORTED(capability_gap) | REFUSED(type); §39 requires every failure to be typed; §36
names an owner. ``evidence.typing_gaps`` enforces type, broken_term, §39 class, owner and
successor. The v26.9.25 audit found five mutants of that code that no test killed
(owner_off, successor_off, type_off, terminal_accepts_partial,
typed_terminal_blocked_as_capability); ``scripts/release_train/root_crown/mutate.py`` names
this module as their killer.

Chicago style: the real release tree (``alive_tree``), real observations, the real
evaluators and the real post-tag court over the committed hardening bytes; every test
changes one real input and asserts on the returned state.
"""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import CROWN_SHA, REPO, RELEASE, alive_observations, alive_tree, committed_tree, dump

from scripts.release_train.root_crown import evidence, gitobj, posttag
from scripts.release_train.root_crown.model import Requirement, code_of

TYPED = "AUTHORITY_FAILURE:operator-repo-rename;R_missing_authority"
HARDENING = REPO / "release" / RELEASE / "hardening"
LOCAL_RECEIPT = f"release/{RELEASE}/observations/terminal-disposition.json"


class TypedTerminalReceiptTest(unittest.TestCase):
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

    def ac15(self, **fields):
        req = next(r for r in self.tree.inputs().requirements if r.id == "AC-15")
        obs = copy.deepcopy(self.obs)
        artifact = obs["artifacts"][req.evidence_locator]["json"]
        for key, value in fields.items():
            if value is None:
                artifact.pop(key, None)
            else:
                artifact[key] = value
        return evidence.receipt_artifact(req, self.ctx(obs))

    # --- owner_off ---------------------------------------------------------------------------
    def local_terminal(self, **fields):
        """A terminal AC whose receipt lives in the crown tree and whose row names no owner repo."""
        req = Requirement("AC-15", "AC", "C", "", "has a terminal standing", "receipt_artifact", f"local:{LOCAL_RECEIPT}", ())
        dump(self.tree.root / LOCAL_RECEIPT, {"standing": "BLOCKED", "type": TYPED} | fields)
        return evidence.receipt_artifact(req, self.ctx())

    def test_local_terminal_receipt_without_owner_is_refused(self):
        state = self.local_terminal()
        self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))
        self.assertTrue(state.detail.endswith(":BLOCKED:missing=owner"), state.detail)

    def test_local_terminal_receipt_with_owner_is_terminal(self):
        state = self.local_terminal(owner="seanchatmangpt/zoela")
        self.assertEqual(state.state, "PASS", state.detail)
        self.assertIn("terminal BLOCKED", state.detail)

    def test_typing_gaps_names_a_blank_owner(self):
        for owner in (None, "", "  "):
            with self.subTest(owner=owner):
                self.assertEqual(evidence.typing_gaps({}, "BLOCKED", type_text=TYPED, owner=owner), ["owner"])

    # --- successor_off -----------------------------------------------------------------------
    def test_superseded_without_successor_is_refused(self):
        state = self.ac15(standing="SUPERSEDED", type=TYPED)
        self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))
        self.assertTrue(state.detail.endswith(":SUPERSEDED:missing=successor"), state.detail)

    def test_superseded_with_successor_is_terminal(self):
        state = self.ac15(standing="SUPERSEDED", type=TYPED, successor={"sha": "f" * 40})
        self.assertEqual(state.state, "PASS", state.detail)
        self.assertIn("terminal SUPERSEDED", state.detail)

    # --- type_off ----------------------------------------------------------------------------
    def test_typed_row_without_type_text_is_refused(self):
        """broken_term and §39 class as explicit fields do not replace the BLOCKED(reason) itself."""
        state = self.ac15(standing="BLOCKED", broken_term="R_missing_authority", failure_class="AUTHORITY_FAILURE")
        self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))
        self.assertTrue(state.detail.endswith(":BLOCKED:missing=type"), state.detail)

    # --- broken_term / failure_class, one gap at a time --------------------------------------
    def test_each_missing_typing_field_is_named_alone(self):
        cases = {
            "broken_term": "AUTHORITY_FAILURE:operator-repo-rename",
            "failure_class": "operator-repo-rename;R_missing_authority",
        }
        for gap, type_text in cases.items():
            with self.subTest(gap=gap):
                state = self.ac15(standing="BLOCKED", type=type_text)
                self.assertEqual((state.state, state.code), ("REFUSED", "BLOCKED_WITHOUT_TYPE"))
                self.assertTrue(state.detail.endswith(f":BLOCKED:missing={gap}"), state.detail)

    # --- terminal_accepts_partial ------------------------------------------------------------
    def test_partial_alive_receipt_is_not_terminal(self):
        """RFC §38: PARTIAL_ALIVE is not a disposition; AC-15 stays BLOCKED, never PASS."""
        state = self.ac15(standing="PARTIAL_ALIVE")
        self.assertEqual((state.state, state.code), ("BLOCKED", "ARTIFACT_BLOCKED"))
        self.assertIn("not terminal", state.detail)

    # --- typed_terminal_blocked_as_capability ------------------------------------------------
    def test_typed_planned_receipt_is_not_terminal(self):
        """A fully typed PLANNED receipt is still not one of the §38 dispositions."""
        state = self.ac15(standing="PLANNED", type=TYPED, broken_term="R_missing_authority")
        self.assertEqual((state.state, state.code), ("BLOCKED", "ARTIFACT_BLOCKED"))
        self.assertIn("PLANNED", state.detail)

    # --- worktree freshness (AC-09) ----------------------------------------------------------
    def test_stale_worktree_observation_is_typed_blocked(self):
        obs = copy.deepcopy(self.obs)
        obs["local_worktrees"]["observed_at"] = "2026-09-24T12:59:59Z"
        req = next(r for r in self.tree.inputs().requirements if r.id == "AC-09")
        state = evidence.worktree_observation(req, self.ctx(obs))
        self.assertEqual((state.state, state.code), ("BLOCKED", "OBSERVATION_STALE"))
        self.assertEqual(evidence.worktree_observation(req, self.ctx()).state, "PASS")


@unittest.skipUnless((HARDENING / "TAG-SUBJECT.json").is_file(), "hardening/TAG-SUBJECT.json not committed")
class RecordBindingTest(unittest.TestCase):
    """The committed TAG-SUBJECT.json record must recompute from raw objects on its own."""

    def setUp(self):
        self.tree = committed_tree()
        self.hardening = self.tree.release_dir / "hardening"
        shutil.copytree(HARDENING, self.hardening)
        self.record = posttag.load_record(self.hardening)

    def tearDown(self):
        self.tree.cleanup()

    def refusal_codes(self, record):
        refusals, _ = posttag.verify_tag_subject(record, self.hardening, [])
        return {code_of(r) for r in refusals}

    def test_committed_record_recomputes(self):
        self.assertEqual(self.refusal_codes(self.record), set())

    def test_edited_record_sections_are_refused(self):
        edits = {
            "TAG_SUBJECT_SPLIT": ("subject", "tree_sha", "0" * 40),
            "TAG_RECEIPT_SPLIT": ("tag_receipt", "observations_digest", "sha256:" + "0" * 64),
            "TAG_MUTATED": ("tag", "tagger", "someone else"),
        }
        for code, (section, key, value) in edits.items():
            with self.subTest(code=code):
                record = copy.deepcopy(self.record)
                record[section][key] = value
                self.assertEqual(self.refusal_codes(record), {code})

    def test_historical_replay_refuses_a_record_naming_another_receipt(self):
        record = copy.deepcopy(self.record)
        record["tag_receipt"]["receipt_digest"] = "sha256:" + "0" * 64
        historical = posttag.historical_standing(record, self.hardening, None, self.tree.root)
        self.assertEqual(historical["standing"], "REFUSED")
        self.assertIn("TAG_RECEIPT_SPLIT", {code_of(r) for r in historical["refusals"]})
        clean = posttag.historical_standing(self.record, self.hardening, None, self.tree.root)
        self.assertEqual(clean["refusals"], [])


class SubjectTreeTest(unittest.TestCase):
    """verify_subject_tree over a real directory whose recorded tree id is computed by gitobj."""

    def test_one_changed_byte_is_subject_tree_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "release" / RELEASE).mkdir(parents=True)
            (root / "release" / RELEASE / "pins.json").write_text(json.dumps({"repos": {}}) + "\n")
            record = {"subject": {"paths": {f"release/{RELEASE}": gitobj.tree_sha_of_dir(root / "release" / RELEASE)}}}
            self.assertEqual(posttag.verify_subject_tree(root, record), [])
            (root / "release" / RELEASE / "pins.json").write_text(json.dumps({"repos": {}}) + " \n")
            refusals = posttag.verify_subject_tree(root, record)
        self.assertEqual([code_of(r) for r in refusals], ["SUBJECT_TREE_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
