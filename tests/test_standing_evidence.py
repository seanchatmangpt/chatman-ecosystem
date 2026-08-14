from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_standing_evidence import EvidenceRefusal, verify  # noqa: E402


class StandingEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = ROOT / "release" / "v26.9.1" / "manifest.toml"

    def _write(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False)
        handle.write(text)
        handle.close()
        return Path(handle.name)

    def test_current_unknown_manifest_is_admitted_without_execution_claim(self) -> None:
        receipt = verify(self.source)
        self.assertEqual(receipt["alive_components"], 0)
        self.assertFalse(receipt["do_authority"])

    def test_alive_without_execution_receipt_is_refused(self) -> None:
        text = self.source.read_text().replace('standing = "UNKNOWN"', 'standing = "ALIVE"', 1)
        with self.assertRaisesRegex(EvidenceRefusal, "ALIVE_WITHOUT_EXECUTION_RECEIPT"):
            verify(self._write(text))

    def test_alive_must_bind_exact_admitted_sha(self) -> None:
        source_sha = "16d01cfcbc2a8efe2f074776fa4a4e5fe6701b99"
        text = self.source.read_text().replace(
            'standing = "UNKNOWN"\nrequired = true',
            'standing = "ALIVE"\nexecution_receipt = "github-actions:123"\n'
            'executed_sha = "0000000000000000000000000000000000000000"\nrequired = true',
            1,
        )
        self.assertIn(source_sha, text)
        with self.assertRaisesRegex(EvidenceRefusal, "ALIVE_SUBJECT_IDENTITY_MISMATCH"):
            verify(self._write(text))

    def test_blocked_component_cannot_carry_execution_standing(self) -> None:
        text = self.source.read_text().replace(
            'standing = "UNKNOWN"\nrequired = true',
            'standing = "BLOCKED"\nblocker = "TEST_GATE"\nexecution_receipt = "github-actions:123"\n'
            'executed_sha = "16d01cfcbc2a8efe2f074776fa4a4e5fe6701b99"\nrequired = true',
            1,
        )
        with self.assertRaisesRegex(EvidenceRefusal, "BLOCKED_WITH_EXECUTION_STANDING"):
            verify(self._write(text))


if __name__ == "__main__":
    unittest.main()
