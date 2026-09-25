from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from collections.abc import Callable
from contextlib import redirect_stdout
from pathlib import Path

from scripts.release_train.release_closure_court.__main__ import main
from scripts.release_train.release_closure_court.court import BASE_RULES, DURABLE_RULES, RULES, evaluate

ROOT = Path(__file__).resolve().parents[3]
REAL_CLOSURE = ROOT / "release" / "v26.9.24" / "closure.json"
A, B, C = "a" * 40, "b" * 40, "c" * 40


def _base() -> dict:
    return {
        "release": "v26.9.24",
        "normative_ledger": "seanchatmangpt/engineering-standards:RFC-0002",
        "transient_heads": [{"repository": "o/pack", "sha": C, "replaced_by": B}],
        "subjects": [
            {
                "subject_id": "SPEC",
                "rfc_id": "RFC-X",
                "repository": "o/spec",
                "artifact": "docs/rfc/RFC-X.md",
                "sha": A,
                "required": True,
                "spec_standing": "FINAL_SPEC",
                "impl_standing": "PLANNED",
                "authority_ceiling": "NONE",
                "authority_claimed": "NONE",
                "courts": [{"court": "docs", "kind": "spec", "result": "PASS", "sha": A}],
                "pins": [{"repository": "o/pack", "sha": B}],
            },
            {
                "subject_id": "IMPL",
                "repository": "o/impl",
                "artifact": "lib/impl.ex",
                "sha": B,
                "required": True,
                "spec_standing": "NOT_A_SPEC",
                "impl_standing": "ALIVE",
                "authority_ceiling": "CONSTRUCT",
                "authority_claimed": "CONSTRUCT",
                "courts": [{"court": "ci", "result": "PASS", "sha": B}],
            },
        ],
    }


def _refusal_prefixes(closure: dict) -> set[str]:
    return {":".join(r.split(":")[:2]) for r in evaluate(closure).refusals}


class ReleaseClosureCourtTests(unittest.TestCase):
    def test_valid_closure_is_alive_with_stable_digest(self) -> None:
        first, second = evaluate(_base()), evaluate(_base())
        self.assertEqual(first.standing, "ALIVE")
        self.assertEqual(first.refusals, ())
        self.assertEqual(first.receipt["receipt_digest"], second.receipt["receipt_digest"])
        self.assertTrue(first.receipt["receipt_digest"].startswith("sha256:"))

    def test_typed_blocker_is_partial_alive_and_listed_as_remaining(self) -> None:
        c = _base()
        c["subjects"][1]["impl_standing"] = "BLOCKED"
        c["subjects"][1]["impl_type"] = "evidence:o/impl@" + B
        v = evaluate(c)
        self.assertEqual(v.standing, "PARTIAL_ALIVE")
        self.assertEqual(v.remaining, ("IMPL:impl:BLOCKED(evidence:o/impl@" + B + ")",))

    def test_merged_spec_is_terminal_but_not_a_canonical_owner(self) -> None:
        c = _base()
        c["subjects"].append(
            {**copy.deepcopy(c["subjects"][0]), "subject_id": "SPEC-MERGED", "repository": "o/other",
             "spec_standing": "MERGED"}
        )
        v = evaluate(c)
        self.assertEqual(v.standing, "ALIVE", v.refusals)
        c["subjects"][-1]["spec_standing"] = "MERGED_ISH"
        self.assertIn("REFUSED:UNKNOWN_REQUIRED_SUBJECT", _refusal_prefixes(c))

    def test_every_rule_has_a_refusing_mutant(self) -> None:
        mutants: dict[str, Callable[[dict], object]] = {
            "REFUSED:MALFORMED_ROW": lambda c: c["subjects"][0].pop("artifact"),
            "REFUSED:DUPLICATE_SUBJECT_ID": lambda c: c["subjects"].append(copy.deepcopy(c["subjects"][0])),
            "REFUSED:MISSING_EXACT_SHA": lambda c: c["subjects"][0].update(sha="deadbeef"),
            "REFUSED:UNKNOWN_REQUIRED_SUBJECT": lambda c: c["subjects"][1].update(impl_standing="UNKNOWN"),
            "REFUSED:SUPERSEDED_WITHOUT_SUCCESSOR": lambda c: c["subjects"][0].update(spec_standing="SUPERSEDED"),
            "REFUSED:SUCCESSOR_UNBOUND": lambda c: c["subjects"][0].update(
                spec_standing="SUPERSEDED", successor={"repository": "o/spec", "pr": 9}
            ),
            "REFUSED:FINAL_SPEC_AS_IMPLEMENTATION_EVIDENCE": lambda c: c["subjects"][0].update(impl_standing="ALIVE"),
            "REFUSED:REQUIRED_COURT_FAILED": lambda c: c["subjects"][1]["courts"].append(
                {"court": "stogaf", "result": "FAIL", "sha": B}
            ),
            "REFUSED:COURT_SUBJECT_SPLIT": lambda c: c["subjects"][1]["courts"][0].update(sha=A),
            "REFUSED:AUTHORITY_ESCALATION": lambda c: c["subjects"][1].update(authority_claimed="DO"),
            "REFUSED:TRANSIENT_PIN": lambda c: c["subjects"][0]["pins"].append({"repository": "o/pack", "sha": C}),
            "REFUSED:DUPLICATE_CANONICAL_OWNER": lambda c: c["subjects"].append(
                {**copy.deepcopy(c["subjects"][0]), "subject_id": "SPEC-COPY", "repository": "o/other"}
            ),
            "REFUSED:BLOCKED_WITHOUT_TYPE": lambda c: c["subjects"][1].update(impl_standing="BLOCKED"),
        }
        self.assertEqual(set(mutants), set(BASE_RULES))
        self.assertEqual(set(BASE_RULES) | set(DURABLE_RULES), set(RULES))
        for rule, mutate in mutants.items():
            with self.subTest(rule=rule):
                closure = _base()
                mutate(closure)
                verdict = evaluate(closure)
                self.assertEqual(verdict.standing, "REFUSED")
                self.assertIn(rule, _refusal_prefixes(closure))

    def test_cli_exit_codes_follow_standing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = Path(tmp, "good.json"), Path(tmp, "bad.json")
            good.write_text(json.dumps(_base()))
            broken = _base()
            broken["subjects"][1]["impl_standing"] = "UNKNOWN"
            bad.write_text(json.dumps(broken))
            results = {}
            for name, path in (("ok", good), ("ko", bad)):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(["release_closure_court", str(path)])
                results[name] = (code, json.loads(buf.getvalue()))
            self.assertEqual(results["ok"], (0, results["ok"][1]))
            self.assertEqual(results["ok"][1]["standing"], "ALIVE")
            self.assertEqual(results["ko"][0], 2)
            self.assertEqual(results["ko"][1]["standing"], "REFUSED")

    @unittest.skipUnless(REAL_CLOSURE.is_file(), "release closure file not present at this subject")
    def test_committed_release_closure_is_terminal(self) -> None:
        verdict = evaluate(json.loads(REAL_CLOSURE.read_text(encoding="utf-8")))
        self.assertIn(verdict.standing, {"ALIVE", "PARTIAL_ALIVE"}, verdict.refusals)



