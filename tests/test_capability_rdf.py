import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_capabilities", ROOT / "scripts" / "verify_capabilities.py"
)
verify = importlib.util.module_from_spec(VERIFY_SPEC)
assert VERIFY_SPEC.loader is not None
VERIFY_SPEC.loader.exec_module(verify)

RDF_SPEC = importlib.util.spec_from_file_location(
    "render_capability_rdf", ROOT / "scripts" / "render_capability_rdf.py"
)
rdf = importlib.util.module_from_spec(RDF_SPEC)
assert RDF_SPEC.loader is not None
RDF_SPEC.loader.exec_module(rdf)


class CapabilityRdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = verify.verify(verify.load_default(ROOT))

    def test_render_is_deterministic_and_complete(self):
        first = rdf.render(self.items)
        second = rdf.render(self.items)
        self.assertEqual(first, second)
        self.assertEqual(first.count(" a ce:Capability ;"), 39)
        for item in self.items:
            self.assertIn(f'dcterms:identifier "{item["id"]}"', first)
        self.assertIn("ce:capability-broker-consequential-do a ce:Capability", first)
        self.assertIn('ce:requiredAuthority "modify_external_object"', first)
        self.assertIn("ce:brokerRequired true", first)
        self.assertIn("ce:receiptRequired true", first)

    def test_noncanonical_identity_refuses_rdf_term(self):
        with self.assertRaisesRegex(ValueError, "REFUSED:RDF_CAPABILITY_ID"):
            rdf.term("capability:Bad Identity")


if __name__ == "__main__":
    unittest.main()
