"""Premise imports (RFC-0005 E-ADM-02) against real temporary git repositories.

Chicago style: every import reads a real blob through ``durable_locator.Resolver`` over a
real repository; assertions are on written bytes, IMPORTS.json rows and typed codes.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.durable_locator.durable_locator import Resolver
from scripts.premise_import import premise_import as pi

REPO = Path(__file__).resolve().parents[2]
RFC = b"# RFC-9999\n\nA premise.\n"


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


def commit(repo: Path, files: dict[str, bytes], origin: str = "https://github.com/o/standards.git") -> str:
    if not (repo / ".git").exists():
        repo.mkdir(parents=True, exist_ok=True)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "remote", "add", "origin", origin)
    for rel, data in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(data)
    git(repo, "add", "--", *files)
    git(repo, "commit", "-q", "-m", "c")
    return git(repo, "rev-parse", "HEAD")


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repos = self.tmp / "repos"
        self.sha = commit(self.repos / "standards", {"docs/rfc/9999.md": RFC})
        self.root = self.tmp / "root"
        self.imports = self.root / "release" / "v26.9.26" / "imports"
        self.resolver = Resolver(self.repos, allow_network=False)
        self.locator = f"git:o/standards@{self.sha}:docs/rfc/9999.md"

    def do_import(self, **kw):
        args = dict(
            resolver=self.resolver,
            locator=self.locator,
            imports_dir=self.imports,
            copy_name="RFC-9999.md",
            owner="o/standards (PR #1, FINAL_SPEC)",
            standing="NOT_A_SPEC",
        )
        args.update(kw)
        return pi.import_premise(**args)

    def codes(self, report: dict) -> set[str]:
        return {f["code"] for d in report["directories"] for f in d["findings"]}

    def refused(self, code: str, **kw) -> None:
        with self.assertRaises(pi.ImportRefused) as ctx:
            self.do_import(**kw)
        self.assertEqual(ctx.exception.code, code)


class Produce(Fixture):
    def test_import_binds_digests_computed_from_the_source_bytes(self) -> None:
        row, changed = self.do_import(scope="POST_TAG")
        self.assertTrue(changed)
        self.assertEqual((self.imports / "RFC-9999.md").read_bytes(), RFC)
        self.assertEqual(row["sha256"], hashlib.sha256(RFC).hexdigest())
        self.assertEqual(row["source_blob_sha1"], git(self.repos / "standards", "rev-parse", f"{self.sha}:docs/rfc/9999.md"))
        self.assertEqual(list(row), ["path", "source_repo", "source_sha", "source_path", "source_blob_sha1", "sha256", "standing", "scope", "owner"])
        doc = json.loads((self.imports / "IMPORTS.json").read_text())
        self.assertEqual(doc["imports"], [row])

    def test_reimport_of_the_same_subject_is_a_byte_identical_noop(self) -> None:
        self.do_import()
        before = (self.imports / "IMPORTS.json").read_bytes()
        _, changed = self.do_import()
        self.assertFalse(changed)
        self.assertEqual((self.imports / "IMPORTS.json").read_bytes(), before)

    def test_rows_are_sorted_by_path_whatever_the_import_order(self) -> None:
        self.do_import(copy_name="RFC-9999.md")
        self.do_import(copy_name="RFC-0001.md")
        paths = [r["path"] for r in json.loads((self.imports / "IMPORTS.json").read_text())["imports"]]
        self.assertEqual(paths, ["imports/RFC-0001.md", "imports/RFC-9999.md"])

    def test_new_subject_on_a_bound_path_is_refused_then_rebound_only_with_replace(self) -> None:
        self.do_import()
        sha2 = commit(self.repos / "standards", {"docs/rfc/9999.md": RFC + b"amended\n"})
        loc2 = f"git:o/standards@{sha2}:docs/rfc/9999.md"
        self.refused("IMPORT_PATH_CONFLICT", locator=loc2)
        self.assertEqual((self.imports / "RFC-9999.md").read_bytes(), RFC)  # refusal wrote nothing
        row, changed = self.do_import(locator=loc2, replace=True)
        self.assertTrue(changed)
        self.assertEqual(row["source_sha"], sha2)
        self.assertEqual(pi.check(self.root, self.resolver)["verdict"], "ADMITTED")

    def test_malformed_and_unimportable_inputs_are_typed_refusals(self) -> None:
        self.refused("IMPORT_ROW_MALFORMED", locator=f"o/standards:docs/rfc/9999.md")
        self.refused("IMPORT_ROW_MALFORMED", locator="https://example.invalid/rfc.md")
        self.refused("IMPORT_PATH_ESCAPE", copy_name="../RFC.md")
        self.refused("IMPORT_PATH_ESCAPE", copy_name="IMPORTS.json")
        self.refused("IMPORT_ROW_MALFORMED", standing="final spec")
        self.refused("IMPORT_ROW_MALFORMED", owner="  ")
        self.assertFalse(self.imports.exists())

    def test_absent_sha_or_path_is_source_unresolved(self) -> None:
        self.refused("IMPORT_SOURCE_UNRESOLVED", locator=f"git:o/standards@{'0' * 40}:docs/rfc/9999.md")
        self.refused("IMPORT_SOURCE_UNRESOLVED", locator=f"git:o/standards@{self.sha}:docs/rfc/0000.md")

    def test_unreachable_or_impostor_repository_is_transport_not_subject(self) -> None:
        self.refused("TRANSPORT_UNAVAILABLE", locator=f"git:o/absent@{self.sha}:docs/rfc/9999.md")
        # A checkout named like the repository but whose origin is another owner.
        self.refused("TRANSPORT_UNAVAILABLE", locator=f"git:attacker/standards@{self.sha}:docs/rfc/9999.md")


class Court(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.do_import()

    def test_clean_import_is_admitted_offline_and_resolved(self) -> None:
        for resolver in (None, self.resolver):
            report = pi.check(self.root, resolver)
            self.assertEqual(report["verdict"], "ADMITTED", report)
            self.assertEqual(report["directories"][0]["rows_admitted"], 1)

    def test_tampered_copy_is_digest_mismatch(self) -> None:
        (self.imports / "RFC-9999.md").write_bytes(RFC.replace(b"A premise", b"A forgery"))
        self.assertEqual(self.codes(pi.check(self.root, None)), {"IMPORT_DIGEST_MISMATCH"})

    def test_hand_supplied_bytes_without_a_row_are_unlisted(self) -> None:
        (self.imports / "RFC-0006.md").write_bytes(b"hand copy\n")
        report = pi.check(self.root, None)
        self.assertEqual(self.codes(report), {"IMPORT_UNLISTED_COPY"})
        self.assertEqual(report["verdict"], "REFUSED")

    def test_missing_copy(self) -> None:
        (self.imports / "RFC-9999.md").unlink()
        self.assertEqual(self.codes(pi.check(self.root, None)), {"IMPORT_COPY_MISSING"})

    def _edit_row(self, **fields) -> None:
        path = self.imports / "IMPORTS.json"
        doc = json.loads(path.read_text())
        doc["imports"][0].update(fields)
        path.write_text(json.dumps(doc))

    def test_escaping_path_is_refused_before_any_read(self) -> None:
        for bad in ("../../CONSTITUTION.md", "/etc/passwd", "imports/sub/x.md", "RFC-9999.md", "imports/IMPORTS.json"):
            with self.subTest(bad=bad):
                self._edit_row(path=bad)
                self.assertIn("IMPORT_PATH_ESCAPE", self.codes(pi.check(self.root, None)))

    def test_malformed_rows(self) -> None:
        for field, bad in (("source_sha", "abc"), ("sha256", "sha256:x"), ("source_blob_sha1", ""), ("standing", "ok"), ("owner", None)):
            with self.subTest(field=field):
                self.do_import(replace=True)
                self._edit_row(**{field: bad})
                self.assertIn("IMPORT_ROW_MALFORMED", self.codes(pi.check(self.root, None)))

    def test_duplicate_rows(self) -> None:
        path = self.imports / "IMPORTS.json"
        doc = json.loads(path.read_text())
        doc["imports"].append(dict(doc["imports"][0]))
        path.write_text(json.dumps(doc))
        self.assertEqual(self.codes(pi.check(self.root, None)), {"IMPORT_DUPLICATE_PATH"})

    def test_self_consistent_forgery_is_caught_only_by_source_resolution(self) -> None:
        # Rewrite copy AND row digests coherently: the offline court cannot see it; the source can.
        forged = RFC + b"injected premise\n"
        (self.imports / "RFC-9999.md").write_bytes(forged)
        self._edit_row(sha256=pi.sha256_hex(forged), source_blob_sha1=pi.git_blob_id(forged))
        self.assertEqual(pi.check(self.root, None)["verdict"], "ADMITTED")
        self.assertEqual(self.codes(pi.check(self.root, self.resolver)), {"IMPORT_SOURCE_DRIFT"})

    def test_unreachable_source_is_reported_but_not_a_refusal(self) -> None:
        report = pi.check(self.root, Resolver(self.tmp / "nowhere", allow_network=False))
        self.assertEqual(self.codes(report), {"TRANSPORT_UNAVAILABLE"})
        self.assertEqual((report["verdict"], report["refusals"], report["transport_unavailable"]), ("ADMITTED", 0, 1))

    def test_cli_exit_codes(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(pi.main(["check", "--root", str(self.root), "--json"]), 0)
        (self.imports / "RFC-9999.md").write_bytes(b"x")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pi.main(["check", "--root", str(self.root)]), 1)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(pi.main(["--no-network", "import", self.locator, "--into", str(self.root), "--as", "x.md", "--owner", "o"]), 2)


class Committed(unittest.TestCase):
    def test_every_committed_release_import_recomputes_offline(self) -> None:
        report = pi.check(REPO, None)
        self.assertEqual(report["verdict"], "ADMITTED", json.dumps(report, indent=2))
        self.assertGreaterEqual(sum(d["rows_admitted"] for d in report["directories"]), 2)

    def test_machine_import_replays_the_committed_hand_imports_byte_identically(self) -> None:
        repos = os.environ.get("PREMISE_IMPORT_REPOS_ROOT")
        if not repos:
            self.skipTest("PREMISE_IMPORT_REPOS_ROOT unset: no engineering-standards checkout to replay from")
        resolver = Resolver(Path(repos), allow_network=False)
        for imports_dir in pi.discover(REPO):
            doc = json.loads((imports_dir / "IMPORTS.json").read_text())
            with self.subTest(imports_dir=str(imports_dir.relative_to(REPO))), tempfile.TemporaryDirectory() as t:
                out = Path(t) / "imports"
                for row in doc["imports"]:
                    pi.import_premise(
                        resolver,
                        f"git:{row['source_repo']}@{row['source_sha']}:{row['source_path']}",
                        out,
                        row["path"].split("/", 1)[1],
                        row["owner"],
                        row["standing"],
                        row.get("scope"),
                    )
                for f in sorted(imports_dir.iterdir()):
                    self.assertEqual((out / f.name).read_bytes(), f.read_bytes(), f.name)


if __name__ == "__main__":
    unittest.main()


CATALOG = """schema = "premise-imports.v1"

