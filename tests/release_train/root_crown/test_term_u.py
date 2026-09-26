"""Term U: the root crown evaluates the term set its release premise declares (RFC-0005).

Chicago style: real release trees on disk, the real projector, the real crown and the real
autonomic_crown receipt sealer. ``u_tree`` materializes a v26.9.26-shaped release from the
ALIVE v26.9.25 fixture: the premise declares U, imports RFC-0005 as a premise-set member and
carries one U row whose evidence is the autonomic_crown receipt of that release line.

Falsifiers under test (frontier item chatman-root-crown-term-u-premise-driven-terms):
(a) a U requirement whose autonomic receipt digest does not recompute, or whose subject is
    stale, never passes; (b) the v26.9.25 crown keeps the six-term theorem and receipt;
(c) a premise that declares U (or a release on/after v26.9.26) is never evaluated without U.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import CROWN_SHA, REPO, alive_observations, alive_tree, dump, load

from scripts.release_train.autonomic_crown import receipt as autonomic
from scripts.release_train.root_crown import crown, evidence, projector
from scripts.release_train.root_crown.model import (
    FAILURE_CLASS,
    TERM_REGISTRY,
    TERMS,
    code_of,
    release_terms,
    theorem,
)
from scripts.release_train.root_crown.requirements import validate_requirements

OLD, NEW = "v26.9.25", "v26.9.26"
ROOT_REPO = "seanchatmangpt/chatman-ecosystem"
RECEIPT_PATH = f"release/{NEW}/autonomy/autonomic-receipt.json"
LOCATOR = f"local:{RECEIPT_PATH}"
SUBJECT = hashlib.sha1(b"autonomic-crown-subject").hexdigest()
POLICY_SRC = REPO / "scripts/release_train/root_crown/policy" / OLD
RFC5 = REPO / "release" / OLD / "autonomy/imports/RFC-0005.md"
COMMITTED_AUTONOMIC = REPO / "release" / OLD / "autonomy/autonomic-receipt.json"
U_ROW = {
    "id": "U-01",
    "kind": "AC",
    "term": "U",
    "owner_repo": ROOT_REPO,
    "acceptance": (
        "The autonomic_crown receipt of this release line recomputes, binds the crown subject it "
        "measured to the crown commit, and reports execution ALIVE and autonomy AUTONOMIC (RFC-0005 §2.3, §3)."
    ),
    "evidence_kind": "autonomic_receipt",
    "evidence_locator": LOCATOR,
    "premise_refs": ["RFC-0005§2", "RFC-0005§3"],
    "depends_on": [],
    "required": True,
}


def _swap(value):
    """Re-home release-line paths (release/<v>/, docs/jira/<v>/) onto the new line.

    Other occurrences of the old version (e.g. the RFC-0004 source path, whose file name
    carries its own calver) are premise identity and stay untouched.
    """
    text = json.dumps(value)
    for prefix in ("release/", "docs/jira/"):
        text = text.replace(prefix + OLD, prefix + NEW)
    return json.loads(text)


def pass_gate(gid: str, row: dict) -> dict:
    """A PASS gate row in the autonomic court's shape: evidence digest, no code."""
    return {
        "id": gid,
        "state": "PASS",
        "measured": row.get("threshold"),
        "threshold": row.get("threshold"),
        "detail": "fixture",
        "evidence": {"digest": "sha256:" + hashlib.sha256(f"fixture:{gid}".encode()).hexdigest()},
        "findings": [],
    }


def coherent_blocked_gate(gid: str, row: dict) -> dict:
    """A BLOCKED gate row carrying a typed code (the committed row when it is BLOCKED)."""
    if row.get("state") == "BLOCKED" and row.get("code"):
        return copy.deepcopy(row)
    return {
        "id": gid,
        "state": "BLOCKED",
        "measured": "0",
        "threshold": row.get("threshold"),
        "detail": "fixture",
        "evidence": None,
        "findings": [],
        "code": "HUMAN_OR_LLM_EDGE",
        "failure_class": "CAPABILITY_GAP",
        "broken_term": "mu_on_O",
    }


