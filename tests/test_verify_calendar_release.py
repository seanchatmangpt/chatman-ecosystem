from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("verify_calendar_release", Path(__file__).parents[1] / "scripts" / "verify_calendar_release.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

class CalendarReleaseTests(unittest.TestCase):
    def test_calendar_version_maps_to_release_date(self):
        self.assertEqual(mod.canonical_release("26.8.23"), ("v26.8.23", mod.dt.date(2026, 8, 23)))

    def test_current_release_documents_verify(self):
        report = mod.verify(Path(__file__).parents[1] / "release" / "v26.8.23")
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["requirement_count"], 8)
        self.assertEqual(report["standing"], "PARTIAL_ALIVE")

    def test_ambient_do_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.toml").write_text("""[release]\nversion=\"26.8.23\"\ntarget_date=\"2026-08-23\"\nstanding=\"UNKNOWN\"\n[[components]]\nid=\"x\"\nsha=\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"\nstanding=\"UNKNOWN\"\ndepends_on=[]\n""")
            (root / "requirements.toml").write_text("""[release_requirements]\nrequired_gates=[\"exact_subject\",\"process_intelligence_methodology\",\"deterministic_manufacture\",\"independent_verification\",\"receipt_replay\",\"brce_only_do\",\"failure_dominance\"]\n[[requirements]]\nid=\"x\"\nsubject=\"o/r@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\"\nstanding=\"UNKNOWN\"\nauthority=[\"DO\"]\nfalsifier=\"refuse\"\n""")
            report = mod.verify(root)
            self.assertIn("AMBIENT_DO_FORBIDDEN:x", report["errors"])

if __name__ == "__main__":
    unittest.main()
