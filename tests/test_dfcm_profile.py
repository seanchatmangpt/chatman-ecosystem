import copy
import importlib.util
import pathlib
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_dfcm_profile", ROOT / "scripts" / "verify_dfcm_profile.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)

with (ROOT / "catalog" / "dfcm.toml").open("rb") as handle:
    CATALOG = tomllib.load(handle)
ONTOLOGY = (ROOT / "ontology" / "dfcm.ttl").read_text(encoding="utf-8")
SHAPES = (ROOT / "ontology" / "dfcm.shacl.ttl").read_text(encoding="utf-8")


class DfCMProfileTests(unittest.TestCase):
    def test_canonical_profile_is_admitted(self):
        module.verify(CATALOG, ONTOLOGY, SHAPES)

    def test_failed_edge_must_not_collapse_graph(self):
        mutated = copy.deepcopy(CATALOG)
        mutated["selection"]["failed_edge_invalidates_graph"] = True
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:DFCM_SELECTION_LAW:failed_edge_invalidates_graph"):
            module.verify(mutated, ONTOLOGY, SHAPES)

    def test_irreversible_selection_requires_authority(self):
        mutated = SHAPES.replace("sh:path dfcm:authorityPolicy", "sh:path dfcm:hasBound")
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:DFCM_IRREVERSIBLE_AUTHORITY_SHAPE"):
            module.verify(CATALOG, ONTOLOGY, mutated)

    def test_falsifier_is_required_before_selection(self):
        mutated = SHAPES.replace("sh:path dfcm:hasFalsifier ; sh:minCount 1", "sh:path dfcm:hasFalsifier ; sh:minCount 0")
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:DFCM_FALSIFIER_SHAPE"):
            module.verify(CATALOG, ONTOLOGY, mutated)

    def test_public_ontology_drift_refuses(self):
        mutated = ONTOLOGY.replace("@prefix prov: <http://www.w3.org/ns/prov#> .", "@prefix prov: <https://example.invalid/prov#> .")
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:DFCM_PREFIX_DRIFT:prov"):
            module.verify(CATALOG, mutated, SHAPES)

    def test_public_ontology_redefinition_refuses(self):
        mutated = ONTOLOGY + "\nprov:LocalPlan a owl:Class .\n"
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:PUBLIC_ONTOLOGY_REDEFINED:prov"):
            module.verify(CATALOG, mutated, SHAPES)

    def test_shacl_conformance_cannot_promote_alive(self):
        mutated = SHAPES.replace("this shape cannot promote standing", "this shape promotes standing")
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:DFCM_ADMISSION_STANDING_CONFLATION"):
            module.verify(CATALOG, ONTOLOGY, mutated)

    def test_brce_is_only_do_path(self):
        mutated = copy.deepcopy(CATALOG)
        mutated["authority"]["exclusive_do_path"] = "planner"
        with self.assertRaisesRegex(module.DfCMProfileError, "REFUSED:DFCM_DO_PATH"):
            module.verify(mutated, ONTOLOGY, SHAPES)


if __name__ == "__main__":
    unittest.main()
