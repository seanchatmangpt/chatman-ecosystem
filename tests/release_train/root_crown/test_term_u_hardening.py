"""Term U hardening: adversarial premises and forged-but-sealed autonomic receipts.

Chicago style: the real ``UTree`` release tree (``test_term_u``), the real projector, the
real crown and the real autonomic_crown sealer. Every case below is an input an adversary
(or a careless premise edit) can produce; each must be typed REFUSED/BLOCKED, never PASS,
never a verifier crash. The positive control (``test_term_u``: a valid receipt makes the
crown ALIVE) keeps these non-vacuous; ``test_positive_control_still_alive`` repeats it here.

Guards added by PR #295 hardening (v26.9.26):
- base-term erosion: a premise cannot drop an RFC-0004 term (``base-term-omitted``);
- malformed ``terms`` table: refused, never silently defaulted to the six;
- release relabelling: the term gate reads the crown's release directory, and a premise
  naming another line (or a non-calver line) is refused;
- premise-set shadowing: duplicate members and an RFC-0004 member are refused, and the
  admitted RFC-0004 text always wins in the Berthier sources;
- symlinked premise imports escaping the release tree are unbound;
- forged sealed receipts: ``exit`` false/0.0/"0" and malformed standings are typed
  AUTONOMIC_NOT_AUTONOMIC;
- derived standing (court #295 R_missing_standing): the summary fields ``blocked_gates``,
  ``passed_gates`` and ``standings.autonomy`` must re-derive from the receipt's own sealed
  gate table (total, typed, PASS evidence-backed), else AUTONOMIC_STANDING_UNDERIVED;
- replay/duplicate/reorder: a re-delivered identical receipt is idempotent, and a
  receipt from an earlier evaluation of another subject never passes;
- the v26.9.25 tag-time mutation report is immutable history (pinned bytes).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from _support import CROWN_SHA, REPO, dump, load
from test_term_u import (
    COMMITTED_AUTONOMIC,
    NEW,
    OLD,
    RECEIPT_PATH,
    ROOT_REPO,
    SUBJECT,
    UTree,
    coherent_blocked_gate,
)

from scripts.release_train.autonomic_crown import receipt as autonomic
from scripts.release_train.root_crown import berthier, crown, evidence, mutate, projector
from scripts.release_train.root_crown.model import FAILURE_CLASS, TERM_REGISTRY, TERMS, code_of, release_terms
from scripts.release_train.root_crown.requirements import validate_requirements

# sha256 of release/v26.9.25/hardening/inputs/mutation-report.json as merged on main at
# c8dd167a (the post-tag record attestation/final read). release/v26.9.25 is immutable.
FROZEN_REPORT_SHA256 = "262dc4cad6130cf3d3edf3646db962c4605892c02b8261db86de5467a666d563"


class PremiseErosionTest(unittest.TestCase):
    def test_dropping_a_base_term_is_refused_and_the_term_still_evaluated(self):
        for dropped in TERMS:
            with self.subTest(dropped=dropped):
                doc = {"release": NEW, "terms": {t: "x" for t in TERM_REGISTRY if t != dropped}}
                terms, refusals = release_terms(doc)
                self.assertEqual(terms, TERM_REGISTRY)
                self.assertEqual(refusals, [f"REFUSED:REQ_TERM_UNBOUND:{dropped}:base-term-omitted"])

    def test_u_only_premise_cannot_replace_the_six(self):
        terms, refusals = release_terms({"release": NEW, "terms": {"U": "x"}})
        self.assertEqual(terms, TERM_REGISTRY)
        self.assertEqual(len(refusals), len(TERMS))

    def test_malformed_terms_table_is_refused_not_defaulted(self):
        for bad in ([], ["C", "A", "R", "X", "F", "M", "U"], {}, "C A R X F M", None, 7):
            with self.subTest(terms=bad):
                terms, refusals = release_terms({"release": OLD, "terms": bad})
                self.assertIn("REFUSED:REQ_MALFORMED:terms:not-a-non-empty-object", refusals)
                self.assertEqual(terms, TERMS)

    def test_relabelled_premise_cannot_evade_u(self):
        # A v26.9.26 crown whose premise claims v26.9.25 is refused and still evaluates U.
        terms, refusals = release_terms({"release": OLD, "terms": {t: "x" for t in TERMS}}, NEW)
        self.assertEqual(terms, TERM_REGISTRY)
        self.assertIn(f"REFUSED:REQ_MALFORMED:release:premise-names-{OLD}-for-{NEW}", refusals)
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:U:required-from-v26.9.26", refusals)

    def test_non_calver_line_is_refused(self):
        for line in ("v26.9.26-rc1", "next", "26.9.26", ""):
            with self.subTest(line=line):
                _, refusals = release_terms({"release": line, "terms": {t: "x" for t in TERMS}})
                self.assertIn(f"REFUSED:REQ_MALFORMED:release:not-calver:{line}", refusals)

    def test_every_hardening_code_is_typed(self):
        docs = [
            {"release": NEW, "terms": {"U": "x"}},
            {"release": "next", "terms": []},
            {"release": OLD, "terms": {t: "x" for t in TERMS}},
        ]
        codes = {code_of(r) for d in docs for r in release_terms(d, NEW)[1]}
        self.assertEqual(codes - set(FAILURE_CLASS), set())
        self.assertEqual(codes, {"REQ_TERM_UNBOUND", "REQ_MALFORMED"})


class CrownRelabelTest(unittest.TestCase):
    def setUp(self):
        self.tree = UTree()

    def tearDown(self):
        self.tree.cleanup()

    def test_positive_control_still_alive(self):
        self.tree.write_receipt()
        verdict = self.tree.evaluate()
        self.assertEqual(verdict.standing, "ALIVE", verdict.remaining)

    def test_crown_reads_the_directory_line_not_the_premise_label(self):
        doc = load(self.tree.release_dir / "requirements.json")
        doc["release"] = OLD
        del doc["terms"]["U"]
        doc["requirements"] = [r for r in doc["requirements"] if r["term"] != "U"]
        del doc["premise"]["set"]
        dump(self.tree.release_dir / "requirements.json", doc)
        projector.write(self.tree.release_dir)
        verdict = self.tree.evaluate()
        self.assertIn("U", verdict.terms)
        self.assertEqual(verdict.terms["U"], "BLOCKED")
        self.assertIn(f"REFUSED:REQ_MALFORMED:release:premise-names-{OLD}-for-{NEW}", verdict.refusals)
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:U:required-from-v26.9.26", verdict.refusals)
        self.assertEqual(verdict.standing, "REFUSED")


class PremiseSetShadowTest(unittest.TestCase):
    def setUp(self):
        self.tree = UTree()
        self.inputs = projector.load_inputs(self.tree.release_dir)

    def tearDown(self):
        self.tree.cleanup()

    def refusals(self, doc, premise_set=None):
        return validate_requirements(
            doc,
            self.inputs.pins,
            self.inputs.rfc_text,
            evidence.EVALUATORS,
            self.inputs.premise_set if premise_set is None else premise_set,
            release=NEW,
        )

    def test_duplicate_set_member_is_refused(self):
        doc = copy.deepcopy(self.inputs.requirements_doc)
        doc["premise"]["set"] = [{"rfc_id": "RFC-0005", "import": "imports/absent.md", "sha256": "0" * 64}] + doc[
            "premise"
        ]["set"]
        self.assertIn("REFUSED:REQ_PREMISE_UNBOUND:RFC-0005:duplicate-set-member", self.refusals(doc))

    def test_primary_premise_in_set_is_refused_and_never_replaces_it(self):
        doc = load(self.tree.release_dir / "requirements.json")
        forged = self.tree.release_dir / "imports/RFC-0004-forged.md"
        forged.write_text("# forged\n\n## 3. nothing\n", encoding="utf-8")
        doc["premise"]["set"].append(
            {
                "rfc_id": "RFC-0004",
                "import": "imports/RFC-0004-forged.md",
                "sha256": hashlib.sha256(forged.read_bytes()).hexdigest(),
            }
        )
        dump(self.tree.release_dir / "requirements.json", doc)
        inputs = projector.load_inputs(self.tree.release_dir)
        self.assertIn(
            "REFUSED:REQ_PREMISE_UNBOUND:RFC-0004:primary-premise-in-set",
            validate_requirements(
                inputs.requirements_doc, inputs.pins, inputs.rfc_text, evidence.EVALUATORS, inputs.premise_set, release=NEW
            ),
        )
        # The admitted RFC-0004 text wins in the Berthier sources.
        self.assertEqual(projector.premise_input(inputs)[berthier.PREMISE], inputs.rfc_text)

    def test_symlinked_import_escaping_the_tree_is_unbound(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "RFC-0005.md"
            target.write_bytes((self.tree.release_dir / "imports/RFC-0005.md").read_bytes())
            link = self.tree.release_dir / "imports/RFC-0005.md"
            link.unlink()
            os.symlink(target, link)
            inputs = projector.load_inputs(self.tree.release_dir)
            self.assertEqual(inputs.premise_set, {})
            self.assertIn(
                "REFUSED:REQ_PREMISE_UNBOUND:U:RFC-0005-not-imported",
                validate_requirements(
                    inputs.requirements_doc,
                    inputs.pins,
                    inputs.rfc_text,
                    evidence.EVALUATORS,
                    inputs.premise_set,
                    release=NEW,
                ),
            )

    def test_traversal_and_absolute_imports_are_unbound(self):
        for rel in ("../v26.9.25/imports/RFC-0004.md", "/etc/hosts", "", 5):
            with self.subTest(rel=rel):
                doc = load(self.tree.release_dir / "requirements.json")
                doc["premise"]["set"][0]["import"] = rel
                dump(self.tree.release_dir / "requirements.json", doc)
                self.assertEqual(projector.load_inputs(self.tree.release_dir).premise_set, {})


class ForgedReceiptTest(unittest.TestCase):
    """Receipts re-sealed by an adversary: the digest recomputes, the content lies."""

    def setUp(self):
        self.tree = UTree()

    def tearDown(self):
        self.tree.cleanup()

    def assert_not_autonomic(self, **changes):
        self.tree.write_receipt(**changes)
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("BLOCKED", "AUTONOMIC_NOT_AUTONOMIC"), state.detail)
        self.assertNotEqual(self.tree.evaluate().standing, "ALIVE")

    def test_exit_that_merely_equals_zero_is_not_a_witness(self):
        for value in (False, 0.0, "0", None, [0]):
            with self.subTest(exit=value):
                self.assert_not_autonomic(exit=value)

    def test_exit_true_or_two_point_zero_never_passes(self):
        for value in (True, 2.0):
            with self.subTest(exit=value):
                self.assert_not_autonomic(exit=value)

    def test_autonomic_with_blocked_gates_is_contradictory(self):
        # The summary list disagrees with the (all-PASS) gate table it summarizes.
        for gates in (["U-03"], None, "U-03", {"U-03": 1}, [1]):
            with self.subTest(blocked_gates=gates):
                self.tree.write_receipt(blocked_gates=gates)
                state = self.tree.u_state()
                self.assertEqual((state.state, state.code), ("REFUSED", "AUTONOMIC_STANDING_UNDERIVED"), state.detail)
                self.assertNotEqual(self.tree.evaluate().standing, "ALIVE")

    def test_malformed_standings_are_typed_not_crashes(self):
        for standings in (
            None,
            [],
            "AUTONOMIC",
            {"execution": "ALIVE", "autonomy": "AUTONOMIC"},
            {"execution": {"state": "ALIVE"}, "autonomy": "autonomic"},
            {"execution": {"state": "UNKNOWN"}, "autonomy": "AUTONOMIC"},
        ):
            with self.subTest(standings=standings):
                self.tree.write_receipt(standings=standings)
                state = self.tree.u_state()
                self.assertIn(state.state, ("BLOCKED", "REFUSED"), state.detail)
                self.assertIn(state.code, FAILURE_CLASS)
                self.assertNotEqual(self.tree.evaluate().standing, "ALIVE")

    def test_non_string_subject_is_refused(self):
        for subject in (None, 40, "C" * 40, SUBJECT[:39], SUBJECT + "0"):
            with self.subTest(subject=subject):
                self.tree.write_receipt(crown_subject=subject)
                state = self.tree.u_state()
                self.assertIn(state.state, ("BLOCKED", "REFUSED"), state.detail)
                self.assertNotEqual(self.tree.evaluate().standing, "ALIVE")

    def test_receipt_with_no_release_or_foreign_release_is_stale(self):
        for release in (None, OLD, "v26.9.27", ""):
            with self.subTest(release=release):
                self.tree.write_receipt(release=release)
                self.assertEqual(self.tree.u_state().code, "AUTONOMIC_RECEIPT_STALE")

    def test_non_object_json_receipt_is_typed(self):
        for body in ([], "receipt", 0, None):
            with self.subTest(body=body):
                dump(self.tree.root / RECEIPT_PATH, body)
                self.assertEqual(self.tree.u_state().code, "ARTIFACT_NOT_JSON")

    def test_unsealed_digest_forms_are_refused(self):
        sealed = self.tree.write_receipt()
        for digest_value in (None, "", sealed["receipt_digest"].upper(), sealed["receipt_digest"][7:]):
            with self.subTest(receipt_digest=digest_value):
                forged = dict(sealed, receipt_digest=digest_value)
                dump(self.tree.root / RECEIPT_PATH, forged)
                self.assertEqual(self.tree.u_state().code, "AUTONOMIC_RECEIPT_DIGEST_MISMATCH")


class DerivedStandingTest(unittest.TestCase):
    """Sealed receipts whose summary standing contradicts their own gate table (court #295)."""

    def setUp(self):
        self.tree = UTree()
        self.gate_ids = sorted(load(COMMITTED_AUTONOMIC)["gates"])

    def tearDown(self):
        self.tree.cleanup()

    def assert_underived(self, sealed=None, **changes):
        if sealed is None:
            self.tree.write_receipt(**changes)
        else:
            dump(self.tree.root / RECEIPT_PATH, autonomic.seal(sealed, sealed.get("evaluated_at")))
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("REFUSED", "AUTONOMIC_STANDING_UNDERIVED"), state.detail)
        self.assertEqual((state.failure_class, state.broken_term), ("VERIFICATION_FAILURE", "R_missing_standing"))
        verdict = self.tree.evaluate()
        self.assertNotEqual(verdict.standing, "ALIVE")
        self.assertNotEqual(verdict.terms["U"], "PASS")
        return state

    def body(self, **kwargs):
        sealed = self.tree.write_receipt(**kwargs)
        sealed.pop("receipt_digest")
        return sealed

    def test_positive_control_gate_table_is_all_pass(self):
        sealed = self.tree.write_receipt()
        self.assertEqual(evidence.derive_autonomic_standing(sealed)[1], [])
        self.assertEqual(sealed["passed_gates"], self.gate_ids)
        self.assertEqual(self.tree.u_state().state, "PASS")

    def test_committed_producer_receipt_re_derives(self):
        # Anti-vacuity: the real autonomic court's committed output is coherent under the
        # derivation, so the refusals below are about contradiction, not shape.
        derived, gaps = evidence.derive_autonomic_standing(load(COMMITTED_AUTONOMIC))
        self.assertEqual(gaps, [])
        self.assertEqual(derived["autonomy"], "NOT_AUTONOMIC")
        self.assertEqual(len(derived["blocked_gates"]), 14)

    def test_a1_empty_passed_gates_with_blocked_table(self):
        # Court A1: summary AUTONOMIC/[] over a table with 14 of 18 gates BLOCKED.
        body = self.body()
        body["gates"] = load(COMMITTED_AUTONOMIC)["gates"]
        body["passed_gates"] = []
        self.assert_underived(body)

    def test_a2_every_gate_blocked_under_autonomic_summary(self):
        # Court A2: all 18 gates BLOCKED while the summary says AUTONOMIC with no blocked gate.
        body = self.body()
        body["gates"] = {g: coherent_blocked_gate(g, row) for g, row in body["gates"].items()}
        self.assert_underived(body)

    def test_one_blocked_gate_hidden_by_the_summary(self):
        for gid in (self.gate_ids[0], self.gate_ids[-1]):
            with self.subTest(gate=gid):
                body = self.body()
                body["gates"][gid] = coherent_blocked_gate(gid, body["gates"][gid])
                self.assert_underived(body)

    def test_passed_gates_summary_must_match(self):
        for passed in ([], self.gate_ids[:-1], self.gate_ids + ["U-19"], list(reversed(self.gate_ids)), None):
            with self.subTest(passed=passed):
                self.assert_underived(passed_gates=passed)

    def test_not_autonomic_summary_over_all_pass_table_is_underived(self):
        # Under-claiming is also stored standing: the court would have said AUTONOMIC.
        self.assert_underived(
            standings={
                "execution": {"state": "ALIVE"},
                "autonomy": "NOT_AUTONOMIC",
                "authority": {"state": "AUTHORIZED"},
            }
        )

    def test_pass_without_evidence_digest_is_underived(self):
        for evidence_value in (None, {}, {"digest": "sha256:short"}, {"digest": 7}):
            with self.subTest(evidence=evidence_value):
                body = self.body()
                body["gates"][self.gate_ids[2]]["evidence"] = evidence_value
                self.assert_underived(body)

    def test_blocked_gate_without_typed_code_is_underived(self):
        body = self.body(blocked=(self.gate_ids[4],))
        body["gates"][self.gate_ids[4]]["code"] = "NOT_A_CODE"
        self.assert_underived(body)

    def test_incomplete_extra_or_mislabelled_gate_table_is_underived(self):
        cases = {
            "missing": lambda g: g.pop("U-18"),
            "extra": lambda g: g.update({"U-19": dict(g["U-01"], id="U-19")}),
            "relabelled": lambda g: g["U-01"].update({"id": "U-02"}),
            "non-object-row": lambda g: g.update({"U-01": "PASS"}),
            "unknown-state": lambda g: g["U-01"].update({"state": "pass"}),
        }
        for name, edit in cases.items():
            with self.subTest(case=name):
                body = self.body()
                edit(body["gates"])
                self.assert_underived(body)

    def test_non_object_gate_table_is_underived(self):
        for gates in (None, [], "U-01..U-18 PASS", 18):
            with self.subTest(gates=gates):
                self.assert_underived(gates=gates)

    def test_coherent_not_autonomic_receipt_stays_typed_blocked(self):
        self.tree.write_receipt(blocked=(self.gate_ids[0],))
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("BLOCKED", "AUTONOMIC_NOT_AUTONOMIC"), state.detail)
        self.assertIn(self.gate_ids[0], state.detail)