class UTree:
    """A v26.9.26-shaped release tree plus its policy root and observations."""

    def __init__(self) -> None:
        base = alive_tree()
        obs = alive_observations(base)
        self._base = base
        self.root = base.root
        old_dir = base.release_dir
        self.release_dir = self.root / "release" / NEW
        shutil.move(str(old_dir), str(self.release_dir))
        jira_old, jira_new = self.root / "docs/jira" / OLD, self.root / "docs/jira" / NEW
        shutil.move(str(jira_old), str(jira_new))
        doc = _swap(load(self.release_dir / "requirements.json"))
        doc["release"] = NEW
        shutil.copyfile(RFC5, self.release_dir / "imports/RFC-0005.md")
        doc["terms"]["U"] = "SelfStart AND SelfObserve AND SelfAdmit AND NoHiddenHuman AND NoRepeatedLLM"
        doc["premise"]["set"] = [
            {
                "rfc_id": "RFC-0005",
                "import": "imports/RFC-0005.md",
                "sha256": hashlib.sha256(RFC5.read_bytes()).hexdigest(),
            }
        ]
        doc["requirements"].append(copy.deepcopy(U_ROW))
        self.doc = doc
        dump(self.release_dir / "requirements.json", doc)
        for name in ("closure.json", "pins.json"):
            dump(self.release_dir / name, _swap(load(self.release_dir / name)))
        projector.write(self.release_dir)
        # Terminality policy + delta allowlist for the new line (test data, never committed):
        # the v26.9.25 rows re-hashed over the swapped acceptance text, and the allowlist also
        # admitting the autonomic receipt path as an inert receipt.
        self._policy = tempfile.TemporaryDirectory()
        self.policy_root = Path(self._policy.name)
        target = self.policy_root / NEW
        target.mkdir(parents=True)
        policy = _swap(load(POLICY_SRC / "terminality.json")) | {"release": NEW}
        acceptance = {r["id"]: r["acceptance"] for r in doc["requirements"]}
        for row in policy["rows"]:
            row["acceptance_sha256"] = hashlib.sha256(acceptance[row["id"]].encode("utf-8")).hexdigest()
        dump(target / "terminality.json", policy)
        allow = _swap(load(POLICY_SRC / "delta-allowlist.json")) | {"release": NEW}
        allow["allow"] = allow["allow"] + ["release/*/autonomy/autonomic-receipt.json"]
        dump(target / "delta-allowlist.json", allow)
        self.obs = _swap(obs) | {"release": NEW, "tag": {"name": NEW, "sha": None}}
        self.obs["subjects"][f"{ROOT_REPO}@{SUBJECT}"] = "ahead"
        self.obs.setdefault("subject_deltas", {})[f"{ROOT_REPO}@{SUBJECT}..{CROWN_SHA}"] = [RECEIPT_PATH]

    def cleanup(self) -> None:
        self._base.cleanup()
        self._policy.cleanup()

    def write_receipt(self, blocked=(), **changes) -> dict:
        """A real autonomic_crown receipt for this line, re-sealed by the real sealer.

        The body is coherent: the gate table is total over U-01..U-18, every gate not in
        ``blocked`` is PASS with an evidence digest, every gate in ``blocked`` is BLOCKED
        with the committed receipt's typed code, and ``blocked_gates``/``passed_gates``/
        ``standings.autonomy``/``exit`` are what the autonomic court derives from that table.
        ``changes`` then override any field (forgeries re-sealed by the same sealer).
        """
        body = load(COMMITTED_AUTONOMIC)
        body.pop("receipt_digest")
        gates = {}
        for gid, row in body["gates"].items():
            if gid in blocked:
                gates[gid] = coherent_blocked_gate(gid, row)
            else:
                gates[gid] = pass_gate(gid, row)
        autonomic_ok = not blocked
        body.update(
            {
                "release": NEW,
                "crown_subject": SUBJECT,
                "standings": {
                    "execution": {"state": "ALIVE", "detail": "fixture"},
                    "autonomy": "AUTONOMIC" if autonomic_ok else "NOT_AUTONOMIC",
                    "authority": {"state": "AUTHORIZED", "detail": "fixture"},
                },
                "gates": gates,
                "blocked_gates": sorted(g for g in gates if gates[g]["state"] != "PASS"),
                "passed_gates": sorted(g for g in gates if gates[g]["state"] == "PASS"),
                "exit": 0 if autonomic_ok else 3,
            }
        )
        body.update(changes)
        sealed = autonomic.seal(body, body.get("evaluated_at"))
        dump(self.root / RECEIPT_PATH, sealed)
        return sealed

    def evaluate(self, obs=None):
        return crown.evaluate(
            self.release_dir,
            self.obs if obs is None else obs,
            None,
            CROWN_SHA,
            root=self.root,
            policy_root=self.policy_root,
            allowlist_root=self.policy_root,
        )

    def ctx(self, obs=None) -> evidence.Context:
        return evidence.Context(
            root=self.root,
            release_dir=self.release_dir,
            observations=self.obs if obs is None else obs,
            crown_sha=CROWN_SHA,
            inputs=projector.load_inputs(self.release_dir),
            policy_root=self.policy_root,
            allowlist_root=self.policy_root,
        )

    def u_state(self, obs=None):
        req = next(r for r in projector.load_inputs(self.release_dir).requirements if r.id == "U-01")
        return evidence.autonomic_receipt(req, self.ctx(obs))


