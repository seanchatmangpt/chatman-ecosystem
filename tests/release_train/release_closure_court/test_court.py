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
from scripts.release_train.release_closure_court.court import RULES, evaluate

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
        self.assertEqual(set(mutants), set(RULES))
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


if __name__ == "__main__":
    unittest.main()
