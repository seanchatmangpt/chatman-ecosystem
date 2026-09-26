"""Observer (outside the court): default branch read, never hardcoded; typed errors, no raise.

The GitHub API is replaced by an in-process fixture implementing the same fetch contract
(url -> JSON object, HTTPError on 404) because the real API is a network side channel
the unit gate must not depend on; the live observer run is recorded separately by the
root-crown workflow receipt.
"""

from __future__ import annotations

import base64
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import observe_release_heads as obs  # noqa: E402

API = obs.API
PIN = "a" * 40
HEAD = "b" * 40


class FixtureApi:
    """A dict-backed GitHub API: a real, simple implementation of the fetch contract."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if url not in self.routes:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b""))
        return self.routes[url]


def content(value):
    return {"content": base64.b64encode(json.dumps(value).encode()).decode(), "sha": "c" * 40}


class ObserverTest(unittest.TestCase):
    def test_master_default_branch_is_honored(self):
        api = FixtureApi(
            {
                f"{API}/repos/o/autofde-lab": {"default_branch": "master", "visibility": "public"},
                f"{API}/repos/o/autofde-lab/commits/master": {"sha": HEAD},
                f"{API}/repos/o/autofde-lab/compare/{PIN}...{HEAD}": {"status": "ahead"},
            }
        )
        out = obs.observe_repo(api, "o/autofde-lab", PIN)
        self.assertEqual((out["default_branch"], out["head_sha"], out["compare_status"]), ("master", HEAD, "ahead"))
        self.assertFalse(any("/commits/main" in c for c in api.calls))

    def test_unreachable_repo_is_a_typed_error_not_an_exception(self):
        out = obs.observe_repo(FixtureApi({}), "o/private", PIN)
        self.assertEqual(out["error"], "HTTP404")
        self.assertNotIn("head_sha", out)

    def test_artifact_subject_lineage_is_observed(self):
        receipt = {"standing": "ALIVE", "subject_sha": PIN}
        api = FixtureApi(
            {
                f"{API}/repos/o/r/contents/release/v26.9.25/receipts/x.json?ref={HEAD}": content(receipt),
                f"{API}/repos/o/r/compare/{PIN}...{HEAD}": {"status": "ahead"},
            }
        )
        out = obs.observe_artifact(api, "o/r:release/v26.9.25/receipts/x.json", {"head_sha": HEAD})
        self.assertEqual(out["json"], receipt)
        self.assertEqual(out["subject_compare"], "ahead")
        missing = obs.observe_artifact(api, "o/r:absent.json", {"head_sha": HEAD})
        self.assertEqual(missing["error"], "HTTP404")

    def test_absent_tag_is_null_and_annotated_tag_is_dereferenced(self):
        self.assertEqual(obs.observe_tag(FixtureApi({}), "o/r", "v26.9.25"), {"name": "v26.9.25", "sha": None})
        api = FixtureApi(
            {
                f"{API}/repos/o/r/git/ref/tags/v26.9.25": {"object": {"type": "tag", "sha": "d" * 40}},
                f"{API}/repos/o/r/git/tags/{'d' * 40}": {"object": {"sha": HEAD}},
            }
        )
        self.assertEqual(obs.observe_tag(api, "o/r", "v26.9.25")["sha"], HEAD)

    def test_tag_observation_records_the_tag_object_identity(self):
        annotated = FixtureApi(
            {
                f"{API}/repos/o/r/git/ref/tags/v26.9.25": {"object": {"type": "tag", "sha": "d" * 40}},
                f"{API}/repos/o/r/git/tags/{'d' * 40}": {"object": {"sha": HEAD}},
            }
        )
        self.assertEqual(
            obs.observe_tag(annotated, "o/r", "v26.9.25"),
            {"name": "v26.9.25", "sha": HEAD, "object_sha": "d" * 40, "object_type": "tag"},
        )
        lightweight = FixtureApi(
            {f"{API}/repos/o/r/git/ref/tags/v26.9.25": {"object": {"type": "commit", "sha": HEAD}}}
        )
        self.assertEqual(
            obs.observe_tag(lightweight, "o/r", "v26.9.25"),
            {"name": "v26.9.25", "sha": HEAD, "object_sha": HEAD, "object_type": "commit"},
        )

    def test_subject_delta_lists_paths_changed_since_the_tag(self):
        api = FixtureApi(
            {
                f"{API}/repos/o/r/compare/{PIN}...{HEAD}": {
                    "status": "ahead",
                    "files": [{"filename": "b.py"}, {"filename": "a.py"}],
                }
            }
        )
        delta = obs.observe_subject_delta(api, "o/r", {"sha": PIN}, HEAD)
        self.assertEqual((delta["status"], delta["paths"]), ("ahead", ["a.py", "b.py"]))
        self.assertEqual(obs.observe_subject_delta(api, "o/r", {"sha": HEAD}, HEAD)["paths"], [])
        self.assertIsNone(obs.observe_subject_delta(api, "o/r", {"sha": None}, HEAD)["paths"])
        self.assertEqual(obs.observe_subject_delta(FixtureApi({}), "o/r", {"sha": PIN}, HEAD)["error"], "HTTP404")

    def test_local_topology_receipt_projects_violations(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "TOPOLOGY-RECEIPT.json"
            path.write_text(
                json.dumps(
                    {
                        "m_term": {
                            "observed_at": "2026-09-25T07:00:00Z",
                            "holds": False,
                            "unauthorized_worktrees": 1,
                            "violations": [{"repo_id": "unibit", "path": "/x", "class": "ORPHAN_WORKTREE"}],
                        }
                    }
                )
            )
            local = obs.observe_local_worktrees(str(Path(tmp) / "TOPOLOGY-RECEIPT*.json"))
        self.assertEqual(
            local["worktrees"], [{"repo": "unibit", "path": "/x", "class": "ORPHAN_WORKTREE", "blocked": None}]
        )
        self.assertEqual(local["observed_at"], "2026-09-25T07:00:00Z")
        self.assertFalse(local["holds"])

    def test_newest_topology_receipt_wins_over_lexically_last_stage(self):
        """``TOPOLOGY-RECEIPT.stage1.json`` sorts after ``TOPOLOGY-RECEIPT.json`` but is older:
        the observer must ingest the newest m_term observation, not the last file name."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "TOPOLOGY-RECEIPT.json").write_text(
                json.dumps({"m_term": {"observed_at": "2026-09-25T16:18:10Z", "holds": True, "violations": []}})
            )
            (Path(tmp) / "TOPOLOGY-RECEIPT.stage1.json").write_text(
                json.dumps(
                    {
                        "m_term": {
                            "observed_at": "2026-09-25T07:14:00Z",
                            "holds": False,
                            "violations": [{"repo_id": "unibit", "path": "/x", "class": "ORPHAN_WORKTREE"}],
                        }
                    }
                )
            )
            local = obs.observe_local_worktrees(str(Path(tmp) / "TOPOLOGY-RECEIPT*.json"))
        self.assertEqual(local["source"], "TOPOLOGY-RECEIPT.json")
        self.assertEqual(local["observed_at"], "2026-09-25T16:18:10Z")
        self.assertTrue(local["holds"])
        self.assertEqual(local["worktrees"], [])

    def test_private_local_records_bytes_digests_blob_sha_and_check_runs(self):
        import hashlib
        import tempfile

        receipt = {"standing": "ALIVE", "subject_sha": PIN}
        raw = json.dumps(receipt).encode()
        api = FixtureApi(
            {
                f"{API}/repos/o/z": {"default_branch": "main", "visibility": "private"},
                f"{API}/repos/o/z/commits/main": {"sha": HEAD},
                f"{API}/repos/o/z/compare/{PIN}...{HEAD}": {"status": "ahead"},
                f"{API}/repos/o/z/contents/release/v26.9.25/receipts/x.json?ref={HEAD}": {
                    "content": base64.b64encode(raw).decode(),
                    "sha": obs.git_blob_sha(raw),
                },
                f"{API}/repos/o/z/commits/{HEAD}/check-runs?per_page=100": {
                    "check_runs": [{"name": "ci", "status": "completed", "conclusion": "success", "head_sha": HEAD}]
                },
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            release = Path(tmp) / "v26.9.25"
            release.mkdir()
            (release / "pins.json").write_text(json.dumps({"repos": {"z": {"repository": "o/z", "sha": PIN}}}))
            (release / "requirements.json").write_text(
                json.dumps({"requirements": [{"evidence_locator": "o/z:release/v26.9.25/receipts/x.json"}]})
            )
            out = obs.observe_private_local(release, ["o/z"], api, now="2026-09-25T16:00:00Z")
        record = out["repos"]["o/z"]
        self.assertEqual((out["observer"], record["observer"]), ("operator-local", "operator-local"))
        self.assertEqual((record["head_sha"], record["compare_status"]), (HEAD, "ahead"))
        [entry] = record["receipts"]
        self.assertEqual(entry["content"].encode(), raw)
        self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(entry["blob_sha"], obs.git_blob_sha(raw))
        self.assertEqual(entry["subject_compare"], "ahead")
        self.assertEqual(record["check_runs"][0]["conclusion"], "success")

    def test_git_blob_sha_matches_git(self):
        # `printf 'hello\n' | git hash-object --stdin`
        self.assertEqual(obs.git_blob_sha(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_public_compare_only_where_the_public_head_is_observable(self):
        private = {"repos": {"o/z": {"head_sha": PIN}, "o/hidden": {"head_sha": PIN}}}
        api = FixtureApi({f"{API}/repos/o/z/compare/{PIN}...{HEAD}": {"status": "diverged"}})
        out = obs.public_compare(api, private, {"o/z": {"head_sha": HEAD}, "o/hidden": {"error": "HTTP404"}})
        self.assertEqual(out, {"o/z": "diverged"})


REPO = Path(__file__).resolve().parents[1]
RELEASE_DIR = REPO / "release" / "v26.9.25"
DELTAS = RELEASE_DIR / "hardening/inputs/delta-observations.json"


class DeltaObserverTest(unittest.TestCase):
    def test_artifact_records_subject_delta_paths(self):
        api = FixtureApi(
            {
                f"{API}/repos/o/r/contents/release/v26.9.25/receipts/x.json?ref={HEAD}": content({"subject_sha": PIN}),
                f"{API}/repos/o/r/compare/{PIN}...{HEAD}": {
                    "status": "ahead",
                    "files": [{"filename": "scripts/gen.py", "status": "added"},
                              {"filename": "release/v26.9.25/receipts/x.json", "status": "added"}],
                },
            }
        )  # fmt: skip
        out = obs.observe_artifact(api, "o/r:release/v26.9.25/receipts/x.json", {"head_sha": HEAD})
        self.assertEqual(out["subject_compare"], "ahead")
        self.assertEqual(out["subject_delta_paths"], ["release/v26.9.25/receipts/x.json", "scripts/gen.py"])

    def test_rename_keeps_its_source_path_in_the_delta(self):
        """compare files[] ``previous_filename`` is part of the delta: a code file renamed into
        receipts/ must not look receipt-only (it removed code from the subject)."""
        from scripts.release_train.root_crown import binding

        payload = {
            "status": "ahead",
            "files": [
                {"filename": "release/v26.9.25/receipts/gate.json", "previous_filename": "scripts/release_gate.py", "status": "renamed"},
                {"filename": "release/v26.9.25/receipts/b.json", "previous_filename": "release/v26.9.25/receipts/a.json", "status": "copied"},
            ],
        }  # fmt: skip
        api = FixtureApi({f"{API}/repos/o/r/compare/{PIN}...{HEAD}": payload})
        delta = obs.compare_delta(api, "o/r", PIN, HEAD)
        self.assertEqual(
            delta["delta_paths"],
            [
                "release/v26.9.25/receipts/a.json",
                "release/v26.9.25/receipts/b.json",
                "release/v26.9.25/receipts/gate.json",
                "scripts/release_gate.py",
            ],
        )
        self.assertEqual(
            [f.get("previous_filename") for f in delta["files"]],
            ["release/v26.9.25/receipts/a.json", "scripts/release_gate.py"],
        )
        allowlist = binding.load_allowlist("v26.9.25")
        self.assertEqual(binding.classify_delta(delta["delta_paths"], allowlist), ("UNBOUNDED", ["scripts/release_gate.py"]))
        # the artifact path records the same union
        api.routes[f"{API}/repos/o/r/contents/release/v26.9.25/receipts/gate.json?ref={HEAD}"] = content({"subject_sha": PIN})
        out = obs.observe_artifact(api, "o/r:release/v26.9.25/receipts/gate.json", {"head_sha": HEAD})
        self.assertIn("scripts/release_gate.py", out["subject_delta_paths"])

    def test_full_compare_page_is_not_a_lineage_proof(self):
        files = [{"filename": f"release/v26.9.25/receipts/{i}.json", "status": "added"} for i in range(300)]
        api = FixtureApi({f"{API}/repos/o/r/compare/{PIN}...{HEAD}": {"status": "ahead", "files": files}})
        delta = obs.compare_delta(api, "o/r", PIN, HEAD)
        self.assertIsNone(delta["delta_paths"])
        self.assertEqual(obs.compare_delta(FixtureApi({}), "o/r", PIN, PIN)["delta_paths"], [])

    def test_immutable_pairs_come_from_closure_and_the_tag_named_observations(self):
        pairs = {(p["repository"], p["base"][:8], p["head"][:8]) for p in obs.immutable_pairs(RELEASE_DIR)}
        self.assertLessEqual(
            {
                ("seanchatmangpt/autofde-lab", "6fbe1807", "98b6cc9b"),
                ("seanchatmangpt/ggen_igniter", "780a81d8", "9639198b"),
                ("seanchatmangpt/xaas", "c10cdab9", "e039967d"),
                ("seanchatmangpt/affidavit", "9d158477", "d70b0e40"),
            },
            pairs,
        )

    @unittest.skipUnless(DELTAS.is_file(), "delta observations not committed")
    def test_post_tag_bindings_replay_from_the_recorded_compare_files(self):
        """Re-running the observer over an API that serves the recorded files reproduces the doc."""
        recorded = json.loads(DELTAS.read_text(encoding="utf-8"))
        routes = {
            f"{API}/repos/{p['repository']}/compare/{p['base']}...{p['head']}": {
                "status": p["status"],
                "ahead_by": p["ahead_by"],
                "files": p["files"],
            }
            for p in recorded["pairs"]
        }
        replayed = obs.observe_post_tag_bindings(RELEASE_DIR, FixtureApi(routes), now=recorded["observed_at"])
        self.assertEqual(replayed, recorded)
        classes = {p["repository"]: p["binding"] for p in replayed["pairs"]}
        self.assertEqual(classes["seanchatmangpt/autofde-lab"], "BLOCKED(EVIDENCE_DELTA_UNBOUNDED)")
        self.assertEqual(classes["seanchatmangpt/affidavit"], "ADMITTED")

    def test_unreachable_compare_is_lineage_missing_not_an_exception(self):
        doc = obs.observe_post_tag_bindings(RELEASE_DIR, FixtureApi({}), now="2026-09-25T00:00:00Z")
        self.assertTrue(doc["pairs"])
        self.assertEqual({p["binding"] for p in doc["pairs"]}, {"REFUSED(EVIDENCE_LINEAGE_MISSING)"})
        self.assertEqual({p["error"] for p in doc["pairs"]}, {"HTTP404"})


if __name__ == "__main__":
    unittest.main()
