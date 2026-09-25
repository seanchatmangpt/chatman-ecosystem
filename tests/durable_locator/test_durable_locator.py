"""Durable locators (CE23-9) against real temporary git repositories.

Chicago style: every resolution runs real ``git`` over real repositories created in a
temporary directory; assertions are on returned bytes, typed refusal codes and the
generated JSON. No collaborator is replaced.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.durable_locator import durable_locator as dl

REPO = Path(__file__).resolve().parents[2]
RELEASE = "v26.9.25"
SCRATCH = "scratchpad/v26925/lanes/x/courts.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True, env=env)
    return out.stdout.decode().strip()


def make_repo(root: Path, name: str, files: dict[str, bytes]) -> str:
    repo = root / name
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / ".git").exists():
        git(repo, "init", "-q", "-b", "main")
    for rel, data in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    git(repo, "add", "--", *files)
    git(repo, "commit", "-q", "-m", "c")
    return git(repo, "rev-parse", "HEAD")


class GrammarTest(unittest.TestCase):
    def test_git_locator_parses(self):
        loc = dl.parse("git:o/r@" + "a" * 40 + ":release/x.json")
        self.assertEqual((loc.kind, loc.repository, loc.sha, loc.path), ("git", "o/r", "a" * 40, "release/x.json"))

    def test_notes_and_https_parse(self):
        self.assertEqual(dl.parse("git-notes:refs/notes/crown@" + "b" * 40).ref, "refs/notes/crown")
        self.assertEqual(dl.parse("https://github.com/o/r/actions/runs/1").kind, "https")

    def test_scratch_locators_refused(self):
        for text in (
            SCRATCH,
            "/private/tmp/claude-501/x/out.json",
            "/tmp/run/out.json",
            "~/.claude/migration/v26925-topology",
            "/Users/someone/.claude/migration/b.bundle",
            "git:o/r@" + "a" * 40 + ":scratchpad/v26925/x.json",
        ):
            with self.subTest(text=text), self.assertRaises(dl.Refused) as ctx:
                dl.parse(text)
            self.assertEqual(ctx.exception.code, "SCRATCH_LOCATOR")

    def test_absolute_path_refused(self):
        for text in ("/Users/someone/zoela", "~/zoela/x"):
            with self.subTest(text=text), self.assertRaises(dl.Refused) as ctx:
                dl.parse(text)
            self.assertEqual(ctx.exception.code, "ABSOLUTE_PATH")

    def test_missing_or_short_sha_refused(self):
        for text in ("seanchatmangpt/xaas:release/v26.9.25/receipts/a.json", "git:o/r:x", "git:o/r@abc123:x"):
            with self.subTest(text=text), self.assertRaises(dl.Refused) as ctx:
                dl.parse(text)
            self.assertEqual(ctx.exception.code, "MISSING_SHA")

    def test_malformed_refused(self):
        for text in ("", " git:o/r@" + "a" * 40 + ":x", "http://x", "git:o/r@" + "a" * 40 + ":../x", "gitlab:x"):
            with self.subTest(text=text), self.assertRaises(dl.Refused) as ctx:
                dl.parse(text)
            self.assertEqual(ctx.exception.code, "MALFORMED")


class ResolverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.body = b'{"court": "PASS"}\n'
        self.sha = make_repo(self.root, "r", {"ev/court.out": self.body})
        self.resolver = dl.Resolver(self.root, allow_network=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_locator_resolves_to_exact_bytes(self):
        data = self.resolver.resolve(dl.parse(f"git:o/r@{self.sha}:ev/court.out"))
        self.assertEqual(data, self.body)

    def test_wrong_sha_refused(self):
        with self.assertRaises(dl.Refused) as ctx:
            self.resolver.resolve(dl.parse("git:o/r@" + "0" * 40 + ":ev/court.out"))
        self.assertEqual(ctx.exception.code, "SHA_NOT_FOUND")

    def test_wrong_path_refused(self):
        with self.assertRaises(dl.Refused) as ctx:
            self.resolver.resolve(dl.parse(f"git:o/r@{self.sha}:ev/missing.out"))
        self.assertEqual(ctx.exception.code, "PATH_NOT_FOUND")

    def test_file_added_after_sha_is_not_visible_at_that_sha(self):
        make_repo(self.root, "r", {"ev/later.out": b"later\n"})
        with self.assertRaises(dl.Refused) as ctx:
            self.resolver.resolve(dl.parse(f"git:o/r@{self.sha}:ev/later.out"))
        self.assertEqual(ctx.exception.code, "PATH_NOT_FOUND")

    def test_unknown_repository_without_network_refused(self):
        with self.assertRaises(dl.Refused) as ctx:
            self.resolver.resolve(dl.parse("git:o/absent@" + "a" * 40 + ":x"))
        self.assertEqual(ctx.exception.code, "REPOSITORY_UNAVAILABLE")


class VerifyIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.body = b"evidence bytes\n"
        self.sha = make_repo(self.root, "e1", {"ev/log": self.body})
        self.resolver = dl.Resolver(self.root, allow_network=False)
        self.good = {"durable_locator": f"git:o/e1@{self.sha}:ev/log", "sha256": sha256(self.body)}

    def tearDown(self):
        self.tmp.cleanup()

    def findings(self, *rows):
        return dl.verify_index(self.resolver, {"rows": list(rows)})

    def test_good_row_admitted(self):
        self.assertEqual(self.findings(self.good), [])

    def test_hash_mismatch_refused(self):
        out = self.findings({**self.good, "sha256": sha256(b"other")})
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("REFUSED[HASH_MISMATCH] rows/0"), out)

    def test_scratch_locator_row_refused(self):
        out = self.findings({"durable_locator": SCRATCH, "sha256": sha256(self.body)})
        self.assertTrue(out[0].startswith("REFUSED[SCRATCH_LOCATOR]"), out)

    def test_missing_sha_row_refused(self):
        out = self.findings({"durable_locator": "o/e1:ev/log", "sha256": sha256(self.body)})
        self.assertTrue(out[0].startswith("REFUSED[MISSING_SHA]"), out)

    def test_wrong_sha_and_path_rows_refused(self):
        out = self.findings(
            {**self.good, "durable_locator": "git:o/e1@" + "1" * 40 + ":ev/log"},
            {**self.good, "durable_locator": f"git:o/e1@{self.sha}:ev/nope"},
        )
        self.assertEqual([f.split("]")[0] for f in out], ["REFUSED[SHA_NOT_FOUND", "REFUSED[PATH_NOT_FOUND"])

    def test_residue_must_be_typed(self):
        self.assertEqual(self.findings({"durable_locator": "RESIDUE:SUBJECT_PATH(x)", "sha256": None, "standing": "NOT_EVIDENCE"}), [])
        out = self.findings({"durable_locator": "RESIDUE:SUBJECT_PATH(x)", "sha256": None})
        self.assertTrue(out[0].startswith("REFUSED[UNTYPED_RESIDUE]"), out)

    def test_recorded_mismatch_needs_declared_divergence(self):
        companion = {**self.good, "recorded_in_closure": "MISMATCH"}
        out = self.findings({**self.good, "companions": [companion]})
        self.assertTrue(out[0].startswith("REFUSED[RECORDED_DIGEST_MISMATCH]"), out)
        declared = {**companion, "divergence": {"type": "BLOCKED(EVIDENCE_FAILURE:x)", "broken_term": "R_missing_replay"}}
        self.assertEqual(self.findings({**self.good, "companions": [declared]}), [])

    def test_unmatched_scan_hits_refuse_the_index(self):
        out = dl.verify_index(self.resolver, {"rows": [self.good], "unmatched": [{"path": "a.json", "pointer": "/x"}]})
        self.assertEqual(out, ["REFUSED[UNINDEXED_SCRATCH_LOCATOR] unmatched/0 a.json/x"])

    def test_resolve_only_skips_digest_but_refuses_unbound(self):
        out = dl.verify_index(
            self.resolver, {"rows": [{"durable_locator": self.good["durable_locator"]}, {"durable_locator": None}]}, True
        )
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("REFUSED[UNBOUND_LOCATOR] rows/1"), out)


class IndexCompletenessTest(unittest.TestCase):
    """build_index over a real source repo and a real E1 repo, then completeness rescans."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out_bytes = b"court output\n"
        self.e1 = make_repo(self.root, "e1", {"ev/courts/a/court.out": self.out_bytes, "ev/courts/a/courts.json": b"{}\n"})
        closure = {
            "subjects": [
                {"courts": [{"evidence": SCRATCH, "output_sha256": "sha256:" + sha256(self.out_bytes)}]},
                {"courts": [{"path": "/private/tmp/retired-copy"}]},
            ]
        }
        self.src = make_repo(self.root, "src", {"release/v/closure.json": json.dumps(closure).encode()})
        self.resolver = dl.Resolver(self.root, allow_network=False)
        self.rules = {
            "release": "v",
            "e1": {"repository": "o/e1", "commit": self.e1, "root": "ev/courts"},
            "sources": [{"repository": "o/src", "sha": self.src, "prefix": "release/v"}],
            "rules": [
                {
                    "id": "courts",
                    "locator": "^scratchpad/",
                    "durable": "a/courts.json",
                    "companions": [{"durable": "a/court.out", "recorded_field": "output_sha256"}],
                },
                {"id": "subject", "pointer": "/path$", "residue": "SUBJECT_PATH(x)", "standing": "NOT_EVIDENCE"},
            ],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_scratch_locator_indexed_and_verified(self):
        index = dl.build_index(self.resolver, self.rules)
        self.assertEqual(index["summary"], {"rows": 2, "by_disposition": {"RESIDUE:SUBJECT_PATH": 1, "durable": 1}, "unmatched": 0})
        row = index["rows"][0]
        self.assertEqual(row["closure_pointer"], "/subjects/0/courts/0/evidence")
        self.assertEqual(row["durable_locator"], f"git:o/e1@{self.e1}:ev/courts/a/courts.json")
        self.assertEqual(row["sha256"], sha256(b"{}\n"))
        self.assertEqual(row["recorded_in_closure"], "UNRECORDED")
        self.assertEqual(row["companions"][0]["recorded_in_closure"], "match")
        self.assertEqual(dl.verify_index(self.resolver, index), [])
        self.assertEqual(dl.completeness(self.resolver, index), [])

    def test_primary_row_recorded_digest_match_and_mismatch(self):
        rules = json.loads(json.dumps(self.rules))
        rules["rules"][0] = {"id": "out", "locator": "^scratchpad/", "durable": "a/court.out", "recorded_field": "output_sha256"}
        row = dl.build_index(self.resolver, rules)["rows"][0]
        self.assertEqual((row["recorded_in_closure"], row["standing"]), ("match", "ALIVE"))
        rules["rules"][0]["durable"] = "a/courts.json"
        row = dl.build_index(self.resolver, rules)["rows"][0]
        self.assertEqual((row["recorded_in_closure"], row["standing"]), ("MISMATCH", "REFUSED(HASH_MISMATCH)"))

    def test_unruled_locator_is_listed_unmatched(self):
        rules = {**self.rules, "rules": self.rules["rules"][:1]}
        index = dl.build_index(self.resolver, rules)
        self.assertEqual(index["summary"]["unmatched"], 1)
        self.assertEqual(index["unmatched"][0]["text"], "/private/tmp/retired-copy")
        self.assertEqual(len(dl.verify_index(self.resolver, index)), 1)

    def test_new_scratch_locator_at_new_source_sha_is_unindexed(self):
        index = dl.build_index(self.resolver, self.rules)
        doc = {"evidence": "/tmp/new/receipt.json"}
        new_sha = make_repo(self.root, "src", {"release/v/extra.json": json.dumps(doc).encode()})
        index["sources"] = [{**index["sources"][0], "sha": new_sha}]
        out = dl.completeness(self.resolver, index)
        self.assertIn(f"REFUSED[UNINDEXED_SCRATCH_LOCATOR] git:o/src@{new_sha}:release/v/extra.json#/evidence", out)
        self.assertEqual(sum(f.startswith("REFUSED[UNINDEXED") for f in out), 3)
        self.assertEqual(sum(f.startswith("REFUSED[STALE_ROW") for f in out), 2)

    def test_dropped_row_is_unindexed(self):
        index = dl.build_index(self.resolver, self.rules)
        index["rows"] = index["rows"][1:]
        out = dl.completeness(self.resolver, index)
        self.assertEqual(out, [f"REFUSED[UNINDEXED_SCRATCH_LOCATOR] git:o/src@{self.src}:release/v/closure.json#/subjects/0/courts/0/evidence"])

    def test_cli_index_write_then_check_then_drift(self):
        rules_path = self.root / "rules.json"
        rules_path.write_text(json.dumps(self.rules))
        out = self.root / "INDEX.json"
        base = ["--repos-root", str(self.root), "--no-network"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dl.main(base + ["index", "--rules", str(rules_path), "--out", str(out), "--write"]), 0)
            self.assertEqual(dl.main(base + ["index", "--rules", str(rules_path), "--out", str(out), "--check"]), 0)
            self.assertEqual(dl.main(base + ["verify", str(out)]), 0)
            self.assertEqual(dl.main(base + ["completeness", str(out)]), 0)
            out.write_bytes(out.read_bytes().replace(b'"NOT_EVIDENCE"', b'"ALIVE"'))
            self.assertEqual(dl.main(base + ["index", "--rules", str(rules_path), "--out", str(out), "--check"]), 1)


class RequirementsLocatorsTest(unittest.TestCase):
    def test_binds_pinned_remote_and_local_locators(self):
        with tempfile.TemporaryDirectory() as tmp:
            rel = Path(tmp) / "release" / "v"
            (rel / "hardening").mkdir(parents=True)
            (rel / "requirements.json").write_text(json.dumps({"requirements": [
                {"id": "AC-1", "evidence_locator": "local:release/v/closure.json"},
                {"id": "AC-2", "evidence_locator": "o/x:release/v/receipts/a.json"},
                {"id": "AC-3", "evidence_locator": "o/unpinned:release/v/receipts/b.json"},
            ]}))
            (rel / "pins.json").write_text(json.dumps({"repos": {"x": {"repository": "o/x", "sha": "c" * 40}}}))
            (rel / "hardening" / "TAG-SUBJECT.json").write_text(
                json.dumps({"repository": "o/root", "subject": {"commit_sha": "d" * 40}})
            )
            doc = dl.requirements_locators(Path(tmp), "v")
        got = [(r["id"], r["durable_locator"]) for r in doc["rows"]]
        self.assertEqual(got, [
            ("AC-1", "git:o/root@" + "d" * 40 + ":release/v/closure.json"),
            ("AC-2", "git:o/x@" + "c" * 40 + ":release/v/receipts/a.json"),
            ("AC-3", None),
        ])
        self.assertEqual(doc["rows"][2]["standing"], "REFUSED(UNPINNED_REPOSITORY)")

    def test_committed_projection_has_no_drift(self):
        committed = REPO / "release" / RELEASE / "hardening" / "requirements-locators.json"
        self.assertTrue(committed.is_file())
        self.assertEqual(committed.read_bytes(), dl.dump(dl.requirements_locators(REPO, RELEASE)))
        rows = json.loads(committed.read_bytes())["rows"]
        self.assertEqual(len(rows), 33)
        self.assertTrue(all(r["durable_locator"] and dl.parse(r["durable_locator"]).kind == "git" for r in rows))


REPOS_ROOT = Path(os.environ.get("DURABLE_LOCATOR_REPOS_ROOT", str(Path.home())))
E1 = "c599667a84ec79d832bb779bce1730b33b43fdd4"


def _has_commit(name: str, sha: str) -> bool:
    d = REPOS_ROOT / name
    return d.is_dir() and subprocess.run(
        ["git", "-C", str(d), "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True, check=False
    ).returncode == 0


@unittest.skipUnless(
    _has_commit("chatman-ecosystem", E1),
    "canonical chatman-ecosystem object DB with E1 c599667a not reachable under DURABLE_LOCATOR_REPOS_ROOT",
)
class CommittedIndexTest(unittest.TestCase):
    """The committed INDEX.json against the canonical object database (read-only cat-file)."""

    def setUp(self):
        self.index = json.loads((REPO / "release" / RELEASE / "hardening" / "evidence" / "INDEX.json").read_bytes())
        self.resolver = dl.Resolver(REPOS_ROOT, allow_network=False)

    def test_every_durable_row_resolves_and_rehashes(self):
        self.assertEqual(dl.verify_index(self.resolver, self.index), [])

    def test_no_row_cites_scratch_as_durable(self):
        for r in self.index["rows"]:
            loc = r["durable_locator"]
            self.assertTrue(loc.startswith("RESIDUE:") or dl.parse(loc).sha == E1, loc)

    def test_affidavit_replay_is_recorded_exact(self):
        (replay,) = self.index["replays"]
        self.assertEqual(replay["result"], "LOCAL_EXACT_SHA_REPLAYED")
        self.assertEqual(replay["stdout_sha256"], replay["recorded_output_sha256"])
        data = self.resolver.resolve(dl.parse(replay["durable_output"]))
        self.assertEqual(sha256(data), replay["stdout_sha256"])

    @unittest.skipUnless(
        all(_has_commit(s["repository"].split("/")[1], s["sha"]) for s in json.loads(
            (REPO / "release" / RELEASE / "hardening" / "evidence" / "INDEX.json").read_bytes())["sources"]),
        "not every source repository object DB is reachable",
    )
    def test_completeness_zero_unindexed(self):
        self.assertEqual(dl.completeness(self.resolver, self.index), [])


if __name__ == "__main__":
    unittest.main()