class ReleaseTermsTest(unittest.TestCase):
    def test_committed_premise_evaluates_exactly_the_six_terms(self):
        doc = load(REPO / "release" / OLD / "requirements.json")
        self.assertEqual(release_terms(doc), (TERMS, []))
        self.assertEqual(theorem(TERMS), "RELEASE = C AND A AND R AND X AND F AND M")

    def test_premise_without_terms_table_defaults_to_rfc_0004(self):
        self.assertEqual(release_terms({"release": OLD}), (TERMS, []))

    def test_u_declared_before_its_calver_is_refused(self):
        doc = {"release": OLD, "terms": {t: "x" for t in TERM_REGISTRY}}
        terms, refusals = release_terms(doc)
        self.assertEqual(refusals, ["REFUSED:REQ_TERM_UNBOUND:U:premature(binds-from-v26.9.26)"])
        self.assertIn("U", terms)

    def test_premise_omitting_u_from_its_calver_is_refused_and_still_evaluates_u(self):
        # Falsifier (c): a v26.9.26 premise cannot drop U by omission.
        doc = {"release": NEW, "terms": {t: "x" for t in TERMS}}
        terms, refusals = release_terms(doc)
        self.assertEqual(terms, TERM_REGISTRY)
        self.assertEqual(refusals, ["REFUSED:REQ_TERM_UNBOUND:U:required-from-v26.9.26"])
        later = {"release": "v27.1.1", "terms": {t: "x" for t in TERMS}}
        self.assertEqual(release_terms(later)[0], TERM_REGISTRY)

    def test_unknown_term_symbol_is_refused(self):
        doc = {"release": NEW, "terms": {t: "x" for t in TERM_REGISTRY} | {"Z": "x"}}
        terms, refusals = release_terms(doc)
        self.assertEqual(terms, TERM_REGISTRY)
        self.assertEqual(refusals, ["REFUSED:REQ_TERM_UNBOUND:Z:not-in-registry"])

    def test_declared_theorem_orders_by_registry(self):
        doc = {"release": NEW, "terms": {"U": "x"} | {t: "x" for t in reversed(TERMS)}}
        self.assertEqual(theorem(release_terms(doc)[0]), "RELEASE = C AND A AND R AND X AND F AND M AND U")

    def test_every_new_code_is_typed(self):
        for code in (
            "AUTONOMIC_RECEIPT_DIGEST_MISMATCH",
            "AUTONOMIC_STANDING_UNDERIVED",
            "AUTONOMIC_RECEIPT_STALE",
            "AUTONOMIC_NOT_AUTONOMIC",
        ):
            self.assertIn(code, FAILURE_CLASS)


