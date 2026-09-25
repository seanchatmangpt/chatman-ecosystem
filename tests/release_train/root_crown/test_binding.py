"""Evidence binding (PR-4): every PASS names its evaluated subject, durable container and lineage.

Chicago style: the real binding court, the real committed delta allowlist, the real
observed delta observations (hardening/inputs/delta-observations.json, written by
``observe_release_heads.py --post-tag-bindings``) and the real crown over the ALIVE fixture.

Falsifier fixtures: the three paths named by the frontier of
origin/feat/v26.9.25-receipt-descendant-admission (beb7bc2dc3891544889314d39db302bdff8068d4,
release/v26.9.25/observations/ecosystem-closure-ledger.json ``frontier.falsifiers``):
ggen_igniter ``receipts/replay/origin_probe.exs``, xaas ``receipts/manufacture.py`` and
autofde-lab ``scripts/release_tlc_court_receipt.py``. That branch is cited, not merged.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
import unittest
from dataclasses import replace

from _support import CROWN_SHA, REPO, RELEASE, alive_observations, alive_tree, producer_sha

from scripts.release_train.root_crown import binding, crown, evidence
from scripts.release_train.root_crown.model import (
    BINDING_BLOCKERS,
    BINDING_RULES,
    FAILURE_CLASS,
    EvidenceBinding,
    digest,
)

ALLOWLIST = binding.load_allowlist(RELEASE)
DELTAS = REPO / "release" / RELEASE / "hardening/inputs/delta-observations.json"
FALSIFIERS = {
    "seanchatmangpt/ggen_igniter": "release/v26.9.25/receipts/replay/origin_probe.exs",
    "seanchatmangpt/xaas": "release/v26.9.25/receipts/manufacture.py",
    "seanchatmangpt/autofde-lab": "scripts/release_tlc_court_receipt.py",
}
ROOT_REPO = "seanchatmangpt/chatman-ecosystem"
P, H = "1" * 40, "2" * 40  # producer subject, container head


def receipt_binding(**fields) -> EvidenceBinding:
    base = EvidenceBinding(
        requirement_id="AC-07",
        kind="REMOTE_RECEIPT",
        evaluated_subject_sha=P,
        evaluated_subject_kind="producer_commit",
        container_repository="seanchatmangpt/autofde-lab",
        evidence_container_sha=H,
        evidence_locator=f"git:seanchatmangpt/autofde-lab@{H}:release/v26.9.25/receipts/tlc-court.json",
        evidence_digest="sha256:" + hashlib.sha256(b"{}").hexdigest(),
        producer="seanchatmangpt/autofde-lab",
        court="tlc",
        command=None,
        exit_code=0,
        toolchain=None,
        standing="ALIVE",
        owner="seanchatmangpt/autofde-lab",
        owner_source="container",
        lineage_proof={
            "status": "ahead",
            "delta_paths": ["release/v26.9.25/receipts/tlc-court.json"],
            "delta_class": "RECEIPT_ONLY",
        },
    )
    return replace(base, **fields).sealed()


def admit(b: EvidenceBinding, content: bytes | None = None):
    return binding.admit(b, crown_sha=CROWN_SHA, root_repository=ROOT_REPO, allowlist=ALLOWLIST, content=content)


class LocatorTest(unittest.TestCase):
    def test_durable_grammar(self):
        good = [
            f"git:seanchatmangpt/xaas@{P}:release/v26.9.25/receipts/cloud-runtime.json",
            f"git-notes:refs/notes/receipts@{P}",
            "https://github.com/seanchatmangpt/xaas/actions/runs/1",
        ]
        bad = [
            None,
            "scratchpad/v26925/act/receipts/x.json",
            "/tmp/x.json",
            "~/.claude/x.json",
            "local:release/v26.9.25/closure.json",
            "seanchatmangpt/xaas:release/v26.9.25/receipts/cloud-runtime.json",
            f"git:seanchatmangpt/xaas@{P[:8]}:a.json",
            f"git:seanchatmangpt/xaas@main:a.json",
            f"git:seanchatmangpt/xaas@{P}:/etc/passwd",
            f"git:seanchatmangpt/xaas@{P}:release/../../x.json",
            "http://example.com/x",
        ]
        self.assertEqual([g for g in good if not binding.is_durable(g)], [])
        self.assertEqual([b for b in bad if binding.is_durable(b)], [])


class ClassifyDeltaTest(unittest.TestCase):
    def test_committed_allowlist_admits_only_receipt_json(self):
        self.assertEqual(ALLOWLIST["allow"], ["release/*/receipts/**.json"])

    def test_falsifier_paths_are_unbounded(self):
        for repo, path in FALSIFIERS.items():
            with self.subTest(repo=repo):
                cls, offending = binding.classify_delta(["release/v26.9.25/receipts/x.json", path], ALLOWLIST)
                self.assertEqual((cls, offending), ("UNBOUNDED", [path]))

    def test_classes(self):
        table = [
            (None, None),
            ([], "EMPTY"),
            (["release/v26.9.25/receipts/brce-ledger.json"], "RECEIPT_ONLY"),
            (["release/v26.9.25/receipts/replay/origin-probe.out.json"], "RECEIPT_ONLY"),
            (["release/v26.9.25/receipts/../../scripts/x.json"], "UNBOUNDED"),
            (["release/v26.9.25/receipts/../../ci/x.json"], "UNBOUNDED"),
            (["/release/v26.9.25/receipts/a.json"], "UNBOUNDED"),
            (["release/v26.9.25/receipts/schemas/a.json"], "UNBOUNDED"),
            (["release/v26.9.25/manifest.toml"], "UNBOUNDED"),
            (["release/v26.9.25/receipts/a.yml"], "UNBOUNDED"),
            (["release/v26.9.25/receipts.json"], "UNBOUNDED"),
            ([".github/workflows/root-crown.yml"], "UNBOUNDED"),
            (["release/v26.9.25/nested/receipts/a.json"], "UNBOUNDED"),
            (["release/receipts/a.json"], "UNBOUNDED"),
            (["README.md"], "UNBOUNDED"),
        ]
        for paths, expected in table:
            with self.subTest(paths=paths):
                self.assertEqual(binding.classify_delta(paths, ALLOWLIST)[0], expected)

    def test_deny_lists_outrank_a_broadened_allow_glob(self):
        broad = dict(ALLOWLIST, allow=["release/*/receipts/**"])
        for path in FALSIFIERS.values():
            if path.startswith("release/"):
                with self.subTest(path=path):
                    self.assertEqual(binding.classify_delta([path], broad), ("UNBOUNDED", [path]))
        self.assertEqual(binding.classify_delta(["release/v26.9.25/receipts/x.json"], broad)[0], "RECEIPT_ONLY")

    def test_empty_allowlist_fails_closed(self):
        self.assertEqual(binding.classify_delta(["release/v26.9.25/receipts/a.json"], {})[0], "UNBOUNDED")

    def test_code_renamed_into_receipts_is_unbounded(self):
        """A rename keeps its source path in the delta: code moved into receipts/ removed code."""
        observer = importlib.import_module("scripts.observe_release_heads")
        payload = {
            "status": "ahead",
            "files": [
                {
                    "filename": "release/v26.9.25/receipts/gate.json",
                    "previous_filename": "scripts/release_gate.py",
                    "status": "renamed",
                }
            ],
        }
        delta = observer.compare_delta(lambda url: payload, "o/r", P, H)
        self.assertEqual(delta["delta_paths"], ["release/v26.9.25/receipts/gate.json", "scripts/release_gate.py"])
        self.assertEqual(delta["files"][0]["previous_filename"], "scripts/release_gate.py")
        self.assertEqual(
            binding.classify_delta(delta["delta_paths"], ALLOWLIST), ("UNBOUNDED", ["scripts/release_gate.py"])
        )
        # control: a receipt renamed within receipts/ stays receipt-only
        payload["files"][0]["previous_filename"] = "release/v26.9.25/receipts/old-gate.json"
        delta = observer.compare_delta(lambda url: payload, "o/r", P, H)
        self.assertEqual(binding.classify_delta(delta["delta_paths"], ALLOWLIST)[0], "RECEIPT_ONLY")


@unittest.skipUnless(DELTAS.is_file(), "delta observations not committed")
class DeltaObservationsTest(unittest.TestCase):
    """The committed observation recomputes against the committed allowlist."""

    def setUp(self):
        self.doc = json.loads(DELTAS.read_text(encoding="utf-8"))

    def test_allowlist_identity_and_classification_recompute(self):
        allow_path = REPO / self.doc["allowlist"]["path"]
        self.assertEqual(self.doc["allowlist"]["sha256"], hashlib.sha256(allow_path.read_bytes()).hexdigest())
        for pair in self.doc["pairs"]:
            with self.subTest(repo=pair["repository"]):
                cls, offending = binding.classify_delta(pair["delta_paths"], ALLOWLIST)
                self.assertEqual((pair["delta_class"], pair["offending_paths"]), (cls, offending))
                touched = {f["filename"] for f in pair["files"]} | {
                    f["previous_filename"] for f in pair["files"] if "previous_filename" in f
                }
                self.assertEqual(pair["delta_paths"], sorted(touched))

    def test_falsifier_pairs_are_unbounded_and_affidavit_is_admitted(self):
        by_repo = {p["repository"]: p for p in self.doc["pairs"]}
        for repo, path in FALSIFIERS.items():
            with self.subTest(repo=repo):
                self.assertEqual(by_repo[repo]["binding"], "BLOCKED(EVIDENCE_DELTA_UNBOUNDED)")
                self.assertIn(path, by_repo[repo]["offending_paths"])
                self.assertIs(by_repo[repo]["claim_holds"], False)  # closure prose claimed receipt-only
        autofde = by_repo["seanchatmangpt/autofde-lab"]
        self.assertEqual((autofde["base"][:8], autofde["head"][:8]), ("6fbe1807", "98b6cc9b"))
        self.assertEqual(by_repo["seanchatmangpt/affidavit"]["binding"], "ADMITTED")
        self.assertEqual(by_repo["seanchatmangpt/affidavit"]["delta_class"], "RECEIPT_ONLY")


class AdmitTest(unittest.TestCase):
    def test_lawful_receipt_is_admitted(self):
        self.assertIsNone(admit(receipt_binding()))
        self.assertIsNone(admit(receipt_binding(), content=b"{}"))

    def test_every_binding_code_is_typed(self):
        for code in BINDING_RULES + BINDING_BLOCKERS:
            self.assertIn(code, FAILURE_CLASS)

    def test_one_refusing_mutant_per_rule(self):
        unbounded = ["release/v26.9.25/receipts/tlc-court.json", FALSIFIERS["seanchatmangpt/autofde-lab"]]
        cases = {
            "EVIDENCE_NOT_DURABLE": receipt_binding(evidence_locator="scratchpad/v26925/act/receipts/tlc.json"),
            "EVIDENCE_SUBJECT_MUTABLE": receipt_binding(evaluated_subject_sha="master"),
            "EVIDENCE_CONTAINER_CLAIMS_SUBJECT": receipt_binding(evaluated_subject_sha=CROWN_SHA),
            "EVIDENCE_SUBJECT_SPLIT": receipt_binding(
                lineage_proof={"status": "diverged", "delta_paths": [], "delta_class": "EMPTY"}
            ),
            "EVIDENCE_LINEAGE_MISSING": receipt_binding(
                lineage_proof={"status": "ahead", "delta_paths": None, "delta_class": None}
            ),
            "EVIDENCE_DELTA_MISCLAIMED": receipt_binding(
                lineage_proof={"status": "ahead", "delta_paths": unbounded, "delta_class": "RECEIPT_ONLY"}
            ),
        }
        self.assertEqual(set(cases) | {"EVIDENCE_DIGEST_MISMATCH"}, set(BINDING_RULES))
        for code, b in cases.items():
            with self.subTest(code=code):
                state = admit(b)
                self.assertEqual((state.state, state.code), ("REFUSED", code), state.detail)
        state = admit(receipt_binding(), content=b'{"standing": "ALIVE"}')
        self.assertEqual((state.state, state.code), ("REFUSED", "EVIDENCE_DIGEST_MISMATCH"))
        tampered = replace(receipt_binding(), standing="FINAL")  # binding_digest no longer recomputes
        self.assertEqual(admit(tampered).code, "EVIDENCE_DIGEST_MISMATCH")

    def test_unbounded_delta_is_a_typed_blocker(self):
        paths = ["release/v26.9.25/receipts/tlc-court.json", FALSIFIERS["seanchatmangpt/autofde-lab"]]
        state = admit(receipt_binding(lineage_proof={"status": "ahead", "delta_paths": paths, "delta_class": "UNBOUNDED"}))
        self.assertEqual((state.state, state.code), ("BLOCKED", "EVIDENCE_DELTA_UNBOUNDED"))
        self.assertEqual((state.failure_class, state.broken_term), ("EVIDENCE_FAILURE", "R_missing_identity"))
        self.assertIn("scripts/release_tlc_court_receipt.py", state.detail)

    def test_receipt_naming_its_own_container_is_refused(self):
        state = admit(receipt_binding(evaluated_subject_sha=H))
        self.assertEqual(state.code, "EVIDENCE_CONTAINER_CLAIMS_SUBJECT")

    def test_in_tree_binding_must_evaluate_its_container(self):
        tree = alive_tree()
        try:
            req = next(r for r in tree.inputs().requirements if r.id == "AC-01")
            b = binding.bind_in_tree(req, CROWN_SHA, ROOT_REPO, "release/v26.9.25/manifest.toml", b"x", court="m")
            self.assertIsNone(admit(b))
            split = replace(b, evaluated_subject_sha=P).sealed()
            self.assertEqual(admit(split).code, "EVIDENCE_SUBJECT_SPLIT")
            mutable = binding.bind_in_tree(req, "HEAD", ROOT_REPO, "release/v26.9.25/manifest.toml", b"x", court="m")
            self.assertEqual(admit(mutable).code, "EVIDENCE_SUBJECT_MUTABLE")
        finally:
            tree.cleanup()


class CrownBindingTest(unittest.TestCase):
    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)

    def tearDown(self):
        self.tree.cleanup()

    def evaluate(self, obs=None, previous=None, crown_sha=CROWN_SHA, mode="PRE_TAG"):
        return crown.evaluate(
            self.tree.release_dir, obs or self.obs, previous, crown_sha, root=self.tree.root, mode=mode
        )

    def test_every_pass_carries_an_admitted_binding(self):
        verdict = self.evaluate()
        self.assertEqual(verdict.standing, "ALIVE", verdict.remaining)
        reqs = {r.id: r for r in self.tree.inputs().requirements}
        for rid, state in verdict.receipt["requirements"].items():
            with self.subTest(rid=rid):
                b = state["binding"]
                self.assertIsNotNone(b)
                self.assertTrue(binding.is_durable(b["evidence_locator"]), b["evidence_locator"])
                body = {k: v for k, v in b.items() if k != "binding_digest"}
                self.assertEqual(b["binding_digest"], digest(body))
                if reqs[rid].evidence_locator.startswith("local:"):
                    self.assertIn(b["kind"], {"IN_TREE_DERIVED", "LOCAL_RECEIPT", "OPERATOR_LOCAL"})
                    self.assertEqual(b["evidence_container_sha"], CROWN_SHA)
                else:
                    self.assertEqual(b["kind"], "REMOTE_RECEIPT")
                    self.assertEqual(b["evaluated_subject_sha"], producer_sha(reqs[rid].locator_repo))
                    self.assertNotEqual(b["evaluated_subject_sha"], b["evidence_container_sha"])
                    self.assertEqual(b["lineage_proof"]["delta_class"], "RECEIPT_ONLY")

    def test_every_pass_site_passes_a_binding(self):
        """Source law: no evaluator constructs a PASS without an EvidenceBinding."""
        for rel in ("evidence.py", "posttag.py"):
            tree = ast.parse((REPO / "scripts/release_train/root_crown" / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "PASS":
                    with self.subTest(file=rel, line=node.lineno):
                        has = len(node.args) >= 3 or any(k.arg == "binding" for k in node.keywords)
                        self.assertTrue(has, f"{rel}:{node.lineno} PASS without binding")

    def test_falsifier_delta_blocks_the_requirement(self):
        obs = copy.deepcopy(self.obs)
        req = next(r for r in self.tree.inputs().requirements if r.id == "AC-07")
        obs["artifacts"][req.evidence_locator]["subject_delta_paths"].append(FALSIFIERS["seanchatmangpt/autofde-lab"])
        verdict = self.evaluate(obs)
        state = verdict.receipt["requirements"]["AC-07"]
        self.assertEqual((verdict.standing, state["state"], state["code"]), ("BLOCKED", "BLOCKED", "EVIDENCE_DELTA_UNBOUNDED"))

    def test_mutable_subject_is_refused(self):
        obs = copy.deepcopy(self.obs)
        req = next(r for r in self.tree.inputs().requirements if r.id == "AC-07")
        obs["artifacts"][req.evidence_locator]["json"]["subject_sha"] = "master"
        state = self.evaluate(obs).receipt["requirements"]["AC-07"]
        self.assertEqual((state["state"], state["code"]), ("REFUSED", "EVIDENCE_SUBJECT_MUTABLE"))

    def test_new_head_exemption_is_only_for_in_tree_derived(self):
        """The observed root head moves past the attested crown (POST_TAG drift): what the crown
        derived from its own tree at crown_sha stays PASS; receipts committed in that tree
        (LOCAL_RECEIPT, OPERATOR_LOCAL) are not exempted by the crown commit."""
        r0 = self.evaluate()
        obs = copy.deepcopy(self.obs)
        obs["repos"][ROOT_REPO]["head_sha"] = "d" * 40
        r1 = self.evaluate(obs, r0.receipt, CROWN_SHA, mode="POST_TAG")
        reqs = r1.receipt["requirements"]
        kinds = {rid: (r0.receipt["requirements"][rid]["binding"] or {}).get("kind") for rid in reqs}
        unknown = {rid for rid, s in reqs.items() if s["code"] == "NEW_HEAD_UNEVIDENCED"}
        root_local = {r.id for r in self.tree.inputs().requirements if r.owner_repo == ROOT_REPO}
        self.assertTrue(unknown)
        self.assertEqual({kinds[rid] for rid in unknown}, {"LOCAL_RECEIPT", "OPERATOR_LOCAL"})
        in_tree = {rid for rid in root_local if kinds[rid] == "IN_TREE_DERIVED" and rid != "AC-18"}
        self.assertTrue(in_tree)
        self.assertEqual({rid for rid in in_tree if reqs[rid]["state"] != "PASS"}, set())

    def test_overlay_fills_only_matching_pairs(self):
        doc = {"pairs": [{"repository": "seanchatmangpt/autofde-lab", "base": P, "head": H, "status": "ahead",
                          "delta_paths": ["a"]}]}  # fmt: skip
        obs = {"artifacts": {"seanchatmangpt/autofde-lab:x.json": {"head_sha": H, "json": {"subject_sha": P}},
                             "seanchatmangpt/xaas:y.json": {"head_sha": H, "json": {"subject_sha": P}}}}  # fmt: skip
        out = binding.overlay_deltas(obs, doc)
        self.assertEqual(out["artifacts"]["seanchatmangpt/autofde-lab:x.json"]["subject_delta_paths"], ["a"])
        self.assertNotIn("subject_delta_paths", out["artifacts"]["seanchatmangpt/xaas:y.json"])
        self.assertNotIn("subject_delta_paths", obs["artifacts"]["seanchatmangpt/autofde-lab:x.json"])


INDEX = REPO / "release" / RELEASE / "hardening/evidence/INDEX.json"
CLOSURE = REPO / "release" / RELEASE / "closure.json"


@unittest.skipUnless(INDEX.is_file() and DELTAS.is_file(), "E1 index / delta observations not committed")
class DurableClosureTest(unittest.TestCase):
    """The tagged closure bound to the committed E1 evidence (durable/v1): the court recomputes
    every evidence, log and output digest from the committed bytes."""

    def bound(self):
        from scripts.release_train.release_closure_court.court import bind_index

        return bind_index(
            json.loads(CLOSURE.read_text(encoding="utf-8")),
            json.loads(INDEX.read_text(encoding="utf-8")),
            json.loads(DELTAS.read_text(encoding="utf-8")),
        )

    def test_committed_evidence_recomputes(self):
        from scripts.release_train.release_closure_court.court import evaluate

        verdict = evaluate(self.bound(), REPO)
        # Two PASS courts carry no durable evidence yet (a github run court with no locator;
        # the zoela witness court with no INDEX row): typed findings for the hardening outputs.
        self.assertEqual(
            {":".join(r.split(":")[:3]) for r in verdict.refusals},
            {"REFUSED:EVIDENCE_NOT_DURABLE:ENGINEERING_STANDARDS", "REFUSED:EVIDENCE_NOT_DURABLE:ZOELA"},
        )
        unbounded = {r.split(":")[0] for r in verdict.remaining if r.endswith(":EVIDENCE_DELTA_UNBOUNDED")}
        self.assertEqual(unbounded, {"AUTOFDE_LAB", "GGEN_IGNITER", "XAAS", "ZOELA"})

    def test_tampered_evidence_byte_is_digest_mismatch(self):
        import shutil
        import tempfile

        from scripts.release_train.release_closure_court.court import evaluate

        rel = "release/v26.9.25/hardening/evidence"
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(REPO / rel, f"{tmp}/{rel}")
            out = next((REPO / rel / "courts/affidavit").glob("*/court.out")).relative_to(REPO)
            target = f"{tmp}/{out}"
            data = bytearray(open(target, "rb").read())
            data[0] ^= 1
            open(target, "wb").write(bytes(data))
            refusals = evaluate(self.bound(), __import__("pathlib").Path(tmp)).refusals
        self.assertIn("REFUSED:EVIDENCE_DIGEST_MISMATCH:AFFIDAVIT:affidavit:brce_court(AC-08/F-05):output_sha256", refusals)


class ContextAllowlistTest(unittest.TestCase):
    def test_missing_allowlist_fails_closed(self):
        tree = alive_tree()
        try:
            ctx = evidence.Context(
                root=tree.root,
                release_dir=tree.release_dir,
                observations=alive_observations(tree),
                crown_sha=CROWN_SHA,
                inputs=tree.inputs(),
                allowlist_root=tree.root / "no-policy",
            )
            self.assertEqual(ctx.allowlist, {})
            req = next(r for r in tree.inputs().requirements if r.id == "AC-07")
            state = evidence.EVALUATORS[req.evidence_kind](req, ctx)
            self.assertEqual((state.state, state.code), ("BLOCKED", "EVIDENCE_DELTA_UNBOUNDED"))
        finally:
            tree.cleanup()


if __name__ == "__main__":
    unittest.main()
