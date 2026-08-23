from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_release", ROOT / "scripts" / "verify_release.py")
verify_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = verify_release
SPEC.loader.exec_module(verify_release)


class ReleaseControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_path = ROOT / "release" / "v26.9.1" / "manifest.toml"
        self.data = verify_release.load_manifest(self.manifest_path)

    def test_manifest_is_structurally_admitted(self) -> None:
        self.assertEqual([], verify_release.validate_manifest(self.data))

    def test_crown_escalates_exact_build_breaks_over_runtime_blocks(self) -> None:
        self.assertEqual("BUILD_BROKEN", verify_release.crown_standing(self.data, []))

    def test_runtime_frontier_is_required_and_fail_closed(self) -> None:
        by_id = {component["id"]: component for component in self.data["components"]}
        self.assertIn("orchestration", self.data["release"]["required_roles"])
        self.assertEqual("orchestration", by_id["mfw"]["role"])
        self.assertTrue(by_id["mfw"]["required"])
        self.assertEqual("BLOCKED", by_id["mfw"]["standing"])
        self.assertEqual("GITHUB_ACTIONS_BILLING_OR_SPENDING_LIMIT", by_id["mfw"]["blocker"])
        self.assertEqual("BLOCKED", by_id["gymact"]["standing"])
        self.assertEqual("GITHUB_ACTIONS_BILLING_OR_SPENDING_LIMIT", by_id["gymact"]["blocker"])
        self.assertIn("mfw", by_id["fdegym"]["depends_on"])

    def test_marketplace_exact_subject_is_alive_only_with_owning_receipt(self) -> None:
        by_id = {component["id"]: component for component in self.data["components"]}
        marketplace = by_id["ggen-marketplace"]
        self.assertEqual("ALIVE", marketplace["standing"])
        self.assertEqual("ceb2b69ad1dc1bf0906a1979a9e18c53245181f3", marketplace["sha"])
        self.assertEqual(marketplace["sha"], marketplace["executed_sha"])
        self.assertEqual("github-actions:31923773826", marketplace["execution_receipt"])
        self.assertNotIn("blocker", marketplace)

    def test_autofde_lab_exact_failure_receipt_is_preserved(self) -> None:
        by_id = {component["id"]: component for component in self.data["components"]}
        lab = by_id["autofde-lab"]
        self.assertEqual("BUILD_BROKEN", lab["standing"])
        self.assertEqual("87d719f441ded3af123a73b95825d5f2847f9c66", lab["sha"])
        self.assertEqual(lab["sha"], lab["executed_sha"])
        self.assertEqual("github-actions:31909415315", lab["execution_receipt"])
        self.assertEqual("REQUIRED_CI_GATES_FAILED", lab["blocker"])

    def test_affidavit_exact_subject_is_alive_only_with_owning_receipt(self) -> None:
        by_id = {component["id"]: component for component in self.data["components"]}
        affidavit = by_id["affidavit"]
        self.assertEqual("ALIVE", affidavit["standing"])
        self.assertEqual("feat/ecosystem-standing-receipts-20260812", affidavit["ref"])
        self.assertEqual("external", affidavit["ref_check"])
        self.assertEqual("5dc78f113e60ba95a4b4594a6da3511334e86024", affidavit["sha"])
        self.assertEqual(affidavit["sha"], affidavit["executed_sha"])
        self.assertEqual("github-actions:31674647112", affidavit["execution_receipt"])
        self.assertNotIn("blocker", affidavit)

    def test_star_toml_exact_failure_receipt_is_preserved(self) -> None:
        by_id = {component["id"]: component for component in self.data["components"]}
        star_toml = by_id["star-toml"]
        self.assertEqual("BUILD_BROKEN", star_toml["standing"])
        self.assertEqual("8395515cf8e68bfdc9edff49fb358c4f1da7c795", star_toml["sha"])
        self.assertEqual(star_toml["sha"], star_toml["executed_sha"])
        self.assertEqual("github-actions:30680591983", star_toml["execution_receipt"])
        self.assertEqual("REQUIRED_CI_GATES_FAILED", star_toml["blocker"])

    def test_autofde_exact_main_execution_receipt_is_preserved(self) -> None:
        by_id = {component["id"]: component for component in self.data["components"]}
        autofde = by_id["autofde"]
        self.assertEqual("ALIVE", autofde["standing"])
        self.assertEqual("c3f8abc2e83388b5bdb6cc1bbb8cd19a987c19c7", autofde["sha"])
        self.assertEqual(autofde["sha"], autofde["executed_sha"])
        self.assertEqual("github-actions:31775830421", autofde["execution_receipt"])
        self.assertNotIn("blocker", autofde)

    def test_github_json_uses_available_read_token(self) -> None:
        captured: dict[str, str | None] = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{}"

        def fake_urlopen(request, timeout):
            captured["authorization"] = request.get_header("Authorization")
            self.assertEqual(1.5, timeout)
            return Response()

        with (
            mock.patch.dict(verify_release.os.environ, {"GITHUB_TOKEN": "test-read-token"}, clear=True),
            mock.patch.object(verify_release.urllib.request, "urlopen", side_effect=fake_urlopen),
        ):
            self.assertEqual({}, verify_release._github_json("https://api.github.com/example", 1.5))
        self.assertEqual("Bearer test-read-token", captured["authorization"])

        captured.clear()
        with (
            mock.patch.dict(verify_release.os.environ, {}, clear=True),
            mock.patch.object(verify_release.urllib.request, "urlopen", side_effect=fake_urlopen),
        ):
            self.assertEqual({}, verify_release._github_json("https://api.github.com/example", 1.5))
        self.assertIsNone(captured["authorization"])

    def test_branch_advancement_does_not_invalidate_admitted_sha(self) -> None:
        candidate = {
            "components": [
                {
                    "id": "x",
                    "repository": "seanchatmangpt/x",
                    "ref": "main",
                    "ref_check": "github",
                    "sha": "a" * 40,
                    "required": True,
                }
            ]
        }
        with (
            mock.patch.object(verify_release, "resolve_ref", return_value="b" * 40),
            mock.patch.object(verify_release, "compare_ref_lineage", return_value="ahead"),
        ):
            findings, coverage = verify_release.check_ref_drift(candidate)
        self.assertEqual([], findings)
        self.assertEqual(1, coverage["github_live"])
        self.assertEqual(0, coverage["github_exact"])
        self.assertEqual(1, coverage["github_advanced"])

    def test_branch_divergence_refuses_admitted_lineage(self) -> None:
        candidate = {
            "components": [
                {
                    "id": "x",
                    "repository": "seanchatmangpt/x",
                    "ref": "main",
                    "ref_check": "github",
                    "sha": "a" * 40,
                    "required": True,
                }
            ]
        }
        with (
            mock.patch.object(verify_release, "resolve_ref", return_value="b" * 40),
            mock.patch.object(verify_release, "compare_ref_lineage", return_value="diverged"),
        ):
            findings, coverage = verify_release.check_ref_drift(candidate)
        self.assertEqual(1, coverage["github_live"])
        self.assertEqual(0, coverage["github_advanced"])
        self.assertEqual(1, len(findings))
        self.assertEqual("ECOSYSTEM_REF_LINEAGE_VIOLATION", findings[0].code)

    def test_exact_ref_head_counts_as_exact_lineage(self) -> None:
        candidate = {
            "components": [
                {
                    "id": "x",
                    "repository": "seanchatmangpt/x",
                    "ref": "main",
                    "ref_check": "github",
                    "sha": "a" * 40,
                    "required": True,
                }
            ]
        }
        with mock.patch.object(verify_release, "resolve_ref", return_value="a" * 40):
            findings, coverage = verify_release.check_ref_drift(candidate)
        self.assertEqual([], findings)
        self.assertEqual(1, coverage["github_exact"])
        self.assertEqual(0, coverage["github_advanced"])

    def test_removing_mfw_from_components_refuses_required_role(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["components"] = [component for component in candidate["components"] if component["id"] != "mfw"]
        candidate["external_ref_observations"] = [
            observation
            for observation in candidate["external_ref_observations"]
            if observation["component"] != "mfw"
        ]
        codes = {finding.code for finding in verify_release.validate_manifest(candidate)}
        self.assertIn("ECOSYSTEM_REQUIRED_ROLE_MISSING", codes)

    def test_duplicate_repository_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["components"][1]["repository"] = candidate["components"][0]["repository"]
        codes = {finding.code for finding in verify_release.validate_manifest(candidate)}
        self.assertIn("ECOSYSTEM_DUPLICATE_REPOSITORY", codes)

    def test_invalid_sha_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["components"][0]["sha"] = "main"
        codes = {finding.code for finding in verify_release.validate_manifest(candidate)}
        self.assertIn("ECOSYSTEM_SHA_INVALID", codes)

    def test_dependency_cycle_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        by_id = {component["id"]: component for component in candidate["components"]}
        by_id["ggen"]["depends_on"] = ["ggen-marketplace"]
        codes = {finding.code for finding in verify_release.validate_manifest(candidate)}
        self.assertIn("ECOSYSTEM_DEPENDENCY_CYCLE", codes)

    def test_external_ref_observation_is_required_and_exact(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["external_ref_observations"][0]["sha"] = "0" * 40
        codes = {finding.code for finding in verify_release.validate_manifest(candidate)}
        self.assertIn("ECOSYSTEM_EXTERNAL_REF_EVIDENCE_MISMATCH", codes)

    def test_unadmitted_dependency_is_refused(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["components"][0]["depends_on"] = ["nonexistent"]
        codes = {finding.code for finding in verify_release.validate_manifest(candidate)}
        self.assertIn("ECOSYSTEM_DEPENDENCY_NOT_ADMITTED", codes)


if __name__ == "__main__":
    unittest.main()