class TermUCrownTest(unittest.TestCase):
    def setUp(self):
        self.tree = UTree()

    def tearDown(self):
        self.tree.cleanup()

    def test_missing_autonomic_evidence_is_typed_blocked_not_alive(self):
        verdict = self.tree.evaluate()
        self.assertEqual(verdict.receipt["theorem"], "RELEASE = C AND A AND R AND X AND F AND M AND U")
        self.assertIn("U", verdict.terms)
        self.assertEqual(verdict.terms["U"], "BLOCKED")
        self.assertEqual(verdict.refusals, ())
        self.assertEqual(verdict.standing, "BLOCKED")
        state = verdict.receipt["requirements"]["U-01"]
        self.assertEqual(state["state"], "BLOCKED")
        self.assertEqual(state["code"], "EVIDENCE_ABSENT")
        self.assertEqual(state["broken_term"], "R_missing_consequence")
        self.assertEqual(state["failure_class"], "EVIDENCE_FAILURE")

    def test_valid_autonomic_receipt_makes_u_pass_and_the_crown_alive(self):
        # Positive control: without it every BLOCKED/REFUSED below would be vacuous.
        self.tree.write_receipt()
        verdict = self.tree.evaluate()
        self.assertEqual(verdict.terms, {t: "PASS" for t in TERM_REGISTRY}, verdict.remaining)
        self.assertEqual(verdict.standing, "ALIVE")
        binding = verdict.receipt["requirements"]["U-01"]["binding"]
        self.assertEqual(binding["evaluated_subject_sha"], SUBJECT)
        self.assertEqual(binding["evidence_container_sha"], CROWN_SHA)
        self.assertEqual(binding["kind"], "LOCAL_RECEIPT")
        self.assertEqual(binding["lineage_proof"]["delta_class"], "RECEIPT_ONLY")
        self.assertEqual(
            binding["evidence_digest"],
            "sha256:" + hashlib.sha256((self.tree.root / RECEIPT_PATH).read_bytes()).hexdigest(),
        )

    def test_tampered_receipt_digest_is_refused(self):
        # Falsifier (a): a receipt whose digest does not recompute never passes.
        sealed = self.tree.write_receipt()
        sealed["standings"]["autonomy"] = "AUTONOMIC"
        sealed["blocked_gates"] = ["U-03"]  # edited after sealing
        dump(self.tree.root / RECEIPT_PATH, sealed)
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("REFUSED", "AUTONOMIC_RECEIPT_DIGEST_MISMATCH"))
        self.assertEqual(state.broken_term, "R_missing_identity")
        self.assertEqual(self.tree.evaluate().standing, "REFUSED")

    def test_foreign_schema_is_refused(self):
        self.tree.write_receipt(schema="https://chatman.dev/root-crown/receipt/v1")
        self.assertEqual(self.tree.u_state().code, "AUTONOMIC_RECEIPT_DIGEST_MISMATCH")

    def test_committed_v26_9_25_receipt_is_never_evidence_of_u(self):
        # RFC-0005 §2.2: no v26.9.25 receipt is reinterpreted as evidence of U.
        (self.tree.root / RECEIPT_PATH).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(COMMITTED_AUTONOMIC, self.tree.root / RECEIPT_PATH)
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("BLOCKED", "AUTONOMIC_RECEIPT_STALE"))
        self.assertEqual(state.broken_term, "R_not_fed_back")

    def test_stale_subject_never_passes(self):
        # Falsifier (a): the measured crown subject must bind to the crown commit.
        self.tree.write_receipt()
        identity = f"{ROOT_REPO}@{SUBJECT}"
        cases = {
            "diverged": ({"subjects": {identity: "diverged"}}, "REFUSED", "EVIDENCE_SUBJECT_SPLIT"),
            "behind": ({"subjects": {identity: "behind"}}, "REFUSED", "EVIDENCE_SUBJECT_SPLIT"),
            "unobserved": ({"subjects": {}}, "REFUSED", "EVIDENCE_LINEAGE_MISSING"),
            "delta-unobserved": ({"subject_deltas": {}}, "REFUSED", "EVIDENCE_LINEAGE_MISSING"),
            "code-in-delta": (
                {"subject_deltas": {f"{identity}..{CROWN_SHA}": [RECEIPT_PATH, "scripts/release_train/x.py"]}},
                "BLOCKED",
                "EVIDENCE_DELTA_UNBOUNDED",
            ),
        }
        for name, (patch, state_name, code) in cases.items():
            with self.subTest(name):
                obs = copy.deepcopy(self.tree.obs)
                for key, value in patch.items():
                    obs[key] = value
                state = self.tree.u_state(obs)
                self.assertEqual((state.state, state.code), (state_name, code), state.detail)
                self.assertIsNotNone(state.broken_term)
                self.assertNotEqual(self.tree.evaluate(obs).standing, "ALIVE")

    def test_subject_that_is_the_crown_commit_or_mutable_is_refused(self):
        for subject, code in ((CROWN_SHA, "EVIDENCE_CONTAINER_CLAIMS_SUBJECT"), ("main", "EVIDENCE_SUBJECT_MUTABLE")):
            with self.subTest(subject=subject):
                self.tree.write_receipt(crown_subject=subject)
                obs = copy.deepcopy(self.tree.obs)
                obs["subjects"][f"{ROOT_REPO}@{subject}"] = "ahead"
                obs["subject_deltas"][f"{ROOT_REPO}@{subject}..{CROWN_SHA}"] = [RECEIPT_PATH]
                state = self.tree.u_state(obs)
                self.assertEqual((state.state, state.code), ("REFUSED", code))

    def test_not_autonomic_receipt_is_typed_blocked(self):
        # RFC-0005 §15: the expected first standing (ALIVE / NOT_AUTONOMIC) keeps U open.
        self.tree.write_receipt(blocked=("U-03", "U-15"))
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("BLOCKED", "AUTONOMIC_NOT_AUTONOMIC"))
        self.assertEqual((state.failure_class, state.broken_term), ("CAPABILITY_GAP", "mu_on_O"))
        self.assertIn("U-03,U-15", state.detail)
        verdict = self.tree.evaluate()
        self.assertEqual((verdict.standing, verdict.terms["U"]), ("BLOCKED", "BLOCKED"))

    def test_autonomic_exit_and_standing_must_agree(self):
        # AUTONOMIC standings with a non-zero exit (or vice versa) is not a witness of U.
        self.tree.write_receipt(exit=3)
        self.assertEqual(self.tree.u_state().code, "AUTONOMIC_NOT_AUTONOMIC")

    def test_refusing_autonomic_court_refuses_u(self):
        self.tree.write_receipt(exit=2)
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("REFUSED", "ARTIFACT_REFUSED"))

    def test_non_json_receipt_is_typed_blocked(self):
        (self.tree.root / RECEIPT_PATH).parent.mkdir(parents=True, exist_ok=True)
        (self.tree.root / RECEIPT_PATH).write_text("not json", encoding="utf-8")
        state = self.tree.u_state()
        self.assertEqual((state.state, state.code), ("BLOCKED", "ARTIFACT_NOT_JSON"))


