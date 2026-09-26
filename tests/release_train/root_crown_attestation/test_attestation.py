"""attestation.py: current-conformance.json and ATTESTATION.json are deterministic projections
of committed bytes, and every attested check refuses its own mutant.

Chicago style: the real projector and the real POST_TAG crown over the committed hardening
inputs; each mutant is a real byte change in a temporary copy of release/v26.9.25 (the rest of
the repository is linked read-only), judged by the real code. No collaborator is replaced.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.release_train.root_crown import attestation, hardening  # noqa: E402

RELEASE = "v26.9.25"
REPOSITORY = "seanchatmangpt/chatman-ecosystem"
HARDENING = REPO / "release" / RELEASE / "hardening"
SUBJECT = Path(os.environ.get("ROOT_CROWN_SUBJECT_TREE", "/nonexistent-subject"))
HAVE_SUBJECT = (SUBJECT / "scripts").is_dir()
COMMITTED = (HARDENING / attestation.ATTESTATION).is_file()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


class Root:
    """A temporary repository root: release/v26.9.25 copied, every other top-level entry linked."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)
        for entry in REPO.iterdir():
            if entry.name in (".git", "release"):
                continue
            (self.path / entry.name).symlink_to(entry)
        (self.path / "release").mkdir()
        for entry in (REPO / "release").iterdir():
            if entry.name == RELEASE:
                shutil.copytree(entry, self.path / "release" / RELEASE)
            else:
                (self.path / "release" / entry.name).symlink_to(entry)
        self.hardening = self.path / "release" / RELEASE / "hardening"

    def close(self) -> None:
        self._tmp.cleanup()


@unittest.skipUnless(COMMITTED, "ATTESTATION.json not committed")
class CommittedTest(unittest.TestCase):
    def test_committed_outputs_carry_no_machine_path_and_are_marked_generated(self):
        for name in (attestation.ATTESTATION, attestation.CURRENT):
            doc = load(HARDENING / name)
            with self.subTest(name=name):
                self.assertEqual(doc["GENERATED"], attestation.GENERATED)
                text = json.dumps(
                    {k: v for k, v in doc.items() if k != "operator_actions"}
                )
                for marker in ("/Users/", "/tmp/", "/private/", "/home/"):
                    self.assertNotIn(marker, text)

    def test_committed_attestation_holds_every_check(self):
        doc = load(HARDENING / attestation.ATTESTATION)
        self.assertEqual(doc["refusals"], [])
        self.assertEqual(doc["standing"]["attestation"], "ALIVE")
        self.assertEqual(
            doc["tag"]["object_sha"], "337e839937c247de4ee58b744c8b8e43950d18e3"
        )
        self.assertEqual(
            doc["tag"]["target_sha"], "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"
        )
        self.assertEqual(doc["frozen_payload"]["result"], "UNCHANGED")
        self.assertEqual(doc["locators"]["violations"], [])
        self.assertEqual(doc["mutation"]["survivors"], 0)
        self.assertEqual(doc["lanes"]["verified"], doc["lanes"]["total"])
        # historical and current standings stay separate; attestation never upgrades current
        self.assertEqual(
            doc["current_conformance"]["historical_replay"],
            "HISTORICAL_RELEASE_REPLAY_EXACT",
        )
        self.assertEqual(
            doc["standing"]["current"], doc["current_conformance"]["standing"]
        )

    def test_every_remaining_operator_action_is_typed(self):
        doc = load(HARDENING / attestation.ATTESTATION)
        for row in doc["operator_actions"]["rows"]:
            with self.subTest(id=row["id"]):
                self.assertEqual(row["owner"], "operator")
                self.assertTrue(row["verification"])
                if row["state"] != "PERFORMED":
                    self.assertRegex(
                        row["state"],
                        r"^BLOCKED\((AUTHORITY_CONFIGURATION|AUTHORITY_FAILURE):",
                    )
                    self.assertEqual(row["broken_term"], "R_missing_authority")


