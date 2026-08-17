from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
FORMATION = ROOT / "catalog" / "formation.toml"
REPOSITORIES = ROOT / "catalog" / "repositories.toml"

REQUIRED_FENCES = {
    "NO_CONVERSION_SCORE",
    "NO_SPIRITUAL_LEADERBOARD",
    "NO_RECOGNITION_AS_GOAL",
    "NO_PROSPERITY_FORMULA",
    "NO_AI_REVELATION_CLAIMS",
    "NO_PASTORAL_AUTHORITY",
    "NO_PRIVATE_CONFESSION_STORAGE",
}
REQUIRED_COMPONENTS = {
    "seanchatmangpt/biblegym",
    "seanchatmangpt/ggen-marketplace",
}


class FormationCatalogTests(unittest.TestCase):
    def load(self):
        with FORMATION.open("rb") as handle:
            return tomllib.load(handle)

    def test_goal_is_relationship_not_recognition_or_results(self):
        manifest = self.load()
        formation = manifest["formation"]
        self.assertEqual(formation["id"], "formation:knowing-christ-v1")
        self.assertEqual(formation["goal"], "know_christ")
        self.assertEqual(formation["mode"], "daily_process_not_project")
        self.assertEqual(formation["standing"], "CANDIDATE")
        self.assertEqual(formation["authority"], "SELECT_CONSTRUCT_ONLY")
        self.assertFalse(formation["recognition_is_goal"])
        self.assertFalse(formation["results_are_spiritual_score"])
        self.assertFalse(formation["conversion_is_machine_scored"])
        self.assertFalse(formation["pastoral_authority_is_delegated_to_ai"])
        self.assertTrue(REQUIRED_FENCES.issubset(set(formation["fences"])))

    def test_components_are_exact_candidate_subjects(self):
        manifest = self.load()
        components = manifest["component"]
        self.assertEqual({item["repository"] for item in components}, REQUIRED_COMPONENTS)
        self.assertEqual(len({item["id"] for item in components}), len(components))
        for component in components:
            self.assertEqual(component["standing"], "CANDIDATE")
            self.assertTrue(component["ref"].startswith("feat/"))
            self.assertRegex(component["sha"], re.compile(r"^[0-9a-f]{40}$"))
            self.assertNotEqual(component["standing"], "ALIVE")

    def test_llm_has_no_revelation_or_pastoral_authority(self):
        manifest = self.load()
        interpretation = manifest["interpretation"]
        privacy = manifest["privacy"]
        self.assertTrue(interpretation["scripture_is_source"])
        self.assertTrue(interpretation["llm_output_is_candidate"])
        self.assertFalse(interpretation["llm_output_has_revelation_authority"])
        self.assertFalse(privacy["raw_confession_storage"])
        self.assertFalse(privacy["conversion_targeting"])
        self.assertFalse(privacy["psychological_manipulation"])

    def test_component_repositories_are_registered(self):
        with REPOSITORIES.open("rb") as handle:
            catalog = tomllib.load(handle)
        urls = {entry["url"] for entry in catalog["repository"]}
        for repository in REQUIRED_COMPONENTS:
            self.assertIn(f"https://github.com/{repository}", urls)


if __name__ == "__main__":
    unittest.main()
