from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "apps" / "ecosystem-cli" / "Cargo.toml"
EXPECTED_REPOSITORY = "https://github.com/seanchatmangpt/clap-noun-verb.git"
EXPECTED_REVISION = "a0f9f79b88e454742ec7c17c91ca31837cabc2c8"
EXPECTED_VERSION = "26.9.1"
EXPECTED_FEATURES = {"mcp", "http", "kubernetes", "container"}


class EcosystemCliDependencyTest(unittest.TestCase):
    def dependency(self) -> dict[str, object]:
        with MANIFEST.open("rb") as handle:
            manifest = tomllib.load(handle)
        dependency = manifest["dependencies"]["clap-noun-verb-deploy"]
        self.assertIsInstance(dependency, dict)
        return dependency

    def test_clap_noun_verb_deploy_is_exact_git_subject_not_sibling_path(self) -> None:
        dependency = self.dependency()
        self.assertNotIn("path", dependency)
        self.assertEqual(dependency.get("git"), EXPECTED_REPOSITORY)
        self.assertEqual(dependency.get("rev"), EXPECTED_REVISION)
        self.assertEqual(dependency.get("version"), EXPECTED_VERSION)

    def test_required_deployment_surfaces_remain_admitted(self) -> None:
        dependency = self.dependency()
        self.assertEqual(set(dependency.get("features", [])), EXPECTED_FEATURES)


if __name__ == "__main__":
    unittest.main()