class PremiseSetAdmissionTest(unittest.TestCase):
    """requirements.validate_requirements over a premise that declares U."""

    def setUp(self):
        self.tree = UTree()
        self.inputs = projector.load_inputs(self.tree.release_dir)

    def tearDown(self):
        self.tree.cleanup()

    def refusals(self, doc=None, premise_set=None):
        return validate_requirements(
            self.inputs.requirements_doc if doc is None else doc,
            self.inputs.pins,
            self.inputs.rfc_text,
            evidence.EVALUATORS,
            self.inputs.premise_set if premise_set is None else premise_set,
        )

    def test_u_premise_is_admitted(self):
        self.assertEqual(self.refusals(), [])
        self.assertEqual(sorted(self.inputs.premise_set), ["RFC-0005"])
        self.assertIn("imports/RFC-0005.md", self.inputs.input_digests)

    def test_u_without_rfc_0005_import_is_refused(self):
        self.assertIn("REFUSED:REQ_PREMISE_UNBOUND:U:RFC-0005-not-imported", self.refusals(premise_set={}))

    def test_rfc_0005_digest_mismatch_is_refused(self):
        tampered = {"RFC-0005": self.inputs.premise_set["RFC-0005"] + "\nedited\n"}
        self.assertIn("REFUSED:REQ_PREMISE_UNBOUND:U:RFC-0005-sha256-mismatch", self.refusals(premise_set=tampered))

    def test_u_row_citing_only_rfc_0004_is_refused(self):
        doc = copy.deepcopy(self.inputs.requirements_doc)
        next(r for r in doc["requirements"] if r["id"] == "U-01")["premise_refs"] = ["§3"]
        self.assertIn("REFUSED:REQ_PREMISE_UNBOUND:U-01:term U cites no RFC-0005 section", self.refusals(doc))

    def test_u_row_citing_absent_rfc_0005_section_is_refused(self):
        doc = copy.deepcopy(self.inputs.requirements_doc)
        next(r for r in doc["requirements"] if r["id"] == "U-01")["premise_refs"] = ["RFC-0005§99"]
        self.assertIn("REFUSED:REQ_PREMISE_UNBOUND:U-01:RFC-0005§99", self.refusals(doc))

    def test_declared_u_without_rows_is_refused(self):
        # Falsifier (c): declaring U and supplying no U requirement cannot pass as six terms.
        doc = copy.deepcopy(self.inputs.requirements_doc)
        doc["requirements"] = [r for r in doc["requirements"] if r["term"] != "U"]
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:U:no-requirement", self.refusals(doc))

    def test_u_row_under_a_six_term_premise_is_refused(self):
        doc = copy.deepcopy(self.inputs.requirements_doc)
        doc["release"] = OLD
        del doc["terms"]["U"]
        codes = self.refusals(doc)
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:U-01:U", codes)

    def test_crown_refuses_a_v26_9_26_premise_that_omits_u(self):
        doc = load(self.tree.release_dir / "requirements.json")
        del doc["terms"]["U"]
        doc["requirements"] = [r for r in doc["requirements"] if r["term"] != "U"]
        dump(self.tree.release_dir / "requirements.json", doc)
        projector.write(self.tree.release_dir)
        verdict = self.tree.evaluate()
        self.assertEqual(verdict.terms["U"], "BLOCKED")
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:U:required-from-v26.9.26", verdict.refusals)
        self.assertIn("REFUSED:REQ_TERM_UNBOUND:U:no-requirement", verdict.refusals)
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertEqual({code_of(r) for r in verdict.refusals} - set(FAILURE_CLASS), set())


if __name__ == "__main__":
    unittest.main()
