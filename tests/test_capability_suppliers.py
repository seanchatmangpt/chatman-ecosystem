import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_capability_suppliers", ROOT / "scripts" / "verify_capability_suppliers.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class CapabilitySupplierTests(unittest.TestCase):
    def test_fleet_owner_closure(self):
        result = module.validate()
        self.assertEqual(result["repository_count"], 32)
        self.assertEqual(result["supplier_count"], 31)
        self.assertEqual(result["capability_count"], 83)
        self.assertEqual(result["standing"], "NONE")


if __name__ == "__main__":
    unittest.main()
