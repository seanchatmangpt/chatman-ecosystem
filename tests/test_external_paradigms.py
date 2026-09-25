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


class ExternalParadigmDeltaTest(unittest.TestCase):
    def test_added_skill_is_candidate_unit(self):
        from scripts.detect_external_paradigm_delta import classify_compare

        pattern_map = json.loads(
            (ROOT / "upstream" / "ecc" / "pattern-map.json").read_text(encoding="utf-8")
        )
        result = classify_compare(
            [
                {
                    "filename": "skills/new-paradigm/SKILL.md",
                    "status": "added",
                }
            ],
            pattern_map,
        )
        self.assertIn("skills/new-paradigm/", result["new_units"])
        self.assertIn(
            "ecc.skills-agents-commands",
            result["matched_patterns"],
        )

    def test_unmapped_architecture_file_is_visible(self):
        from scripts.detect_external_paradigm_delta import classify_compare

        pattern_map = {"entries": []}
        result = classify_compare(
            [
                {
                    "filename": "docs/architecture/new-control-plane.md",
                    "status": "added",
                }
            ],
            pattern_map,
        )
        self.assertEqual(
            result["unmapped_files"],
            ["docs/architecture/new-control-plane.md"],
        )


if __name__ == "__main__":
    unittest.main()
