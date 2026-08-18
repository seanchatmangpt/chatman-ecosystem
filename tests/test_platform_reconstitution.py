from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_platform_reconstitution",
    ROOT / "scripts" / "verify_platform_reconstitution.py",
)
verify = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


class PlatformReconstitutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.benchmark_path = ROOT / "benchmarks" / "platform-reconstitution" / "v1" / "benchmark.toml"
        self.scenario_path = ROOT / "benchmarks" / "platform-reconstitution" / "v1" / "scenarios" / "regulated-claims.toml"
        self.data = verify.load_toml(self.benchmark_path)
        self.scenario = verify.load_toml(self.scenario_path)

    def codes(self, data=None, scenario=None) -> set[str]:
        findings = verify.validate_benchmark(data or self.data, scenario or self.scenario)
        return {finding.code for finding in findings}

    def test_candidate_contract_is_structurally_admitted(self) -> None:
        self.assertEqual(set(), self.codes())
        self.assertEqual("UNKNOWN", self.data["benchmark"]["standing"])

    def test_ambient_do_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["calculus"]["ambient_do"] = True
        self.assertIn("BENCHMARK_CALCULUS_VIOLATION", self.codes(candidate))

    def test_non_brce_do_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["calculus"]["do_path"] = "agent"
        self.assertIn("BENCHMARK_CALCULUS_VIOLATION", self.codes(candidate))

    def test_missing_projection_class_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["coverage"]["projection_classes"].remove("infrastructure")
        self.assertIn("BENCHMARK_PROJECTION_CLOSURE_MISSING", self.codes(candidate))

    def test_missing_substrate_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["coverage"]["substrates"].remove("airgap")
        self.assertIn("BENCHMARK_SUBSTRATE_CLOSURE_MISSING", self.codes(candidate))

    def test_projection_owned_business_meaning_is_refused(self) -> None:
        scenario = copy.deepcopy(self.scenario)
        scenario["scenario"]["projection_is_source"] = True
        self.assertIn("BENCHMARK_PROJECTION_OWNS_MEANING", self.codes(scenario=scenario))

    def test_incomplete_reconstitution_delete_set_is_refused(self) -> None:
        scenario = copy.deepcopy(self.scenario)
        scenario["reconstitution"]["delete_projection_classes"].remove("application-source")
        self.assertIn("BENCHMARK_RECONSTITUTION_DELETE_SET_INCOMPLETE", self.codes(scenario=scenario))

    def test_duplicate_projection_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["coverage"]["projection_classes"].append("api")
        self.assertIn("BENCHMARK_DUPLICATE_VALUE", self.codes(candidate))

    def test_alive_without_execution_evidence_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["benchmark"]["standing"] = "ALIVE"
        self.assertIn("BENCHMARK_ALIVE_EVIDENCE_MISSING", self.codes(candidate))

    def test_alive_stale_marketplace_subject_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["benchmark"]["standing"] = "ALIVE"
        candidate["evidence"] = self.alive_evidence()
        candidate["evidence"]["executed_marketplace_sha"] = "0" * 40
        self.assertIn("BENCHMARK_EXACT_SUBJECT_MISMATCH", self.codes(candidate))

    def test_alive_requires_all_substrate_execution_evidence(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["benchmark"]["standing"] = "ALIVE"
        candidate["evidence"] = self.alive_evidence()
        candidate["evidence"]["verified_substrates"].remove("gcp")
        self.assertIn("BENCHMARK_ALIVE_SUBSTRATE_EVIDENCE_INCOMPLETE", self.codes(candidate))

    def test_alive_requires_reconstitution_identity(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["benchmark"]["standing"] = "ALIVE"
        candidate["evidence"] = self.alive_evidence()
        candidate["evidence"]["post_reconstitution_digest"] = "sha256:" + "b" * 64
        self.assertIn("BENCHMARK_RECONSTITUTION_DIGEST_MISMATCH", self.codes(candidate))

    def alive_evidence(self) -> dict[str, object]:
        return {
            "executed_marketplace_sha": self.data["marketplace"]["sha"],
            "execution_receipt": "receipt:execution",
            "reconstitution_receipt": "receipt:reconstitution",
            "replay_receipt": "receipt:replay",
            "pre_delete_digest": "sha256:" + "a" * 64,
            "post_reconstitution_digest": "sha256:" + "a" * 64,
            "verified_projections": list(verify.REQUIRED_PROJECTIONS),
            "verified_substrates": list(verify.REQUIRED_SUBSTRATES),
        }


if __name__ == "__main__":
    unittest.main()