TAGGED_CLOSURE = ROOT / "release" / "v26.9.25" / "closure.json"
# The v26.9.25 tagged closure verdict, computed by the tag-time court (68bacd8d,
# scripts/release_train/release_closure_court) over the tagged closure.json:
# `python3 -m scripts.release_train.release_closure_court release/v26.9.25/closure.json`.
TAGGED_RECEIPT_DIGEST = "sha256:f95b998cd8f7b02ba80612b1d1f87d716360330256e2c4d8743aa105e2326180"
TAGGED_STDOUT_SHA256 = "b849951ae3a788a6cec732868fdd613ee65054d8adb0c1f6a5e85f5457c3cbd7"
D = "d" * 40  # the evidence container commit (holds the receipt bytes)
E = "e" * 40  # a producer subject behind the court sha


class TaggedVerdictUnchangedTests(unittest.TestCase):
    @unittest.skipUnless(TAGGED_CLOSURE.is_file(), "v26.9.25 closure not present")
    def test_tagged_closure_verdict_is_byte_identical(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["release_closure_court", str(TAGGED_CLOSURE)])
        import hashlib

        self.assertEqual(code, 0)
        self.assertEqual(hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest(), TAGGED_STDOUT_SHA256)
        verdict = evaluate(json.loads(TAGGED_CLOSURE.read_text(encoding="utf-8")), Path("/nonexistent"))
        self.assertEqual(verdict.receipt["receipt_digest"], TAGGED_RECEIPT_DIGEST)
        self.assertNotIn("evidence_profile", verdict.receipt)


