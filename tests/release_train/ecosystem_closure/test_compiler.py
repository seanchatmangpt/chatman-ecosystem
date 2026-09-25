from __future__ import annotations

import copy
import io
import json
import tempfile
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scripts.release_train.ecosystem_closure import (
    ClosureMalformed,
    compile_closure,
    verify_receipt,
)
from scripts.release_train.ecosystem_closure.__main__ import main

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "release" / "v26.9.24" / "closure.toml"
DIGEST = "sha256:" + "0" * 64


def sha(ch: str) -> str:
    return ch * 40


def subject(sid: str, ch: str, deps: dict[str, str] | None = None) -> dict:
    deps = deps or {}
    return {
        "id": sid,
        "repository": f"seanchatmangpt/{sid}",
        "role": sid,
        "class": "SPINE",
        "required": True,
        "normative": False,
        "standing": "ALIVE",
        "subject_source": "canonical-pr",
        "sha": sha(ch),
        "default_head": sha(ch),
        "depends_on": list(deps),
        "dependency_shas": dict(deps),
        "unenumerated_open_lineage": 0,
        "terminal_disposition": "ADMIT",
        "verifier": {"court": "exact-head", "conclusion": "SUCCESS", "run_head_sha": sha(ch)},
        "receipt": {"digest": "sha256:" + ch * 64, "replay": "PASS"},
        "propositions": [{"id": f"{sid}-P", "state": "PASS"}],
        "lineage": [
            {"pr": 1, "sha": sha(ch), "state": "MERGED", "draft": False,
             "mergeable": "MERGEABLE", "disposition": "CANONICAL", "additions": 10},
        ],
    }


def alive_manifest() -> dict:
    root = subject("standards", "a")
    root["normative"] = True
    return {
        "closure": {
            "version": "26.9.24",
            "observed_at": "2026-09-25T00:00:00Z",
            "root_repository": "seanchatmangpt/chatman-ecosystem",
            "standing": "ALIVE",
            "max_canonical_additions": 50000,
            "spine": ["standards", "worker", "chatman-ecosystem"],
        },
        "subjects": [
            root,
            subject("worker", "b", {"standards": sha("a")}),
            subject("chatman-ecosystem", "c", {"worker": sha("b")}),
        ],
    }


def codes(receipt: dict, sid: str | None = None) -> set[str]:
    found = {f["code"] for f in receipt["closure_findings"] + receipt["overclaims"]}
    for verdict in receipt["subjects"]:
        if sid is None or verdict["id"] == sid:
            found |= {f["code"] for f in verdict["findings"]}
    return found


class PositiveClosure(unittest.TestCase):
    def test_fully_bound_closure_is_alive(self) -> None:
        receipt = compile_closure(alive_manifest(), DIGEST)
        self.assertEqual(receipt["computed_standing"], "ALIVE")
        self.assertEqual(codes(receipt), set())
        self.assertEqual(receipt["blocked_required"], [])
        self.assertEqual(len(receipt["admitted_subjects"]), 3)
        self.assertTrue(verify_receipt(receipt))

    def test_compile_is_deterministic(self) -> None:
        self.assertEqual(compile_closure(alive_manifest(), DIGEST), compile_closure(alive_manifest(), DIGEST))


