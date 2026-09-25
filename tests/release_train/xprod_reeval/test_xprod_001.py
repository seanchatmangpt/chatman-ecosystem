"""Chicago-style courts over the committed XPROD-001 case.

Every test runs the real court, the real provenance checker and the real
committed evidence bytes. Tampering is done on real copies in a temporary
directory. The online test calls the real GitHub API through ``gh`` and is a
named skip without a GitHub token; nothing is faked.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.release_train.cross_product_court.__main__ import run as court_run
from scripts.release_train.xprod_reeval.mutate import run_mutants
from scripts.release_train.xprod_reeval.provenance import (
    verify_offline,
    verify_online,
)

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "docs" / "jira" / "v26.9.25" / "xprod-cases"
CASE = CASE_DIR / "XPROD-001.json"
RECEIPT = CASE_DIR / "receipts" / "XPROD-001.receipt.json"


def _token_ready() -> bool:
    return bool(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))


class Xprod001Tests(unittest.TestCase):
    def test_committed_receipt_replays_exactly(self) -> None:
        data, code = court_run(str(CASE))
        recomputed = json.loads(json.dumps(data))
        committed = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(recomputed, committed)
        self.assertEqual(code, 0 if committed["standing"] == "ALIVE" else 2)

    def test_hddl_and_fond_are_independent_dimensions(self) -> None:
        raw = json.loads(CASE.read_text(encoding="utf-8"))
        by_id = {item["evidence_id"]: item for item in raw["evidence"]}
        self.assertNotEqual(
            by_id["E-HDDL"]["artifact_digest"],
            by_id["E-FOND"]["artifact_digest"],
        )
        receipt, _ = court_run(str(CASE))
        self.assertFalse(any("NOT_INDEPENDENT" in x for x in receipt["refusals"]))
        self.assertEqual(list(receipt["relations_checked"]), ["R-HDDL-FOND-frontier"])

    def test_tla_mutant_is_a_counterexample_with_trace_digest(self) -> None:
        raw = json.loads(CASE.read_text(encoding="utf-8"))
        mutant = next(x for x in raw["evidence"] if x["evidence_id"] == "E-TLA-MUT-DO")
        self.assertEqual(mutant["result"], "COUNTEREXAMPLE")
        self.assertTrue(mutant["counterexample_digest"].startswith("sha256:"))
        receipt, _ = court_run(str(CASE))
        self.assertIn("M-TLA-DO-WITHOUT-AUTHORITY", receipt["mutants_checked"])

    def test_offline_provenance_binds_every_committed_byte(self) -> None:
        report = verify_offline(CASE, RECEIPT)
        self.assertEqual(report["standing"], "ALIVE", report["refusals"])
        raw = json.loads(CASE.read_text(encoding="utf-8"))
        self.assertEqual(
            len([c for c in report["checked"] if c.startswith("artifact:")]),
            len(raw["evidence"]),
        )

    def test_tampered_evidence_byte_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "case"
            shutil.copytree(CASE_DIR, copy)
            target = copy / "evidence" / "E-OCEL2.zip"
            data = bytearray(target.read_bytes())
            data[-1] ^= 0x01
            target.write_bytes(bytes(data))
            report = verify_offline(copy / "XPROD-001.json")
        self.assertEqual(report["standing"], "REFUSED")
        self.assertIn("REFUSED:ARTIFACT_DIGEST_MISMATCH:E-OCEL2", report["refusals"])

    def test_edited_receipt_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            forged = Path(td) / "receipt.json"
            data = json.loads(RECEIPT.read_text(encoding="utf-8"))
            data["standing"] = "ALIVE" if data["standing"] != "ALIVE" else "BLOCKED"
            forged.write_text(json.dumps(data), encoding="utf-8")
            report = verify_offline(CASE, forged)
        self.assertIn("REFUSED:RECEIPT_REPLAY_MISMATCH", report["refusals"])

    def test_every_case_mutant_is_killed(self) -> None:
        report = run_mutants(CASE)
        self.assertTrue(report["all_killed"], json.dumps(report, indent=2))
        self.assertEqual(
            sorted(report["mutants"]),
            ["authority_do", "digest_mismatch", "missing_producer", "sha_drift"],
        )

    def test_authority_do_case_exits_2_with_typed_refusal(self) -> None:
        raw = json.loads(CASE.read_text(encoding="utf-8"))
        raw["evidence"][0]["authority"] = "DO"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "do.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            done = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.release_train.cross_product_court",
                    str(path),
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": str(ROOT)},
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(done.returncode, 2, done.stderr)
        out = json.loads(done.stdout)
        self.assertEqual(out["standing"], "REFUSED")
        self.assertTrue(out["refusals"][0].startswith("REFUSED:INADMISSIBLE_CASE:"))
        self.assertNotIn("Traceback", done.stderr)

    @unittest.skipUnless(
        _token_ready() and os.environ.get("XPROD_ONLINE") == "1",
        "online provenance needs GH_TOKEN/GITHUB_TOKEN and XPROD_ONLINE=1",
    )
    def test_online_provenance_against_real_producer_runs(self) -> None:
        report = verify_online(CASE)
        self.assertNotEqual(report["standing"], "REFUSED", report["refusals"])


if __name__ == "__main__":
    unittest.main()
