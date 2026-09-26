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