class LocatorScanTest(unittest.TestCase):
    def test_classification(self):
        cases = [
            ("evidence_locator", "git:o/r@" + "a" * 40 + ":p.json", {}, "DURABLE"),
            ("locator", "https://github.com/o/r/pull/1", {}, "DURABLE"),
            (
                "evidence",
                "scratchpad/v26925/x.json",
                {"evidence_locator": "git:o/r@" + "b" * 40 + ":x.json"},
                "REBOUND",
            ),
            (
                "cwd_original",
                "/Users/x/.claude/m",
                {"cwd": "git:o/r@" + "c" * 40 + ":m"},
                "REBOUND",
            ),
            (
                "verify_repo",
                "~/repo",
                {"standing": "BLOCKED(DURABILITY:FOREIGN_LOCAL_ONLY)"},
                "TYPED_RESIDUE",
            ),
            ("evidence", "scratchpad/v26925/x.json", {}, "VIOLATION"),
            ("tagged_locator", "local:release/x.toml", {}, "VIOLATION"),
            ("json_pointer", "/subjects/2/courts/0", {}, None),
            ("name", "plain text", {}, None),
        ]
        for key, value, holder, expected in cases:
            with self.subTest(key=key, value=value):
                self.assertEqual(
                    attestation.classify_locator(key, value, holder), expected
                )

    def test_scratch_locator_injected_into_a_record_is_a_violation(self):
        root = Root()
        try:
            base = attestation.scan_locators(root.hardening)
            self.assertEqual(base["violations"], [])
            path = root.hardening / "pr-dispositions.json"
            doc = load(path)
            doc["rows"][0]["successor_locator"] = (
                "/private/tmp/scratchpad/v26925/lane/receipt.json"
            )
            dump(path, doc)
            scan = attestation.scan_locators(root.hardening)
        finally:
            root.close()
        self.assertEqual(scan["result"], "REFUSED:NON_DURABLE_LOCATOR")
        self.assertEqual(
            [v["json_pointer"] for v in scan["violations"]],
            ["/rows/0/successor_locator"],
        )

    def test_prose_is_not_scanned_but_a_prose_subtree_is(self):
        holder = {
            "commands": [{"cwd_original": "/Users/x/m", "cwd": "/Users/x/m2"}],
            "note": "/Users/x/y",
        }
        hits = [
            (p, attestation.classify_locator(k, v, h))
            for p, k, v, h in attestation._walk(holder, "", None)
        ]
        self.assertEqual(
            sorted(p for p, _ in hits if _),
            ["/commands/0/cwd", "/commands/0/cwd_original"],
        )


class LaneTest(unittest.TestCase):
    def mutate_observation(self, lane_id: str, **fields):
        root = Root()
        try:
            path = root.hardening / attestation.LANE_OBSERVATIONS
            doc = load(path)
            row = next(r for r in doc["lanes"] if r["id"] == lane_id)
            row.update(fields)
            dump(path, doc)
            return attestation.lane_rows(root.hardening)
        finally:
            root.close()

    def test_committed_lanes_all_verify(self):
        rows, refusals, _ = attestation.lane_rows(HARDENING)
        self.assertEqual(refusals, [])
        self.assertTrue(all(r["verification"] == "VERIFIED" for r in rows))

    def test_merge_not_on_default_is_refused(self):
        _, refusals, _ = self.mutate_observation(
            "G1-origin-trust-root", merge_on_default="NOT_ON_DEFAULT"
        )
        self.assertEqual(
            refusals,
            ["REFUSED:LANE_UNVERIFIED:G1-origin-trust-root:MERGE_NOT_ON_DEFAULT"],
        )

    def test_merge_sha_mismatch_is_refused(self):
        _, refusals, _ = self.mutate_observation(
            "PR-B-autonomic-crown", pr_merge_commit="0" * 40
        )
        self.assertEqual(
            refusals,
            ["REFUSED:LANE_UNVERIFIED:PR-B-autonomic-crown:MERGE_SHA_MISMATCH"],
        )

    def test_unresolved_receipt_is_refused(self):
        _, refusals, _ = self.mutate_observation(
            "X2-case-study-durable",
            receipt={
                "locator": "git:seanchatmangpt/xaas@4f176fd4ee0c030720a44aeac7ef60dcc7d10a8f:release/v26.9.25/receipts/case-study-schema.post-tag.json",
                "error": "REFUSED[PATH_NOT_FOUND]",
            },
        )
        self.assertEqual(
            refusals,
            ["REFUSED:LANE_UNVERIFIED:X2-case-study-durable:RECEIPT_UNRESOLVED"],
        )

    def test_closed_lane_observed_merged_is_refused(self):
        _, refusals, _ = self.mutate_observation(
            "A1-pr81-disposition", pr_state="MERGED", pr_merge_commit="1" * 40
        )
        self.assertEqual(
            refusals,
            ["REFUSED:LANE_UNVERIFIED:A1-pr81-disposition:DISPOSITION_MISMATCH"],
        )

    def test_lane_record_edited_after_observation_is_stale(self):
        root = Root()
        try:
            path = root.hardening / attestation.LANES
            doc = load(path)
            doc["lanes"][0]["reported_standing"] = "ALIVE "
            dump(path, doc)
            _, refusals, _ = attestation.lane_rows(root.hardening)
        finally:
            root.close()
        self.assertIn(
            "REFUSED:LANE_OBSERVATION_STALE:attestation-lanes.json changed after observation",
            refusals,
        )