class ReplayTest(unittest.TestCase):
    def setUp(self):
        self.tree = UTree()

    def tearDown(self):
        self.tree.cleanup()

    def test_duplicate_delivery_is_idempotent(self):
        # Re-delivering the identical receipt bytes (at-least-once transport) yields the
        # byte-identical crown receipt: no state accumulates across evaluations.
        self.tree.write_receipt()
        first = self.tree.evaluate().receipt
        raw = (self.tree.root / RECEIPT_PATH).read_bytes()
        (self.tree.root / RECEIPT_PATH).write_bytes(raw)
        second = self.tree.evaluate().receipt
        self.assertEqual(first["receipt_digest"], second["receipt_digest"])
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_reordered_delivery_of_an_older_subject_never_passes(self):
        # An older evaluation (earlier evaluated_at, another crown subject) delivered after
        # the current one is judged on its own subject, never on arrival order.
        older_subject = hashlib.sha1(b"older-autonomic-subject").hexdigest()
        self.tree.write_receipt(crown_subject=older_subject, evaluated_at="2026-09-25T00:00:00Z")
        state = self.tree.u_state()
        self.assertEqual(state.state, "REFUSED")
        self.assertEqual(state.code, "EVIDENCE_LINEAGE_MISSING")

    def test_crown_receipt_replays_byte_identically(self):
        self.tree.write_receipt()
        verdict = self.tree.evaluate()
        replay = crown.evaluate(
            self.tree.release_dir,
            copy.deepcopy(self.tree.obs),
            None,
            CROWN_SHA,
            root=self.tree.root,
            policy_root=self.tree.policy_root,
            allowlist_root=self.tree.policy_root,
        )
        self.assertEqual(verdict.receipt["receipt_digest"], replay.receipt["receipt_digest"])
        self.assertTrue(crown.verify_receipt(verdict.receipt))


class ImmutableReleaseTest(unittest.TestCase):
    def test_live_mutation_report_is_outside_every_release_line(self):
        self.assertFalse(mutate.REPORT.startswith("release/"), mutate.REPORT)
        self.assertEqual(mutate.FROZEN_REPORT, f"release/{OLD}/hardening/inputs/mutation-report.json")

    def test_v26_9_25_tag_time_mutation_report_is_byte_frozen(self):
        path = REPO / mutate.FROZEN_REPORT
        if not path.is_file():
            self.skipTest(f"{mutate.FROZEN_REPORT} not materialized")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), FROZEN_REPORT_SHA256)

    def test_committed_premise_is_unchanged_by_hardening(self):
        doc = load(REPO / "release" / OLD / "requirements.json")
        self.assertEqual(release_terms(doc, OLD), (TERMS, []))


if __name__ == "__main__":
    unittest.main()
