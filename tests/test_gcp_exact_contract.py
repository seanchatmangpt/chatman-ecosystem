from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "gcp-exact.toml"
VERIFIER = ROOT / "scripts" / "verify_gcp_exact.py"


def run_verifier(path: Path) -> tuple[int, dict[str, object]]:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    return proc.returncode, payload


class GcpExactContractTests(unittest.TestCase):
    def test_current_control_plane_is_structurally_admitted_but_not_exact(self) -> None:
        code, payload = run_verifier(CATALOG)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "ALIVE")
        self.assertEqual(payload["standing"], "PARTIAL_ALIVE")
        self.assertFalse(payload["exactness_claim"])
        self.assertFalse(payload["exact_ready"])
        self.assertEqual(payload["required_source_count"], 10)
        self.assertFalse(payload["required_subjects_alive"])

    def test_alive_crown_without_paired_live_closure_is_refused(self) -> None:
        text = CATALOG.read_text(encoding="utf-8")
        text = text.replace('standing = "PARTIAL_ALIVE"', 'standing = "ALIVE"', 1)
        text = text.replace("claim = false", "claim = true", 1)
        text = text.replace("admitted_contract_units = 0", "admitted_contract_units = 1", 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.toml"
            path.write_text(text, encoding="utf-8")
            code, payload = run_verifier(path)
        self.assertEqual(code, 1)
        self.assertIn(
            "REFUSED:EXACTNESS_WITHOUT_COMPLETE_PAIRED_EVIDENCE",
            payload["failures"],
        )
        self.assertIn("REFUSED:ALIVE_WITHOUT_EXACTNESS_CLOSURE", payload["failures"])

    def test_missing_contract_source_is_refused(self) -> None:
        text = CATALOG.read_text(encoding="utf-8")
        block = '''[[contract_sources]]\nid = "audit-logs"\nkind = "public-observation"\nrequired = true\n'''
        self.assertIn(block, text)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.toml"
            path.write_text(text.replace(block, "", 1), encoding="utf-8")
            code, payload = run_verifier(path)
        self.assertEqual(code, 1)
        self.assertTrue(
            any(
                str(failure).startswith("REFUSED:MISSING_CONTRACT_SOURCES:audit-logs")
                for failure in payload["failures"]
            )
        )

    def test_non_exact_subject_sha_is_refused(self) -> None:
        text = CATALOG.read_text(encoding="utf-8")
        text = text.replace(
            'sha = "4c8761273654aded3dc2e000e6246240671c794e"',
            'sha = "main"',
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.toml"
            path.write_text(text, encoding="utf-8")
            code, payload = run_verifier(path)
        self.assertEqual(code, 1)
        self.assertIn("REFUSED:NON_EXACT_SHA:gymact-gcp-runtime", payload["failures"])


if __name__ == "__main__":
    unittest.main()