class NegativeClosure(unittest.TestCase):
    """One mutation per law; each must refuse the crown."""

    def refuse(self, mutate, expected: str, sid: str | None = None) -> dict:
        data = alive_manifest()
        mutate(data)
        receipt = compile_closure(data, DIGEST)
        self.assertEqual(receipt["computed_standing"], "BLOCKED")
        self.assertIn(expected, codes(receipt, sid))
        return receipt

    def s(self, data: dict, sid: str) -> dict:
        return next(item for item in data["subjects"] if item["id"] == sid)

    def test_unresolved_successor(self) -> None:
        def m(d):
            self.s(d, "worker")["lineage"].append({"pr": 2, "sha": sha("e"), "state": "OPEN", "draft": True,
                                                   "mergeable": "MERGEABLE", "disposition": "UNRESOLVED", "additions": 1})
        self.refuse(m, "CLOSURE_SUCCESSOR_AMBIGUOUS", "worker")

    def test_two_canonical_prs(self) -> None:
        def m(d):
            extra = dict(self.s(d, "worker")["lineage"][0], pr=2)
            self.s(d, "worker")["lineage"].append(extra)
        self.refuse(m, "CLOSURE_CANONICAL_PR_AMBIGUOUS", "worker")

    def test_open_superseded_and_zombie_lineage(self) -> None:
        for disposition, code in (("SUPERSEDED", "CLOSURE_SUPERSEDED_LINEAGE_OPEN"), ("ZOMBIE", "CLOSURE_ZOMBIE_LINEAGE_OPEN")):
            def m(d, disposition=disposition):
                self.s(d, "worker")["lineage"].append({"pr": 9, "sha": sha("e"), "state": "OPEN", "draft": True,
                                                       "mergeable": "UNKNOWN", "disposition": disposition, "additions": 0})
            self.refuse(m, code, "worker")

    def test_non_mergeable_required_head(self) -> None:
        def m(d):
            self.s(d, "worker")["lineage"][0].update(state="OPEN", mergeable="CONFLICTING")
        self.refuse(m, "CLOSURE_HEAD_NOT_MERGEABLE", "worker")

    def test_open_head_is_not_final(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["lineage"][0].update(state="OPEN"), "CLOSURE_HEAD_NOT_FINAL", "worker")

    def test_red_exact_head_verification(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["verifier"].update(conclusion="FAILURE"), "CLOSURE_VERIFICATION_NOT_GREEN", "worker")

    def test_green_run_on_another_subject(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["verifier"].update(run_head_sha=sha("f")), "CLOSURE_VERIFICATION_SUBJECT_SPLIT", "worker")

    def test_draft_normative_rfc(self) -> None:
        def m(d):
            self.s(d, "standards")["lineage"][0].update(state="OPEN", draft=True)
        receipt = self.refuse(m, "CLOSURE_NORMATIVE_RFC_DRAFT", "standards")
        self.assertIn("CLOSURE_NORMATIVE_ROOT_NOT_ADMITTED", codes(receipt, "standards"))

    def test_unknown_required_proposition(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["propositions"][0].update(state="UNKNOWN"), "CLOSURE_PROPOSITION_UNKNOWN", "worker")

    def test_failed_proposition(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["propositions"][0].update(state="FAIL"), "CLOSURE_PROPOSITION_FAILED", "worker")

    def test_empty_propositions(self) -> None:
        self.refuse(lambda d: self.s(d, "worker").update(propositions=[]), "CLOSURE_PROPOSITIONS_EMPTY", "worker")

    def test_dependency_sha_not_in_manifest(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["dependency_shas"].update(standards=sha("9")), "CLOSURE_DEPENDENCY_SHA_SPLIT", "worker")

    def test_dependency_sha_unbound(self) -> None:
        self.refuse(lambda d: self.s(d, "worker").update(dependency_shas={}), "CLOSURE_DEPENDENCY_SHA_UNBOUND", "worker")

    def test_dependency_not_admitted(self) -> None:
        def m(d):
            self.s(d, "worker")["depends_on"].append("ghost")
        self.refuse(m, "CLOSURE_DEPENDENCY_NOT_ADMITTED", "worker")

    def test_required_depends_on_advisory(self) -> None:
        self.refuse(lambda d: self.s(d, "standards").update(required=False), "CLOSURE_DEPENDENCY_NOT_REQUIRED", "worker")

    def test_dependency_cycle(self) -> None:
        def m(d):
            self.s(d, "standards")["depends_on"].append("chatman-ecosystem")
            self.s(d, "standards")["dependency_shas"]["chatman-ecosystem"] = sha("c")
        self.refuse(m, "CLOSURE_DEPENDENCY_CYCLE")

    def test_two_heads_for_one_repository(self) -> None:
        self.refuse(lambda d: self.s(d, "worker").update(repository="seanchatmangpt/standards"), "CLOSURE_DUPLICATE_REPOSITORY")

    def test_unresolved_subject_sha(self) -> None:
        self.refuse(lambda d: self.s(d, "worker").update(sha="UNRESOLVED", subject_source="unresolved"), "CLOSURE_SUBJECT_UNRESOLVED", "worker")

    def test_missing_receipt_and_replay(self) -> None:
        receipt = self.refuse(lambda d: self.s(d, "worker").update(receipt={"digest": "", "replay": "UNKNOWN"}), "CLOSURE_RECEIPT_MISSING", "worker")
        self.assertIn("CLOSURE_RECEIPT_NOT_REPLAYED", codes(receipt, "worker"))

    def test_default_head_without_canonical_binding(self) -> None:
        def m(d):
            w = self.s(d, "worker")
            w["subject_source"] = "default-head"
            w["lineage"] = []
        self.refuse(m, "CLOSURE_CANONICAL_BINDING_ABSENT", "worker")

    def test_scope_bound(self) -> None:
        self.refuse(lambda d: self.s(d, "worker")["lineage"][0].update(additions=136153), "CLOSURE_SCOPE_EXCEEDS_BOUND", "worker")

    def test_unenumerated_lineage(self) -> None:
        self.refuse(lambda d: self.s(d, "worker").update(unenumerated_open_lineage=5), "CLOSURE_LINEAGE_UNENUMERATED", "worker")

    def test_spine_edge_missing(self) -> None:
        def m(d):
            w = self.s(d, "chatman-ecosystem")
            w["depends_on"], w["dependency_shas"] = ["standards"], {"standards": sha("a")}
        self.refuse(m, "CLOSURE_SPINE_EDGE_MISSING")

    def test_spine_must_end_at_crown(self) -> None:
        self.refuse(lambda d: d["closure"].update(spine=["standards", "worker"]), "CLOSURE_SPINE_NOT_CROWNED")

    def test_declared_alive_overclaim(self) -> None:
        receipt = self.refuse(lambda d: self.s(d, "worker")["verifier"].update(conclusion="UNKNOWN"), "CLOSURE_STANDING_OVERCLAIM")
        self.assertEqual({o["subject"] for o in receipt["overclaims"]}, {"worker", "closure"})

    def test_blocked_leaf_never_crowns_via_leaf_tests(self) -> None:
        receipt = self.refuse(lambda d: self.s(d, "standards")["verifier"].update(conclusion="CANCELLED"), "CLOSURE_VERIFICATION_NOT_GREEN")
        self.assertEqual(receipt["blocked_required"], ["standards"])
        self.assertEqual(receipt["repair_order"], ["standards"])

    def test_malformed_manifests_refuse(self) -> None:
        cases = [
            lambda d: d.pop("closure"),
            lambda d: d.update(subjects=[]),
            lambda d: self.s(d, "worker").pop("verifier"),
            lambda d: self.s(d, "worker").update(required="yes"),
            lambda d: self.s(d, "worker")["lineage"][0].update(pr=True),
            lambda d: self.s(d, "worker")["lineage"][0].update(disposition="MAYBE"),
            lambda d: self.s(d, "worker").update(standing="OBSERVED"),
        ]
        for mutate in cases:
            data = alive_manifest()
            mutate(data)
            with self.assertRaises(ClosureMalformed):
                compile_closure(data, DIGEST)


