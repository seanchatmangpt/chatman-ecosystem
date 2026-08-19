import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_capability_ontology", ROOT / "scripts" / "verify_capability_ontology.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)
ONTOLOGY = (ROOT / "ontology" / "capabilities.ttl").read_text(encoding="utf-8")


class CapabilityOntologyTests(unittest.TestCase):
    def test_public_custom_boundary_is_admitted(self):
        module.verify_text(ONTOLOGY)

    def test_public_prefix_drift_refuses(self):
        mutated = ONTOLOGY.replace(
            "@prefix prov: <http://www.w3.org/ns/prov#> .",
            "@prefix prov: <https://example.invalid/prov#> .",
        )
        with self.assertRaisesRegex(module.OntologyError, "REFUSED:ONTOLOGY_PREFIX_DRIFT:prov"):
            module.verify_text(mutated)

    def test_public_redefinition_refuses(self):
        mutated = ONTOLOGY + "\nprov:Capability a owl:Class .\n"
        with self.assertRaisesRegex(module.OntologyError, "REFUSED:PUBLIC_ONTOLOGY_REDEFINED:prov"):
            module.verify_text(mutated)

    def test_surface_or_identity_law_drift_refuses(self):
        mutated = ONTOLOGY.replace("sh:minCount 4", "sh:minCount 3")
        with self.assertRaisesRegex(module.OntologyError, "REFUSED:ONTOLOGY_SURFACE_CLOSURE"):
            module.verify_text(mutated)

        mutated = ONTOLOGY.replace(
            "Planner != Policy != Role != Agent != Authority",
            "Planner and authority are equivalent",
        )
        with self.assertRaisesRegex(module.OntologyError, "REFUSED:ONTOLOGY_LAW_MISSING"):
            module.verify_text(mutated)


if __name__ == "__main__":
    unittest.main()
