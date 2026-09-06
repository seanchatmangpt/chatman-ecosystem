from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class WestContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = yaml.safe_load((ROOT / "west.yml").read_text(encoding="utf-8"))
        cls.policy = tomllib.loads((ROOT / "catalog/west.toml").read_text(encoding="utf-8"))
        cls.import_specs = cls.root["manifest"]["self"]["import"]
        cls.import_paths = [spec["file"] if isinstance(spec, dict) else spec for spec in cls.import_specs]
        cls.imports = [yaml.safe_load((ROOT / path).read_text(encoding="utf-8")) for path in cls.import_paths]
        cls.projects = list(cls.root["manifest"]["projects"])
        for imported in cls.imports:
            cls.projects.extend(imported["manifest"].get("projects", []))

    def test_manifest_uses_versioned_imports_extensions_and_prefixing(self) -> None:
        manifest = self.root["manifest"]
        self.assertEqual(manifest["version"], "1.2")
        self.assertEqual(len(self.import_paths), 3)
        self.assertEqual(manifest["self"]["west-commands"], "west-commands.yml")
        self.assertTrue(any(isinstance(s, dict) and s.get("path-prefix") == "portfolio" for s in self.import_specs))

    def test_default_frontier_excludes_reversible_portfolio_and_corpus(self) -> None:
        filters = set(self.root["manifest"]["group-filter"])
        self.assertTrue({"-portfolio", "-external", "-rejected", "-unsupported"} <= filters)
        release_projects = [p for p in self.projects if "release-v26-9-1" in p.get("groups", [])]
        self.assertEqual(len(release_projects), 16)

    def test_feature_surface_is_exercised_not_just_declared(self) -> None:
        self.assertTrue(any(project.get("submodules") is True for project in self.projects))
        self.assertTrue(any(project.get("clone-depth") == 1 for project in self.projects))
        self.assertTrue(any("repo-path" in project for project in self.projects))
        self.assertTrue(all(self.policy["west_features"].values()))

    def test_public_portfolio_is_preserved_but_inactive(self) -> None:
        portfolio = [p for p in self.projects if "observed-github" in p.get("groups", [])]
        self.assertEqual(len(portfolio), 284)
        self.assertEqual(self.policy["inventory"]["public_repository_count"], 308)
        self.assertTrue(all("portfolio" in p.get("groups", []) for p in portfolio))
        self.assertEqual(sum("empty" in p.get("groups", []) for p in portfolio), 8)

    def test_extension_commands_have_no_do_authority(self) -> None:
        text = (ROOT / "scripts/west/chateco.py").read_text(encoding="utf-8")
        self.assertIn('"authority": "SELECT_ONLY"', text)
        self.assertIn('"authority": "CONSTRUCT_ONLY"', text)
        self.assertIn('"actuation": "none"', text)
        self.assertNotIn("git push", text)


if __name__ == "__main__":
    unittest.main()