[[source]]
repository = "o/standards"
ref = "main"
pattern = '^rfc/(?P<number>[0-9]{4})-(?P<release>v[0-9]+\\.[0-9]+\\.[0-9]+)-[a-z0-9-]+\\.md$'
status_prefix = "**Status:** FINAL_SPEC"
copy_name = "RFC-{number}.md"
into = "release/{release}/imports"
standing = "NOT_A_SPEC"
since = "v26.9.25"

[[source.override]]
number = "0007"
into = "release/{release}/autonomy/imports"
scope = "POST_TAG"
"""


def rfc(status: str, body: str = "") -> bytes:
    return f"# RFC\n\n**Status:** {status}\n\n{body}\n".encode()


class Plan(unittest.TestCase):
    """plan/sync over a real owner repository whose premises land by --no-ff merges."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.src = self.tmp / "repos" / "standards"
        commit(self.src, {"README.md": b"standards\n"})
        self.root = self.tmp / "root"
        (self.root / "catalog").mkdir(parents=True)
        (self.root / "catalog" / "premise-imports.toml").write_text(CATALOG)
        self.resolver = Resolver(self.tmp / "repos", allow_network=False)
        self.merges: dict[str, str] = {}

    def merge(self, pr: int, files: dict[str, bytes]) -> str:
        git(self.src, "checkout", "-q", "-b", f"pr{pr}")
        commit(self.src, files)
        git(self.src, "checkout", "-q", "main")
        git(self.src, "-c", "user.name=t", "-c", "user.email=t@e.invalid", "merge", "-q", "--no-ff", f"pr{pr}", "-m", f"Merge pull request #{pr} from o/pr{pr}")
        return git(self.src, "rev-parse", "HEAD")

    def plan(self, release: str | None = None) -> dict:
        return pi.plan(self.root, self.resolver, release)

    def by_number(self, report: dict) -> dict[str, dict]:
        return {r["number"]: r for r in report["premises"]}

    def test_final_premise_is_missing_until_synced_at_its_admitting_merge(self) -> None:
        m = self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC — v26.9.26 premise")})
        report = self.plan()
        self.assertEqual(report["verdict"], "REFUSED")
        row = self.by_number(report)["0006"]
        self.assertEqual((row["status"], row["locator"]), ("MISSING", f"git:o/standards@{m}:rfc/0006-v26.9.26-next.md"))
        self.assertEqual(row["owner"], f"o/standards (PR #6, FINAL_SPEC; merge {m[:8]})")
        after = pi.sync(self.root, self.resolver)
        self.assertEqual(after["verdict"], "ADMITTED")
        idx = json.loads((self.root / "release/v26.9.26/imports/IMPORTS.json").read_text())["imports"]
        self.assertEqual([(r["path"], r["source_sha"]) for r in idx], [("imports/RFC-0006.md", m)])
        self.assertEqual(pi.check(self.root, self.resolver)["verdict"], "ADMITTED")
        before = (self.root / "release/v26.9.26/imports/IMPORTS.json").read_bytes()
        pi.sync(self.root, self.resolver)
        self.assertEqual((self.root / "release/v26.9.26/imports/IMPORTS.json").read_bytes(), before)

    def test_amendment_after_admission_keeps_the_admitting_merge(self) -> None:
        m = self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC")})
        self.merge(8, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC", "amended")})
        row = self.by_number(self.plan())["0006"]
        self.assertEqual(parse_sha(row["locator"]), m)
        self.assertEqual(len(row["amended_after_admission"]), 1)

    def test_withdrawn_then_readmitted_premise_binds_the_readmitting_merge(self) -> None:
        self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC", "first")})
        git(self.src, "rm", "-q", "rfc/0006-v26.9.26-next.md")
        git(self.src, "-c", "user.name=t", "-c", "user.email=t@e.invalid", "commit", "-q", "-m", "withdraw")
        again = self.merge(9, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC", "second")})
        row = self.by_number(self.plan())["0006"]
        self.assertEqual(parse_sha(row["locator"]), again)
        self.assertEqual(row["owner"], f"o/standards (PR #9, FINAL_SPEC; merge {again[:8]})")

    def test_non_final_premise_is_never_imported(self) -> None:
        self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("Proposed for v26.9.26")})
        report = pi.sync(self.root, self.resolver)
        self.assertEqual(self.by_number(report)["0006"]["status"], "NOT_ADMITTED")
        self.assertFalse((self.root / "release/v26.9.26").exists())
        self.assertEqual(self.plan("v26.9.26")["verdict"], "BLOCKED(PREMISE_ABSENT:E-ADM-01)")

    def test_import_of_a_non_final_source_is_refused(self) -> None:
        m = self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("Proposed")})
        pi.import_premise(self.resolver, f"git:o/standards@{m}:rfc/0006-v26.9.26-next.md",
                          self.root / "release/v26.9.26/imports", "RFC-0006.md", "hand", "NOT_A_SPEC")
        report = self.plan()
        self.assertEqual(self.by_number(report)["0006"]["status"], "IMPORTED_NOT_FINAL")
        self.assertEqual(pi.plan_exit(report), 1)

    def test_import_bound_to_another_subject_differs_and_sync_does_not_rebind(self) -> None:
        self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC")})
        side = commit(self.src, {"side.md": rfc("FINAL_SPEC", "not the admitted bytes")})
        pi.import_premise(self.resolver, f"git:o/standards@{side}:side.md",
                          self.root / "release/v26.9.26/imports", "RFC-0006.md", "hand", "NOT_A_SPEC")
        before = (self.root / "release/v26.9.26/imports/IMPORTS.json").read_bytes()
        report = pi.sync(self.root, self.resolver)
        self.assertEqual(self.by_number(report)["0006"]["status"], "SUBJECT_DIFFERS")
        self.assertEqual(report["verdict"], "REFUSED")
        self.assertEqual((self.root / "release/v26.9.26/imports/IMPORTS.json").read_bytes(), before)

    def test_override_lane_and_scope_and_since_floor(self) -> None:
        self.merge(7, {"rfc/0007-v26.9.26-amend.md": rfc("FINAL_SPEC"), "rfc/0002-v26.9.24-old.md": rfc("FINAL_SPEC")})
        report = pi.sync(self.root, self.resolver)
        self.assertEqual(set(self.by_number(report)), {"0007"})  # v26.9.24 is below since
        row = json.loads((self.root / "release/v26.9.26/autonomy/imports/IMPORTS.json").read_text())["imports"][0]
        self.assertEqual((row["path"], row["scope"]), ("imports/RFC-0007.md", "POST_TAG"))

    def test_release_filter_and_absent_line(self) -> None:
        self.merge(6, {"rfc/0006-v26.9.26-next.md": rfc("FINAL_SPEC")})
        self.assertEqual([r["release"] for r in self.plan("v26.9.26")["premises"]], ["v26.9.26"])
        absent = self.plan("v26.9.27")
        self.assertEqual((absent["verdict"], absent["premises"]), ("BLOCKED(PREMISE_ABSENT:E-ADM-01)", []))
        self.assertEqual(pi.plan_exit(absent), 3)

    def test_missing_checkout_is_transport_blocked_not_absent(self) -> None:
        report = pi.plan(self.root, Resolver(self.tmp / "nowhere", allow_network=False), "v26.9.26")
        self.assertEqual(report["verdict"], "BLOCKED(TRANSPORT_UNAVAILABLE)")
        self.assertEqual(report["sources"][0]["status"], "TRANSPORT_UNAVAILABLE")


def parse_sha(locator: str) -> str:
    return locator.split("@", 1)[1].split(":", 1)[0]


class CommittedPlan(unittest.TestCase):
    def test_committed_imports_are_exactly_the_derived_plan(self) -> None:
        repos = os.environ.get("PREMISE_IMPORT_REPOS_ROOT")
        if not repos:
            self.skipTest("PREMISE_IMPORT_REPOS_ROOT unset: no engineering-standards checkout")
        report = pi.plan(REPO, Resolver(Path(repos), allow_network=False))
        self.assertEqual(report["verdict"], "ADMITTED", json.dumps(report, indent=2))
        planned = {(r["into"], r["copy_name"]) for r in report["premises"] if r["status"] == "IMPORTED"}
        committed = {
            (d.relative_to(REPO).as_posix(), r["path"].split("/", 1)[1])
            for d in pi.discover(REPO)
            for r in json.loads((d / "IMPORTS.json").read_text())["imports"]
        }
        self.assertEqual(planned, committed)
