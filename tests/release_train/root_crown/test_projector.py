"""Projector: deterministic, verify_release-compatible, drift refused."""

from __future__ import annotations

import tomllib
import unittest

from _support import committed_tree, dump, load

from scripts import verify_release
from scripts.release_train.root_crown import projector
from scripts.release_train.root_crown.model import PROJECTOR_RULES, code_of


class ProjectorTest(unittest.TestCase):
    def setUp(self):
        self.tree = committed_tree()

    def tearDown(self):
        self.tree.cleanup()

    def test_projection_is_deterministic_and_current(self):
        first = projector.project(self.tree.inputs())
        second = projector.project(self.tree.inputs())
        self.assertEqual(first, second)
        self.assertEqual(sorted(first), sorted(projector.GENERATED))
        self.assertEqual(projector.check(self.tree.release_dir), [])

    def test_manifest_is_verify_release_compatible(self):
        path = self.tree.release_dir / "manifest.toml"
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(verify_release.validate_manifest(data, path), [])
        self.assertEqual(data["release"]["version"], "26.9.25")
        self.assertEqual(verify_release.main(["--manifest", str(path)]), 0)
        self.assertTrue(path.read_text(encoding="utf-8").startswith("# GENERATED"))

    def test_root_repository_is_not_a_component(self):
        data = tomllib.loads((self.tree.release_dir / "manifest.toml").read_text(encoding="utf-8"))
        repos = [c["repository"] for c in data["components"]]
        self.assertNotIn(data["release"]["root_repository"], repos)
        self.assertEqual(len(repos), len(set(repos)))

    def test_component_standing_projects_from_closure(self):
        closure = load(self.tree.release_dir / "closure.json")
        row = next(r for r in closure["subjects"] if r["repository"] == "seanchatmangpt/ash_a2a")
        row["impl_standing"] = "ALIVE"
        row.pop("impl_type")
        row["courts"] = [{"court": "c", "result": "PASS", "sha": row["sha"], "required": True}]
        dump(self.tree.release_dir / "closure.json", closure)
        self.assertEqual(projector.check(self.tree.release_dir)[0].split(":")[1], "PROJECTION_DRIFT")
        self.tree.reproject()
        data = tomllib.loads((self.tree.release_dir / "manifest.toml").read_text(encoding="utf-8"))
        comp = next(c for c in data["components"] if c["id"] == "ash_a2a")
        self.assertEqual(comp["standing"], "ALIVE")

    def mutant_drift(self):
        path = self.tree.release_dir / "manifest.toml"
        path.write_bytes(path.read_bytes().replace(b'standing = "BLOCKED"', b'standing = "ALIVE"', 1))

    def mutant_input_missing(self):
        (self.tree.release_dir / "pins.json").unlink()

    def test_one_refusing_mutant_per_rule(self):
        table = {"PROJECTION_DRIFT": self.mutant_drift, "PROJECTION_INPUT_MISSING": self.mutant_input_missing}
        self.assertEqual(set(table), set(PROJECTOR_RULES))
        for rule, mutate in table.items():
            with self.subTest(rule=rule):
                tree = committed_tree()
                self.tree, keep = tree, self.tree
                try:
                    mutate()
                    self.assertIn(rule, {code_of(r) for r in projector.check(tree.release_dir)})
                finally:
                    tree.cleanup()
                    self.tree = keep

    def test_cli_check_exit_codes(self):
        root = self.tree.root
        self.assertEqual(projector.main(["--release", "v26.9.25", "--root", str(root), "--check"]), 0)
        self.mutant_drift()
        self.assertEqual(projector.main(["--release", "v26.9.25", "--root", str(root), "--check"]), 2)
        self.assertEqual(projector.main(["--release", "v26.9.25", "--root", str(root), "--write"]), 0)
        self.assertEqual(projector.main(["--release", "v26.9.25", "--root", str(root), "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
