import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location(
    "verify_dfcm_capabilities", ROOT / "scripts" / "verify_dfcm_capabilities.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class DfcmCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = module.verify_capabilities.verify(
            module.verify_capabilities.load_default(ROOT)
        )
        cls.profile = module.load_profile()

    def test_repository_capabilities_satisfy_dfcm_profile(self):
        result = module.validate_all_capabilities(self.items, self.profile)
        self.assertEqual(result["capability_count"], 52)
        self.assertEqual(result["epr_capability_count"], 5)
        self.assertEqual(result["epr_do_count"], 0)
        self.assertEqual(result["standing"], "NONE")

    def test_epr_select_refuses_missing_falsifier_contract(self):
        items = copy.deepcopy(self.items)
        classify = next(
            item
            for item in items
            if item["id"] == "capability:classify-external-paradigm"
        )
        classify["inputs"] = [
            value for value in classify["inputs"] if "explicit falsifier" not in value
        ]
        with self.assertRaisesRegex(
            module.DfcmCapabilityError, "REFUSED:EPR_DFCM_SELECTION_INPUTS"
        ):
            module.validate_all_capabilities(items, self.profile)

    def test_epr_select_refuses_extension_order_drift(self):
        items = copy.deepcopy(self.items)
        classify = next(
            item
            for item in items
            if item["id"] == "capability:classify-external-paradigm"
        )
        classify["inputs"] = [
            "DfCM extension order invent -> reuse"
            if "DfCM extension order" in value
            else value
            for value in classify["inputs"]
        ]
        with self.assertRaisesRegex(
            module.DfcmCapabilityError, "REFUSED:EPR_DFCM_SELECTION_INPUTS"
        ):
            module.validate_all_capabilities(items, self.profile)

    def test_epr_cannot_become_do(self):
        items = copy.deepcopy(self.items)
        observe = next(
            item
            for item in items
            if item["id"] == "capability:observe-external-paradigm-subject"
        )
        observe["class"] = "DO"
        observe["required_authority"] = "modify_external_object"
        observe["broker_required"] = True
        observe["receipt_required"] = True
        with self.assertRaisesRegex(
            module.DfcmCapabilityError, "REFUSED:EPR_CONSEQUENTIAL_DO"
        ):
            module.validate_all_capabilities(items, self.profile)

    def test_non_do_irreversibility_refuses(self):
        items = copy.deepcopy(self.items)
        extract = next(
            item
            for item in items
            if item["id"] == "capability:extract-external-paradigm-units"
        )
        extract["reversible"] = False
        with self.assertRaisesRegex(
            module.DfcmCapabilityError, "REFUSED:DFCM_NON_DO_IRREVERSIBLE"
        ):
            module.validate_all_capabilities(items, self.profile)


if __name__ == "__main__":
    unittest.main()
