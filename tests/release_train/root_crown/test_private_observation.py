"""Operator-local private-repo observations: admitted path + one refusing/blocking mutant per rule.

Chicago style: the real committed release tree, the real crown evaluator, real
``private-repos.json``-shaped records whose digests are recomputed from real bytes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unittest

from _support import CROWN_SHA, alive_observations, alive_tree

from scripts.release_train.root_crown import crown
from scripts.release_train.root_crown.evidence import OPERATOR_LOCAL_FRESHNESS

ZOELA = "seanchatmangpt/zoela"
ZOELA_REQS = ("AC-15", "AC-16", "F-13")


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def private_obs(obs: dict, observed_at: str = "2026-09-25T12:30:00Z") -> dict:
    """Public zoela observation fails (repo-scoped token); an operator-local record replaces it."""
    obs = copy.deepcopy(obs)
    public = obs["repos"][ZOELA]
    head, pin = public["head_sha"], public["pin_sha"]
    receipts = []
    for locator in [k for k in obs["artifacts"] if k.startswith(ZOELA + ":")]:
        content = json.dumps(obs["artifacts"].pop(locator)["json"], indent=2) + "\n"
        raw = content.encode("utf-8")
        receipts.append(
            {
                "path": locator.partition(":")[2],
                "blob_sha": blob_sha(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "content": content,
                "subject_compare": "identical",
            }
        )
    obs["repos"][ZOELA] = {"pin_sha": pin, "error": "HTTP404"}
    obs["private_repos"] = {
        "schema": "https://chatman.dev/root-crown/private-observations/v1",
        "observed_at": observed_at,
        "observer": "operator-local",
        "repos": {
            ZOELA: {
                "repository": ZOELA,
                "observer": "operator-local",
                "observed_at": observed_at,
                "default_branch": "main",
                "visibility": "private",
                "head_sha": head,
                "pin_sha": pin,
                "compare_status": "identical",
                "receipts": receipts,
                "check_runs": [],
            }
        },
    }
    obs["private_public_compare"] = {}
    return obs


class PrivateObservationTest(unittest.TestCase):
    def setUp(self):
        self.tree = alive_tree()
        self.obs = private_obs(alive_observations(self.tree))

    def tearDown(self):
        self.tree.cleanup()

    def run_crown(self, obs):
        return crown.evaluate(self.tree.release_dir, obs, None, CROWN_SHA, root=self.tree.root)

    def states(self, verdict, ids=ZOELA_REQS + ("AC-11", "AC-17", "F-04")):
        return {
            rid: (verdict.receipt["requirements"][rid]["state"], verdict.receipt["requirements"][rid]["code"])
            for rid in ids
        }

    def test_without_private_record_the_public_404_blocks_as_transport_failure(self):
        obs = copy.deepcopy(self.obs)
        del obs["private_repos"]
        verdict = self.run_crown(obs)
        self.assertEqual(verdict.standing, "BLOCKED")
        self.assertEqual(self.states(verdict, ("AC-15",)), {"AC-15": ("BLOCKED", "OBSERVATION_MISSING")})

    def test_fresh_operator_local_record_is_admitted_and_crown_is_alive(self):
        verdict = self.run_crown(self.obs)
        self.assertEqual(verdict.standing, "ALIVE", verdict.remaining)
        self.assertEqual(verdict.receipt["heads"][ZOELA], self.obs["private_repos"]["repos"][ZOELA]["head_sha"])

    def test_stale_record_blocks_observation_stale(self):
        obs = private_obs(alive_observations(self.tree), observed_at="2026-09-24T00:00:00Z")
        self.assertGreater(OPERATOR_LOCAL_FRESHNESS.total_seconds(), 0)
        verdict = self.run_crown(obs)
        self.assertEqual(verdict.standing, "BLOCKED")
        self.assertEqual(set(self.states(verdict).values()), {("BLOCKED", "OBSERVATION_STALE")})

    def test_digest_mismatch_refuses(self):
        obs = copy.deepcopy(self.obs)
        receipt = obs["private_repos"]["repos"][ZOELA]["receipts"][0]
        receipt["content"] = receipt["content"].replace('"ALIVE"', '"FINAL"')  # bytes changed, digests kept
        verdict = self.run_crown(obs)
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertEqual(set(self.states(verdict).values()), {("REFUSED", "PRIVATE_OBSERVATION_DIGEST_MISMATCH")})

    def test_head_split_against_public_head_refuses(self):
        obs = copy.deepcopy(self.obs)
        obs["private_public_compare"] = {ZOELA: "diverged"}
        verdict = self.run_crown(obs)
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertEqual(set(self.states(verdict).values()), {("REFUSED", "PRIVATE_HEAD_SPLIT")})

    def test_recorded_head_behind_public_head_refuses(self):
        obs = copy.deepcopy(self.obs)
        obs["private_public_compare"] = {ZOELA: "behind"}
        self.assertIn("REFUSED:PRIVATE_HEAD_SPLIT:AC-15", self.run_crown(obs).refusals)

    def test_ancestor_of_public_head_is_lawful(self):
        obs = copy.deepcopy(self.obs)
        obs["private_public_compare"] = {ZOELA: "ahead"}
        self.assertEqual(self.run_crown(obs).standing, "ALIVE")


if __name__ == "__main__":
    unittest.main()
