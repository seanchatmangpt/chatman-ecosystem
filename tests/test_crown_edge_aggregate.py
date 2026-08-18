from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_crown_edges_aggregate", ROOT / "scripts" / "verify_crown_edges.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class CrownEdgeAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = mod.load(ROOT / "release" / "v26.9.1" / "crown-edges.toml")

    def test_root_standing_cannot_be_manually_promoted_above_unknown_edges(self):
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["standing"] = "PARTIAL_ALIVE"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_STANDING_DERIVATION"):
            mod.verify(candidate)

    def test_build_break_dominates_unknown_in_the_same_way_as_release_graph(self):
        candidate = copy.deepcopy(self.data)
        edge = next(
            item
            for item in candidate["edges"]
            if item["id"] == "bcinr_cmca_mfw_consumption"
        )
        sha = "a" * 40
        edge["standing"] = "BUILD_BROKEN"
        edge["blocker"] = "NON_MUTANT_BASELINE_EXIT_101"
        edge["evidence"] = [
            {
                "repository": "example/bcinr",
                "ref": "main",
                "sha": sha,
                "executed_sha": sha,
                "receipt": "test:cmca-failure",
                "verifier": "test:cmca-verifier",
                "replay": "test:cmca-replay",
                "authority_class": "SELECT",
            }
        ]
        candidate["release_crown"]["standing"] = "BUILD_BROKEN"
        report = mod.verify(candidate)
        self.assertEqual("BUILD_BROKEN", report["edge_set_standing"])
        self.assertFalse(report["mandatory_edges_ready"])
        self.assertFalse(report["release_candidate_ready"])


if __name__ == "__main__":
    unittest.main()
