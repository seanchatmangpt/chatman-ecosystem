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

    def _mutate_first_component(self, replacement: str) -> str:
        text = self.source.read_text()
        marker = (
            'id = "open-ontologies"\n'
            'repository = "seanchatmangpt/open-ontologies"\n'
            'ref = "main"\n'
            'ref_check = "github"\n'
            'sha = "16d01cfcbc2a8efe2f074776fa4a4e5fe6701b99"\n'
            'role = "public-ontology"\n'
            'disposition = "REQUIRED"\n'
            'standing = "UNKNOWN"\n'
            'required = true'
        )
        self.assertIn(marker, text)
        return text.replace(marker, marker.replace('standing = "UNKNOWN"\nrequired = true', replacement), 1)

    def test_current_manifest_admits_only_earned_execution_claims(self) -> None:
        receipt = verify(self.source)
        self.assertEqual(receipt["alive_components"], 1)
        self.assertEqual(receipt["blocked_components"], 2)
        self.assertEqual(receipt["build_broken_components"], 1)
        self.assertFalse(receipt["do_authority"])

    def test_alive_without_execution_receipt_is_refused(self) -> None:
        text = self._mutate_first_component('standing = "ALIVE"\nrequired = true')
        with self.assertRaisesRegex(EvidenceRefusal, "ALIVE_WITHOUT_EXECUTION_RECEIPT"):
            verify(self._write(text))

    def test_alive_must_bind_exact_admitted_sha(self) -> None:
        text = self._mutate_first_component(
            'standing = "ALIVE"\nexecution_receipt = "github-actions:123"\n'
            'executed_sha = "0000000000000000000000000000000000000000"\nrequired = true'
        )
        with self.assertRaisesRegex(EvidenceRefusal, "ALIVE_SUBJECT_IDENTITY_MISMATCH"):
            verify(self._write(text))

    def test_blocked_component_cannot_carry_execution_standing(self) -> None:
        text = self._mutate_first_component(
            'standing = "BLOCKED"\nblocker = "TEST_GATE"\nexecution_receipt = "github-actions:123"\n'
            'executed_sha = "16d01cfcbc2a8efe2f074776fa4a4e5fe6701b99"\nrequired = true'
        )
        with self.assertRaisesRegex(EvidenceRefusal, "BLOCKED_WITH_EXECUTION_STANDING"):
            verify(self._write(text))

    def test_build_broken_requires_execution_receipt(self) -> None:
        text = self._mutate_first_component(
            'standing = "BUILD_BROKEN"\nblocker = "TEST_FAILURE"\nrequired = true'
        )
        with self.assertRaisesRegex(EvidenceRefusal, "BUILD_BROKEN_WITHOUT_EXECUTION_RECEIPT"):
            verify(self._write(text))

    def test_build_broken_must_bind_exact_admitted_sha(self) -> None:
        text = self._mutate_first_component(
            'standing = "BUILD_BROKEN"\nblocker = "TEST_FAILURE"\n'
            'execution_receipt = "github-actions:123"\n'
            'executed_sha = "0000000000000000000000000000000000000000"\nrequired = true'
        )
        with self.assertRaisesRegex(EvidenceRefusal, "BUILD_BROKEN_SUBJECT_IDENTITY_MISMATCH"):
            verify(self._write(text))

    def test_build_broken_requires_typed_reason(self) -> None:
        text = self._mutate_first_component(
            'standing = "BUILD_BROKEN"\nexecution_receipt = "github-actions:123"\n'
            'executed_sha = "16d01cfcbc2a8efe2f074776fa4a4e5fe6701b99"\nrequired = true'
        )
        with self.assertRaisesRegex(EvidenceRefusal, "BUILD_BROKEN_WITHOUT_REASON"):
            verify(self._write(text))


if __name__ == "__main__":
    unittest.main()