class RepairOrder(unittest.TestCase):
    def test_dependencies_first_by_spine_criticality(self) -> None:
        data = alive_manifest()
        leaf = subject("leaf", "d")
        crown = next(s for s in data["subjects"] if s["id"] == "chatman-ecosystem")
        crown["depends_on"].append("leaf")
        crown["dependency_shas"]["leaf"] = sha("d")
        data["subjects"].append(leaf)
        for s in data["subjects"]:
            s["verifier"]["conclusion"] = "UNKNOWN"
            s["standing"] = "BLOCKED"
        data["closure"]["standing"] = "BLOCKED"
        receipt = compile_closure(data, DIGEST)
        self.assertEqual(receipt["repair_order"], ["standards", "worker", "leaf", "chatman-ecosystem"])


class CommandLine(unittest.TestCase):
    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_cli_replay_and_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "closure.toml"
            manifest.write_text(MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
            receipt = Path(tmp) / "receipt.json"
            code, _, _ = self.run_main(str(manifest), "--emit", str(receipt))
            self.assertEqual(code, 0)
            code, _, err = self.run_main(str(manifest), "--emit", str(Path(tmp) / "again.json"), "--replay", str(receipt))
            self.assertEqual(code, 0, err)

            tampered = json.loads(receipt.read_text(encoding="utf-8"))
            tampered["computed_standing"] = "ALIVE"
            receipt.write_text(json.dumps(tampered), encoding="utf-8")
            code, _, err = self.run_main(str(manifest), "--emit", str(Path(tmp) / "x.json"), "--replay", str(receipt))
            self.assertEqual(code, 1)
            self.assertIn("CLOSURE_REPLAY_RECEIPT_TAMPERED", err)


class V26924Manifest(unittest.TestCase):
    """The admitted v26.9.24 closure manifest, as observed."""

    @classmethod
    def setUpClass(cls) -> None:
        raw = MANIFEST.read_bytes()
        cls.data = tomllib.loads(raw.decode("utf-8"))
        cls.receipt = compile_closure(copy.deepcopy(cls.data), DIGEST)

    def test_manifest_is_well_formed_and_consistent(self) -> None:
        self.assertEqual(self.receipt["overclaims"], [])
        self.assertEqual(self.receipt["closure_findings"], [])

    def test_closure_is_blocked_not_alive(self) -> None:
        self.assertEqual(self.receipt["declared_standing"], "BLOCKED")
        self.assertEqual(self.receipt["computed_standing"], "BLOCKED")
        self.assertIn("chatman-ecosystem", self.receipt["blocked_required"])

    def test_normative_root_repairs_first(self) -> None:
        self.assertEqual(self.receipt["repair_order"][0], "engineering-standards")
        self.assertEqual(self.receipt["repair_order"][-1], "chatman-ecosystem")

    def test_every_observed_sha_is_exact(self) -> None:
        for s in self.data["subjects"]:
            if s["subject_source"] != "unresolved":
                self.assertRegex(s["sha"], r"^[0-9a-f]{40}$", s["id"])

    def test_committed_receipt_is_current_projection(self) -> None:
        receipt_path = MANIFEST.with_name("closure-receipt.json")
        committed = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertTrue(verify_receipt(committed))
        with tempfile.TemporaryDirectory() as tmp:
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = main([str(MANIFEST), "--emit", str(Path(tmp) / "r.json"), "--replay", str(receipt_path)])
        self.assertEqual(code, 0, err.getvalue())

    def test_require_alive_refuses(self) -> None:
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main([str(MANIFEST), "--require-alive"])
        self.assertEqual(code, 2)
        self.assertIn("CLOSURE_NOT_ALIVE", err.getvalue())


if __name__ == "__main__":
    unittest.main()
