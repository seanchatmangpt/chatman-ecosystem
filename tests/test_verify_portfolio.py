from __future__ import annotations

import copy
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_portfolio import (  # noqa: E402
    PortfolioRefusal,
    build_report,
    classify,
    manufacture_receipt,
    replay_receipt,
    row_kind,
    validate,
    validate_pagination_evidence,
)


def load(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


class VerifyPortfolioTests(unittest.TestCase):
    def setUp(self) -> None:
        base = ROOT / "release" / "v26.9.1"
        self.policy = load(base / "fleet-policy.toml")
        self.manifest = load(base / "manifest.toml")
        self.candidates = load(base / "candidates.toml")

    def test_current_release_state_is_clean(self) -> None:
        self.assertEqual(validate(self.policy, self.manifest, self.candidates), [])

    def test_legacy_rows_are_typed_by_candidate_sha_presence(self) -> None:
        rows = self.candidates["candidates"]
        kinds = {row["component"]: row_kind(row) for row in rows}
        self.assertEqual(kinds["ggen"], "CANDIDATE")
        self.assertEqual(kinds["fdegym"], "CANDIDATE")
        self.assertEqual(kinds["gymact"], "OBSERVATION")
        self.assertEqual(kinds["autofde-lab"], "OBSERVATION")

    def test_report_counts_candidates_separately_from_observations(self) -> None:
        report = build_report(self.policy, self.manifest, self.candidates)
        self.assertEqual(report["candidate_count"], 2)
        self.assertEqual(report["observation_count"], 13)
        self.assertEqual(report["standing"], "ALIVE")
        self.assertEqual(report["findings"], [])

    def test_observation_drift_does_not_require_candidate_ci(self) -> None:
        ledger = copy.deepcopy(self.candidates)
        observation = next(row for row in ledger["candidates"] if row["component"] == "gymact")
        observation["admitted_sha"] = "a" * 40
        observation.pop("candidate_sha", None)
        observation.pop("exact_head_ci", None)
        findings = validate(self.policy, self.manifest, ledger)
        codes = {finding["code"] for finding in findings}
        self.assertNotIn("CANDIDATE_ADMITTED_SHA_MISMATCH", codes)
        self.assertNotIn("CANDIDATE_EXACT_HEAD_CI_NOT_SUCCESS", codes)

    def test_observation_cannot_smuggle_ci_authority(self) -> None:
        ledger = copy.deepcopy(self.candidates)
        observation = next(row for row in ledger["candidates"] if row["component"] == "gymact")
        observation["exact_head_ci"] = "SUCCESS"
        findings = validate(self.policy, self.manifest, ledger)
        self.assertIn("OBSERVATION_CI_AUTHORITY_INVALID", {finding["code"] for finding in findings})

    def test_explicit_kind_must_match_structural_shape(self) -> None:
        row = copy.deepcopy(self.candidates["candidates"][0])
        row["kind"] = "OBSERVATION"
        with self.assertRaisesRegex(PortfolioRefusal, "LEDGER_KIND_SHAPE_MISMATCH"):
            row_kind(row)

    def test_invalid_explicit_kind_is_refused(self) -> None:
        row = copy.deepcopy(self.candidates["candidates"][0])
        row["kind"] = "PROMOTED_BY_VIBES"
        with self.assertRaisesRegex(PortfolioRefusal, "LEDGER_KIND_INVALID"):
            row_kind(row)

    def test_receipt_is_deterministic_and_replayable(self) -> None:
        report = build_report(self.policy, self.manifest, self.candidates)
        first = manufacture_receipt(report)
        second = manufacture_receipt(report)
        self.assertEqual(first, second)
        self.assertEqual(replay_receipt(first), first)

    def test_receipt_tamper_is_refused(self) -> None:
        report = build_report(self.policy, self.manifest, self.candidates)
        receipt = manufacture_receipt(report)
        receipt["candidate_count"] += 1
        with self.assertRaisesRegex(PortfolioRefusal, "PORTFOLIO_RECEIPT_TAMPERED"):
            replay_receipt(receipt)

    def test_blocked_report_cannot_replay_as_alive(self) -> None:
        report = build_report(self.policy, self.manifest, self.candidates)
        report["standing"] = "BLOCKED"
        report["findings"] = [{"code": "X", "subject": "x", "detail": "x"}]
        receipt = manufacture_receipt(report)
        with self.assertRaisesRegex(PortfolioRefusal, "PORTFOLIO_RECEIPT_NOT_ALIVE"):
            replay_receipt(receipt)

    def test_classify_composition_root_is_crown(self) -> None:
        root = self.policy["fleet"]["composition_root"]
        self.assertEqual(classify(self.policy, root), "CROWN")

    def test_classify_required_repository(self) -> None:
        repo = self.policy["dispositions"]["required"][0]
        self.assertEqual(classify(self.policy, repo), "REQUIRED")

    def test_classify_unknown_repository_falls_back_to_default(self) -> None:
        result = classify(self.policy, "seanchatmangpt/definitely-not-in-any-list")
        self.assertEqual(result, self.policy["fleet"]["default_disposition"])
        self.assertEqual(result, "OUT_OF_RELEASE")

    def test_pagination_evidence_valid_when_count_in_range(self) -> None:
        fleet = {"observed_owned_repository_count": 355, "nonempty_pages": 4, "page_size": 100, "next_page_empty": True}
        self.assertEqual(validate_pagination_evidence(fleet), [])

    def test_pagination_evidence_flags_count_below_page_floor(self) -> None:
        fleet = {"observed_owned_repository_count": 250, "nonempty_pages": 4, "page_size": 100, "next_page_empty": True}
        codes = {f["code"] for f in validate_pagination_evidence(fleet)}
        self.assertIn("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH", codes)

    def test_pagination_evidence_flags_missing_terminator(self) -> None:
        fleet = {"observed_owned_repository_count": 355, "nonempty_pages": 4, "page_size": 100, "next_page_empty": False}
        codes = {f["code"] for f in validate_pagination_evidence(fleet)}
        self.assertIn("FLEET_PAGINATION_TERMINATOR_INVALID", codes)

    def test_pagination_evidence_flags_invalid_types(self) -> None:
        fleet = {"observed_owned_repository_count": "many", "nonempty_pages": 0, "page_size": -1, "next_page_empty": None}
        codes = {f["code"] for f in validate_pagination_evidence(fleet)}
        self.assertIn("FLEET_OBSERVED_COUNT_INVALID", codes)
        self.assertIn("FLEET_NONEMPTY_PAGES_INVALID", codes)
        self.assertIn("FLEET_PAGE_SIZE_INVALID", codes)
        self.assertIn("FLEET_PAGINATION_TERMINATOR_INVALID", codes)
        self.assertNotIn("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH", codes)

    def test_repository_in_two_dispositions_is_flagged(self) -> None:
        policy = copy.deepcopy(self.policy)
        dupe = policy["dispositions"]["required"][0]
        policy["dispositions"]["adapter"].append(dupe)
        codes = {f["code"] for f in validate(policy, self.manifest, self.candidates)}
        self.assertIn("FLEET_REPOSITORY_MULTI_DISPOSITION", codes)

    def test_repository_outside_owner_namespace_is_flagged(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["dispositions"]["required"].append("someoneelse/rogue-repo")
        codes = {f["code"] for f in validate(policy, self.manifest, self.candidates)}
        self.assertIn("FLEET_REPOSITORY_OWNER_INVALID", codes)

    def test_candidate_sha_equal_to_admitted_sha_is_flagged_not_distinct(self) -> None:
        ledger = copy.deepcopy(self.candidates)
        first = ledger["candidates"][0]
        component_id = first["component"]
        admitted_sha = next(c["sha"] for c in self.manifest["components"] if c["id"] == component_id)
        first["candidate_sha"] = admitted_sha
        codes = {f["code"] for f in validate(self.policy, self.manifest, ledger)}
        self.assertIn("CANDIDATE_NOT_DISTINCT", codes)

    def test_candidate_for_unadmitted_component_is_flagged(self) -> None:
        ledger = copy.deepcopy(self.candidates)
        ledger["candidates"][0]["component"] = "not-a-real-component"
        codes = {f["code"] for f in validate(self.policy, self.manifest, ledger)}
        self.assertIn("CANDIDATE_COMPONENT_NOT_ADMITTED", codes)

    def test_duplicate_candidate_component_is_flagged(self) -> None:
        ledger = copy.deepcopy(self.candidates)
        ledger["candidates"].append(dict(ledger["candidates"][0]))
        codes = {f["code"] for f in validate(self.policy, self.manifest, ledger)}
        self.assertIn("CANDIDATE_DUPLICATE_COMPONENT", codes)

    def test_candidate_release_standing_overclaim_is_flagged(self) -> None:
        ledger = copy.deepcopy(self.candidates)
        ledger["candidates"][0]["release_standing"] = "ALIVE"
        codes = {f["code"] for f in validate(self.policy, self.manifest, ledger)}
        self.assertIn("CANDIDATE_RELEASE_STANDING_OVERCLAIM", codes)

    def test_default_disposition_not_fail_safe_is_flagged(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["fleet"]["default_release_blocking"] = True
        codes = {f["code"] for f in validate(policy, self.manifest, self.candidates)}
        self.assertIn("FLEET_DEFAULT_NOT_FAIL_SAFE", codes)


if __name__ == "__main__":
    unittest.main()
