import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "capability_control", ROOT / "scripts" / "capability_control.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class CapabilityControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = module.catalog_items()
        cls.index = module.by_id(cls.items)

    def test_all_four_surfaces_preserve_same_capability_semantics(self):
        expected_ids = [item["id"] for item in self.items]
        projections = {
            surface: module.surface_projection(surface, self.items)
            for surface in module.SURFACES
        }
        for surface, projection in projections.items():
            self.assertFalse(projection["consequential_do_claimed"], surface)
            self.assertEqual(
                [item["id"] for item in projection["capabilities"]],
                expected_ids,
                surface,
            )
        for cid in expected_ids:
            contracts = {
                surface: next(
                    item
                    for item in projections[surface]["capabilities"]
                    if item["id"] == cid
                )
                for surface in module.SURFACES
            }
            baseline = contracts["cli"]
            for surface, contract in contracts.items():
                for key in (
                    "class",
                    "required_authority",
                    "broker_required",
                    "receipt_required",
                    "inputs",
                    "outputs",
                    "depends_on",
                    "refusals",
                ):
                    self.assertEqual(contract[key], baseline[key], (cid, surface, key))
                self.assertFalse(contract["authority_from_surface"])

    def test_unknown_capability_and_surface_refuse(self):
        with self.assertRaisesRegex(module.ControlError, "REFUSED:UNKNOWN_CAPABILITY_SURFACE"):
            module.surface_projection("ambient", self.items)
        self.assertNotIn("capability:not-present", self.index)

    def test_dfcm_preserves_reversible_roots_without_selecting(self):
        result = module.dfcm_frontier(
            self.items,
            observed_standing={},
            allowed_authorities={"observe", "classify", "persist_control_plane", "draft"},
            include_do=False,
        )
        self.assertFalse(result["selection_performed"])
        self.assertFalse(result["consequential_do_performed"])
        frontier_ids = {item["id"] for item in result["frontier"]}
        self.assertIn("capability:observe-exact-github-subject", frontier_ids)
        self.assertNotIn("capability:merge-exact-head", frontier_ids)
        merge = next(item for item in result["blocked"] if item["id"] == "capability:merge-exact-head")
        self.assertIn("REFUSED:DO_NOT_ADMITTED_BY_DFCM", merge["reasons"])

    def test_dfcm_do_requires_dependency_closure_and_exact_authority(self):
        standing = {item["id"]: "ALIVE" for item in self.items}
        without_authority = module.dfcm_frontier(
            self.items,
            standing,
            allowed_authorities={"observe", "classify", "persist_control_plane", "draft"},
            include_do=True,
        )
        merge = next(
            item for item in without_authority["blocked"]
            if item["id"] == "capability:merge-exact-head"
        )
        self.assertIn("REFUSED:EXACT_AUTHORITY_MISSING", merge["reasons"])

        with_authority = module.dfcm_frontier(
            self.items,
            standing,
            allowed_authorities={
                "observe",
                "classify",
                "persist_control_plane",
                "draft",
                "modify_external_object",
                "merge",
                "delete",
            },
            include_do=True,
        )
        frontier_ids = {item["id"] for item in with_authority["frontier"]}
        self.assertIn("capability:merge-exact-head", frontier_ids)
        self.assertIn("capability:retire-merged-equivalent-branch", frontier_ids)
        self.assertFalse(with_authority["selection_performed"])
        self.assertFalse(with_authority["consequential_do_performed"])


if __name__ == "__main__":
    unittest.main()