class OperatorActionTest(unittest.TestCase):
    def test_state_is_derived_from_the_get_only_observation(self):
        blocked = {
            r["id"]: r["state"]
            for r in attestation.operator_actions(
                HARDENING,
                {"main_protected": False, "release_crown_required_reviewers": 0},
            )
        }
        done = {
            r["id"]: r["state"]
            for r in attestation.operator_actions(
                HARDENING,
                {"main_protected": True, "release_crown_required_reviewers": 1},
            )
        }
        self.assertTrue(blocked["OPA-01"].startswith("BLOCKED(AUTHORITY_CONFIGURATION"))
        self.assertTrue(blocked["OPA-02"].startswith("BLOCKED(AUTHORITY_CONFIGURATION"))
        self.assertEqual((done["OPA-01"], done["OPA-02"]), ("PERFORMED", "PERFORMED"))
        # an action with no GET-only observation can never be derived PERFORMED
        self.assertTrue(done["OPA-06"].startswith("BLOCKED("))


@unittest.skipUnless(
    HAVE_SUBJECT and COMMITTED,
    "ROOT_CROWN_SUBJECT_TREE (git archive of 68bacd8d) not provided",
)
class ProjectionTest(unittest.TestCase):
    def test_committed_outputs_are_current_and_deterministic(self):
        first = attestation.outputs(REPO, RELEASE, REPOSITORY, SUBJECT)
        second = attestation.outputs(REPO, RELEASE, REPOSITORY, SUBJECT)
        self.assertEqual(first, second)
        self.assertEqual(hardening.check(HARDENING, first), [])
        current = json.loads(first[attestation.CURRENT])
        self.assertEqual(current["replay"]["result"], "EXACT")
        self.assertEqual(current["exit_code"], current["recorded_exit_code"])

    def attested_after(self, edit) -> dict:
        root = Root()
        try:
            edit(root)
            current = attestation.current_conformance(
                root.path, RELEASE, root.hardening, SUBJECT
            )
            return attestation.attestation(
                root.path, RELEASE, REPOSITORY, SUBJECT, current
            )
        finally:
            root.close()

    def refusals_after(self, edit) -> list[str]:
        return self.attested_after(edit)["refusals"]

    def test_moved_local_tag_observation_is_refused(self):
        def edit(root):
            path = root.hardening / attestation.CURRENT_DIR / "tag-observation.json"
            doc = load(path)
            doc["object_sha"] = "0" * 40
            dump(path, doc)

        doc = self.attested_after(edit)
        self.assertIn("REFUSED:TAG_MOVED:local-git", doc["refusals"])
        self.assertEqual(
            doc["tag"]["observations"]["local-git"]["result"], "REFUSED:TAG_MOVED"
        )
        self.assertEqual(
            doc["tag"]["observations"]["github-api"]["result"], "UNCHANGED"
        )
        self.assertEqual(doc["standing"]["attestation"], "REFUSED")

    def test_mutated_frozen_payload_is_refused(self):
        def edit(root):
            path = root.path / "release" / RELEASE / "manifest.toml"
            path.write_text(path.read_text() + "\n# post-tag edit\n")

        refusals = self.refusals_after(edit)
        self.assertTrue(
            any(r.startswith("REFUSED:PAYLOAD_MUTATED_POST_TAG:") for r in refusals),
            refusals,
        )

    def test_hand_edited_projection_is_refused(self):
        def edit(root):
            path = root.hardening / "drift.json"
            path.write_text(path.read_text() + "\n")

        refusals = self.refusals_after(edit)
        self.assertTrue(
            any(
                r.startswith("REFUSED:PROJECTION_DRIFT:") and r.endswith("drift.json")
                for r in refusals
            ),
            refusals,
        )

    def test_mutant_survivor_is_refused(self):
        def edit(root):
            path = root.hardening / attestation.MUTATION_REPORT
            doc = load(path)
            doc["survivors"] = ["m-planted"]
            dump(path, doc)

        self.assertIn("REFUSED:MUTANT_SURVIVORS:1", self.refusals_after(edit))

    def test_rewritten_run_output_diverges_from_the_replay(self):
        def edit(root):
            path = root.hardening / attestation.CURRENT_DIR / "crown-receipt.json"
            doc = load(path)
            doc["standing"] = "ALIVE"
            dump(path, doc)

        self.assertIn(
            "REFUSED:CURRENT_CONFORMANCE_REPLAY_DIVERGED", self.refusals_after(edit)
        )

    def test_recorded_exit_code_mismatch_is_refused(self):
        def edit(root):
            path = root.hardening / attestation.CURRENT_DIR / "run.json"
            doc = load(path)
            doc["exit_code"] = 0
            dump(path, doc)

        self.assertIn(
            "REFUSED:CURRENT_CONFORMANCE_EXIT_MISMATCH", self.refusals_after(edit)
        )


if __name__ == "__main__":
    unittest.main()
