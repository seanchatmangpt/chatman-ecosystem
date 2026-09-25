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


class ExternalParadigmInventoryTest(unittest.TestCase):
    def test_specific_pattern_overrides_generic_skill_mapping(self):
        from scripts.extract_external_paradigm_units import inventory_from_surfaces

        pattern_map = json.loads(
            (ROOT / "upstream" / "ecc" / "pattern-map.json").read_text(encoding="utf-8")
        )
        surfaces = {
            "skills": [
                {
                    "name": "continuous-learning-v2",
                    "path": "skills/continuous-learning-v2",
                    "sha": "a" * 40,
                    "type": "dir",
                },
                {
                    "name": "api-design",
                    "path": "skills/api-design",
                    "sha": "b" * 40,
                    "type": "dir",
                },
            ],
            "agents": [],
            "commands": [],
            "hooks": [],
            "workflows": [],
        }
        inventory = inventory_from_surfaces(
            "ecc",
            "affaan-m/ECC",
            "e482e579415fde18357cafce70f177ae19fd7f03",
            surfaces,
            pattern_map,
        )
        by_name = {unit["name"]: unit for unit in inventory["units"]}
        self.assertEqual(
            by_name["continuous-learning-v2"]["classification"]["pattern_id"],
            "ecc.continuous-learning-v2",
        )
        self.assertEqual(
            by_name["continuous-learning-v2"]["classification"]["disposition"],
            "REPLACE",
        )
        self.assertEqual(
            by_name["api-design"]["classification"]["pattern_id"],
            "ecc.skills-agents-commands",
        )
        self.assertEqual(inventory["standing"], "NONE")

    def test_inventory_count_is_derived_from_surfaces(self):
        from scripts.extract_external_paradigm_units import inventory_from_surfaces

        pattern_map = {"entries": []}
        surfaces = {
            "skills": [{"name": "x", "path": "skills/x", "sha": "a" * 40, "type": "dir"}],
            "agents": [{"name": "a.md", "path": "agents/a.md", "sha": "b" * 40, "type": "file"}],
            "commands": [],
            "hooks": [],
            "workflows": [],
        }
        inventory = inventory_from_surfaces(
            "ecc",
            "affaan-m/ECC",
            "e482e579415fde18357cafce70f177ae19fd7f03",
            surfaces,
            pattern_map,
        )
        self.assertEqual(inventory["unit_count"], 2)
        self.assertEqual(inventory["counts"]["skill"], 1)
        self.assertEqual(inventory["counts"]["agent"], 1)
        self.assertEqual(inventory["unmapped_count"], 2)


class ExternalParadigmProjectionTest(unittest.TestCase):
    def test_declared_target_is_not_semantic_equivalence(self):
        from scripts.project_external_paradigm_graph import project_inventory

        inventory = {
            "schema": "chatman.external-paradigm-inventory.v1",
            "supplier": "ecc",
            "repository": "affaan-m/ECC",
            "subject_sha": "e482e579415fde18357cafce70f177ae19fd7f03",
            "standing": "NONE",
            "units": [
                {
                    "id": "ecc:skill:api-design",
                    "kind": "skill",
                    "name": "api-design",
                    "source_path": "skills/api-design/SKILL.md",
                    "state": "CANDIDATE",
                    "standing": "NONE",
                    "classification": {
                        "pattern_id": "ecc.skills-agents-commands",
                        "disposition": "WRAP",
                        "target_capabilities": ["capability:distribute-ggen-pack"],
                    },
                }
            ],
        }
        graph, ttl = project_inventory(
            inventory,
            {"capability:distribute-ggen-pack"},
        )
        self.assertEqual(graph["edge_count"], 1)
        self.assertEqual(graph["edges"][0]["semantic_equivalence"], "UNCLAIMED")
        self.assertEqual(graph["standing"], "NONE")
        self.assertIn("prov:wasDerivedFrom", ttl)

    def test_dangling_internal_target_is_refused(self):
        from scripts.project_external_paradigm_graph import (
            ProjectionRefusal,
            project_inventory,
        )

        inventory = {
            "schema": "chatman.external-paradigm-inventory.v1",
            "supplier": "ecc",
            "repository": "affaan-m/ECC",
            "subject_sha": "e482e579415fde18357cafce70f177ae19fd7f03",
            "standing": "NONE",
            "units": [
                {
                    "id": "ecc:skill:x",
                    "kind": "skill",
                    "name": "x",
                    "source_path": "skills/x/SKILL.md",
                    "state": "CANDIDATE",
                    "standing": "NONE",
                    "classification": {
                        "pattern_id": "ecc.skills-agents-commands",
                        "disposition": "WRAP",
                        "target_capabilities": ["capability:does-not-exist"],
                    },
                }
            ],
        }
        with self.assertRaisesRegex(ProjectionRefusal, "DANGLING_TARGET_CAPABILITY"):
            project_inventory(inventory, set())


if __name__ == "__main__":
    unittest.main()
