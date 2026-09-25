import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify_external_paradigms import ParadigmRefusal, validate_registry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "upstream" / "paradigms.json"


class ExternalParadigmsTest(unittest.TestCase):
    def test_repository_registry_is_well_formed(self):
        result = validate_registry(REGISTRY, ROOT)
        self.assertEqual(result["supplier_count"], 1)
        self.assertGreater(result["pattern_count"], 0)
        self.assertEqual(result["standing"], "NONE")

    def test_mutable_ref_is_refused(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        registry["suppliers"][0]["pin"]["sha"] = "main"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "upstream").mkdir()
            bad = tmp_root / "upstream" / "paradigms.json"
            bad.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(ParadigmRefusal, "MUTABLE_OR_INVALID_SHA"):
                validate_registry(bad, tmp_root)

    def test_supplier_cannot_self_grant_standing(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        registry["suppliers"][0]["standing"] = "ALIVE"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "upstream").mkdir()
            bad = tmp_root / "upstream" / "paradigms.json"
            bad.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(ParadigmRefusal, "SUPPLIER_SELF_STANDING"):
                validate_registry(bad, tmp_root)


if __name__ == "__main__":
    unittest.main()
