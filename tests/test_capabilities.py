import copy
import importlib.util
import pathlib
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_capabilities", ROOT / "scripts" / "verify_capabilities.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class CapabilityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = module.load(ROOT / "catalog" / "capabilities.toml")
        cls.extension = module.load(ROOT / "catalog" / "capabilities-decision-graph.toml")
        cls.catalog = module.combine([cls.base, cls.extension])
        cls.repositories = module.load(ROOT / "catalog" / "repositories.toml")

    def test_catalogs_and_projections_are_exact(self):
        items = module.verify(self.catalog)
        module.verify_repository_owners(items, self.repositories)
        self.assertEqual(len(items), 39)

        base_items = module.verify(self.base)
        base_expected = module.render(base_items, "catalog/capabilities.toml")
        base_actual = (ROOT / "views" / "generated" / "capabilities.md").read_text()
        self.assertEqual(base_actual, base_expected)

        extension_ids = {item["id"] for item in self.extension["capability"]}
        extension_items = [item for item in items if item["id"] in extension_ids]
        extension_expected = module.render(
            extension_items, "catalog/capabilities-decision-graph.toml"
        )
        extension_actual = (
            ROOT / "views" / "generated" / "capabilities-decision-graph.md"
        ).read_text()
        self.assertEqual(extension_actual, extension_expected)

    def test_do_requires_broker_and_receipt(self):
        candidate = copy.deepcopy(self.catalog)
        do_cap = next(item for item in candidate["capability"] if item["class"] == "DO")
        do_cap["broker_required"] = False
        with self.assertRaisesRegex(module.CapabilityError, "REFUSED:DO_WITHOUT_BROKER"):
            module.verify(candidate)

        candidate = copy.deepcopy(self.catalog)
        do_cap = next(item for item in candidate["capability"] if item["class"] == "DO")
        do_cap["receipt_required"] = False
        with self.assertRaisesRegex(module.CapabilityError, "REFUSED:DO_WITHOUT_RECEIPT"):
            module.verify(candidate)

    def test_surface_semantics_are_closed_across_cli_api_mcp_a2a(self):
        candidate = copy.deepcopy(self.catalog)
        candidate["capability"][0]["interfaces"].remove("a2a")
        with self.assertRaisesRegex(module.CapabilityError, "REFUSED:SURFACE_CLOSURE"):
            module.verify(candidate)

    def test_dependency_graph_refuses_missing_and_cycle(self):
        candidate = copy.deepcopy(self.catalog)
        candidate["capability"][0]["depends_on"] = ["capability:not-present"]
        with self.assertRaisesRegex(module.CapabilityError, "REFUSED:MISSING_CAPABILITY_DEPENDENCY"):
            module.verify(candidate)

        candidate = copy.deepcopy(self.catalog)
        first = candidate["capability"][0]["id"]
        second = candidate["capability"][1]["id"]
        candidate["capability"][0]["depends_on"] = [second]
        candidate["capability"][1]["depends_on"] = [first]
        with self.assertRaisesRegex(module.CapabilityError, "REFUSED:CAPABILITY_CYCLE"):
            module.verify(candidate)

    def test_repository_owner_must_be_declared(self):
        items = module.verify(self.catalog)
        candidate = copy.deepcopy(self.repositories)
        candidate["repository"] = [
            item for item in candidate["repository"] if item["id"] != "repository:autofde-lab"
        ]
        with self.assertRaisesRegex(module.CapabilityError, "REFUSED:UNDECLARED_CAPABILITY_OWNER"):
            module.verify_repository_owners(items, candidate)


if __name__ == "__main__":
    unittest.main()