class DurableProfileTests(unittest.TestCase):
    """durable/v1 over real evidence bytes in a temp evidence root (git:<repo>@<sha>:<path>)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.receipt = b'{"standing": "ALIVE"}\n'
        self.log = b"ok 12 tests\n"
        for rel, data in (("ci/receipt.json", self.receipt), ("ci/run.log", self.log)):
            target = self.root / "o/evidence" / D / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def closure(self) -> dict:
        import hashlib

        c = _base()
        c["evidence_profile"] = "durable/v1"
        c["release"] = "v26.9.25"  # the delta allowlist is per release (fail-closed when absent)
        court = c["subjects"][1]["courts"][0]
        court.update(
            evidence_locator=f"git:o/evidence@{D}:ci/receipt.json",
            evidence_digest="sha256:" + hashlib.sha256(self.receipt).hexdigest(),
            log_locator=f"git:o/evidence@{D}:ci/run.log",
            log_sha256="sha256:" + hashlib.sha256(self.log).hexdigest(),
            evidence_subject_sha=E,
            lineage_proof={
                "status": "ahead",
                "delta_paths": ["release/v26.9.25/receipts/ci.json"],
                "delta_class": "RECEIPT_ONLY",
            },
        )
        # The spec court is PASS too: it binds in-tree evidence with no producer lineage.
        c["subjects"][0]["courts"][0].update(
            evidence_locator=f"git:o/evidence@{D}:ci/receipt.json",
            evidence_digest="sha256:" + hashlib.sha256(self.receipt).hexdigest(),
        )
        return c

    def test_durable_closure_is_alive_and_profile_is_recorded(self) -> None:
        verdict = evaluate(self.closure(), self.root)
        self.assertEqual((verdict.standing, verdict.refusals), ("ALIVE", ()))
        self.assertEqual(verdict.receipt["evidence_profile"], "durable/v1")

    def test_blocked_court_across_unbounded_delta_is_remaining_not_refused(self) -> None:
        c = self.closure()
        court = c["subjects"][1]["courts"][0]
        court["result"] = "BLOCKED"
        court["lineage_proof"] = {
            "status": "ahead",
            "delta_paths": ["release/v26.9.25/receipts/ci.json", "scripts/release_tlc_court_receipt.py"],
            "delta_class": "UNBOUNDED",
        }
        c["subjects"][1]["courts"].append({"court": "ci2", "result": "PASS", "sha": B, "evidence_locator":
            court["evidence_locator"], "evidence_digest": court["evidence_digest"]})  # fmt: skip
        verdict = evaluate(c, self.root)
        self.assertEqual(verdict.refusals, ())
        self.assertIn("IMPL:court:ci:EVIDENCE_DELTA_UNBOUNDED", verdict.remaining)
        self.assertEqual(verdict.standing, "PARTIAL_ALIVE")

    def test_every_durable_rule_has_a_refusing_mutant(self) -> None:
        def court(c: dict) -> dict:
            return c["subjects"][1]["courts"][0]

        mutants: dict[str, Callable[[dict], object]] = {
            "REFUSED:EVIDENCE_PROFILE_UNKNOWN": lambda c: c.update(evidence_profile="durable/v0"),
            "REFUSED:EVIDENCE_NOT_DURABLE": lambda c: court(c).update(
                evidence_locator="scratchpad/v26925/act/receipts/ci.receipt.json"
            ),
            "REFUSED:EVIDENCE_DIGEST_MISMATCH": lambda c: court(c).update(log_sha256="sha256:" + "0" * 64),
            "REFUSED:EVIDENCE_SUBJECT_MUTABLE": lambda c: court(c).update(evidence_subject_sha="main"),
            "REFUSED:EVIDENCE_SUBJECT_SPLIT": lambda c: court(c)["lineage_proof"].update(status="diverged"),
            "REFUSED:EVIDENCE_LINEAGE_MISSING": lambda c: court(c).pop("lineage_proof"),
            "REFUSED:EVIDENCE_CONTAINER_CLAIMS_SUBJECT": lambda c: court(c).update(evidence_subject_sha=D),
            "REFUSED:EVIDENCE_DELTA_MISCLAIMED": lambda c: court(c)["lineage_proof"].update(
                delta_paths=["release/v26.9.25/receipts/replay/origin_probe.exs"]
            ),
        }
        self.assertEqual(set(mutants), set(DURABLE_RULES))
        for rule, mutate in mutants.items():
            with self.subTest(rule=rule):
                closure = self.closure()
                mutate(closure)
                verdict = evaluate(closure, self.root)
                self.assertEqual(verdict.standing, "REFUSED")
                self.assertIn(rule, {":".join(r.split(":")[:2]) for r in verdict.refusals})
                # Anti-vacuity: the same mutant without the profile is not refused for it.
                closure.pop("evidence_profile")
                self.assertNotIn(rule, {":".join(r.split(":")[:2]) for r in evaluate(closure, self.root).refusals})

    def test_evidence_bytes_changed_is_digest_mismatch(self) -> None:
        (self.root / "o/evidence" / D / "ci/receipt.json").write_bytes(b'{"standing": "FINAL"}\n')
        verdict = evaluate(self.closure(), self.root)
        self.assertIn("REFUSED:EVIDENCE_DIGEST_MISMATCH:IMPL:ci:evidence", verdict.refusals)

    def test_release_without_allowlist_fails_closed(self) -> None:
        c = self.closure()
        c["release"] = "v26.9.24"
        verdict = evaluate(c, self.root)
        self.assertIn("REFUSED:EVIDENCE_DELTA_MISCLAIMED:IMPL:ci:claimed=RECEIPT_ONLY:computed=UNBOUNDED", verdict.refusals)

    def test_missing_evidence_root_is_not_durable(self) -> None:
        verdict = evaluate(self.closure(), None)
        self.assertTrue(all(r.startswith("REFUSED:EVIDENCE_NOT_DURABLE") for r in verdict.refusals), verdict.refusals)
        self.assertTrue(verdict.refusals)

    def test_cli_evidence_root_flag(self) -> None:
        path = self.root / "closure.json"
        path.write_text(json.dumps(self.closure()))
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["release_closure_court", str(path), "--evidence-root", str(self.root)])
        self.assertEqual((code, json.loads(buf.getvalue())["standing"]), (0, "ALIVE"))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["release_closure_court", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
