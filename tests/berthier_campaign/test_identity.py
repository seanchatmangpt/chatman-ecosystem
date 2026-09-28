"""Tests for Berthier content-addressed campaign identity."""

from __future__ import annotations

import math
import unittest

from scripts.berthier_campaign.identity import canonical_bytes, stable_id


class BerthierIdentityTest(unittest.TestCase):
    def test_mapping_order_does_not_change_identity(self):
        self.assertEqual(
            stable_id("campaign", {"b": 2, "a": 1}),
            stable_id("campaign", {"a": 1, "b": 2}),
        )

    def test_kind_is_part_of_identity_namespace(self):
        payload = {"subject": "release:v26.9.27"}
        self.assertNotEqual(stable_id("campaign", payload), stable_id("doctrine", payload))

    def test_non_finite_numbers_are_refused(self):
        with self.assertRaises(ValueError):
            canonical_bytes({"score": math.nan})

    def test_empty_kind_is_refused(self):
        with self.assertRaises(ValueError):
            stable_id("  ", {"x": 1})


if __name__ == "__main__":
    unittest.main()
