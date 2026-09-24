"""Topology guard: repository topology is transport, never ontology (scripts/topology_guard.py).

No committed executable, source, config, court, query, ontology or test file names a shadow checkout
(an absolute, home-relative or $HOME path into the home directory's retired shadow tree) or runs
git's worktree-add subcommand. Receipts, recorded evidence JSON, migration/ and prose docs that quote
history are evidence and are not scanned; a hit in a file another owner pins is legal only while its
scripts/topology_guard.toml residue row holds (pin intact, exact hit count).

Chicago style: the guard runs on the real tracked tree of this checkout (real `git ls-files`), and
its falsifiers run it on real git repositories built in temporary directories: planted references in
real files, real commits, real tree ids and real sha256 pins, and the real CLI as a subprocess.
Every shadow needle below is assembled from pieces so this file never names one itself.
"""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "topology_guard.py"
SPEC = importlib.util.spec_from_file_location("topology_guard", GUARD)
assert SPEC is not None and SPEC.loader is not None
tg = importlib.util.module_from_spec(SPEC)
sys.modules["topology_guard"] = tg
SPEC.loader.exec_module(tg)

SH = "w" + "t"
ABS = "/Users/alice/" + SH + "/v1/int"
TILDE = "~/" + SH + "/v1/lane"
ENV = "$HOME/" + SH + "/v1"
ADD = "git " + "work" + "tree" + " add"
ARGV = '["' + "work" + "tree" + '", "add", str(tree)]'
JOIN = 'Path.home() / "' + SH + '" / "v1"'


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"git {args}: {proc.stderr}")
    return proc.stdout.strip()


def is_checkout(root: Path) -> bool:
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    return proc.returncode == 0 and proc.stdout.strip() == "true"


class RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="topology-guard.")
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "guard@example.invalid")
        git(self.repo, "config", "user.name", "guard")
        git(self.repo, "config", "commit.gpgsign", "false")

    def write(self, files: dict[str, str], executable: tuple[str, ...] = ()) -> None:
        for rel, text in files.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            if rel in executable:
                path.chmod(0o755)

    def commit(self, files: dict[str, str] | None = None, executable: tuple[str, ...] = ()) -> str:
        if files:
            self.write(files, executable)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "subject")
        return git(self.repo, "rev-parse", "HEAD")

    def owned(self, report: Any) -> set[tuple[str, str]]:
        return {(hit.path, code) for hit in report.owned for code in hit.codes}

    def refused(self, report: Any) -> list[str]:
        return [code for code, _ in report.refused]

    def cli(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(GUARD), "--root", str(self.repo)], capture_output=True, text=True)


@unittest.skipUnless(is_checkout(ROOT), "the guard judges a git checkout; this tree has no .git")
class CommittedTreeCase(unittest.TestCase):
    """The real tracked tree of this repository."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = tg.scan(ROOT)

    def test_no_owned_shadow_reference_and_every_residue_row_holds(self) -> None:
        self.assertEqual(self.report.unknown, [])
        self.assertEqual([hit.render() for hit in self.report.owned], [])
        self.assertEqual(self.report.refused, [])
        self.assertEqual(self.report.standing, "ALIVE")

    def test_scope_is_not_vacuous(self) -> None:
        # thousands of tracked code/config/ontology files are read, including the guard and this test
        self.assertGreater(self.report.scanned, 1000)
        self.assertEqual(tg.classify("scripts/topology_guard.py", "100644", b""), "scanned")
        self.assertEqual(tg.classify("tests/test_topology_guard.py", "100644", b""), "scanned")
        self.assertEqual(tg.classify("release/v26.9.23/courts/CE23-9.sh", "100755", b"#!"), "scanned")
        self.assertEqual(tg.classify("release/v26.9.23/release.ttl", "100644", b""), "scanned")
        self.assertEqual(tg.classify("platform-console/services/autofde-lab-mcp/src/autofde_lab/receipts/core.py",
                                     "100644", b""), "scanned")

    def test_ledger_rows_are_typed_and_foreign(self) -> None:
        rows = tomllib.loads((ROOT / tg.LEDGER_REL).read_text(encoding="utf-8"))["residue"]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["kind"], tg.KINDS, row["id"])
            self.assertTrue(row["owner"] and row["edge"] and row["hits"] > 0, row["id"])
            # a residue row never covers chatman-owned code: courts, scripts, tests, workflows
            for pattern in row["paths"]:
                self.assertFalse(pattern.startswith(("scripts/", "tests/", ".github/", "release/v26.9.23/courts/")),
                                 pattern)
        self.assertEqual(sorted(self.report.residue), sorted(row["id"] for row in rows))
        self.assertEqual({rid: len(hits) for rid, hits in self.report.residue.items()},
                         {row["id"]: row["hits"] for row in rows})

    def test_moved_driver_records_are_byte_evidence_not_scanned(self) -> None:
        for rel in ("migration/v26923-single-repo/driver/DRIVER.md", "release/v26.9.23/sjira/annex/scan-plan.json"):
            self.assertTrue((ROOT / rel).is_file(), rel)
            self.assertEqual(tg.classify(rel, "100644", b""), "evidence" if rel.startswith("migration/") else "other")


class PlantedCase(RepoCase):
    """Falsifiers: planted references in a real repository are refused, typed by kind."""

    def test_planted_references_are_refused_by_kind(self) -> None:
        self.commit({
            "scripts/a.py": f'ROOT = "{ABS}"\n',
            "courts/c.sh": f"#!/bin/sh\ncd {TILDE} && make\n",
            "Makefile": f"X := {ENV}/x\n",
            "ontology/o.ttl": f'<urn:a> <urn:b> "{ABS}/COORDINATION.md" .\n',
            "tools/run": f"#!/bin/sh\n{ADD} --detach /tmp/x HEAD\n",
            "tools/exec.py": f"ARGS = {ARGV}\n",
            "templates/t.tmpl": f"P = {JOIN}\n",
            ".github/workflows/w.yml": f"steps:\n  - run: cd {ABS}\n",
        }, executable=("courts/c.sh",))
        report = tg.scan(self.repo)
        self.assertEqual(self.owned(report), {
            ("scripts/a.py", "SHADOW_ABSOLUTE_PATH"),
            ("courts/c.sh", "SHADOW_TILDE_PATH"),
            ("Makefile", "SHADOW_ENV_HOME_PATH"),
            ("ontology/o.ttl", "SHADOW_ABSOLUTE_PATH"),
            ("tools/run", "WORKTREE_ADD"),
            ("tools/exec.py", "WORKTREE_ADD_ARGV"),
            ("templates/t.tmpl", "SHADOW_PATHLIB_JOIN"),
            (".github/workflows/w.yml", "SHADOW_ABSOLUTE_PATH"),
        })
        self.assertEqual(report.standing, "REFUSED")
        proc = self.cli()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("REFUSED[SHADOW_REFERENCE] scripts/a.py:1 SHADOW_ABSOLUTE_PATH", proc.stdout)

    def test_evidence_and_near_misses_are_not_references(self) -> None:
        self.commit({
            "receipts/v1/X.json": f'{{"cmd": "cd {ABS}"}}\n',
            "receipts/v1/X.gate/01.log": f"$ {ADD} /tmp/x\n",
            "receipts/v1/X.gate/probe.py": f'P = "{ABS}"\n',
            "release/r/out/receipts/r.toml": f'path = "{ABS}"\n',
            "migration/m/DRIVER.md": f"lanes live in {ABS}\n",
            "migration/m/tool.sh": f"{ADD} x\n",
            "docs/history.md": f"the int checkout was {TILDE}\n",
            "evidence/run.json": f'{{"tree": "{ABS}"}}\n',
            "scripts/ok.py": "\n".join([
                'A = "/Users/alice/' + SH + 'f/x"',          # a different directory name
                'B = "~/' + SH + 'x"',
                'C = "/Users/alice/src/' + SH + '-lab"',     # shadow name deeper than the home directory
                'D = "git ' + "work" + 'tree list"',          # another subcommand
                'E = str(Path.home() / "' + SH + '") + "/"',  # a needle, joined no further
            ]) + "\n",
        })
        report = tg.scan(self.repo)
        self.assertEqual(self.owned(report), set())
        self.assertEqual(report.standing, "ALIVE")
        proc = self.cli()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_tracked_tree_is_judged_and_a_staged_plant_is_seen(self) -> None:
        self.commit({"scripts/clean.py": "X = 1\n"})
        (self.repo / "scripts" / "new.py").write_text(f'P = "{ABS}"\n', encoding="utf-8")
        self.assertEqual(self.owned(tg.scan(self.repo)), set())  # untracked: not part of the tree
        git(self.repo, "add", "-N", "scripts/new.py")
        self.assertEqual(self.owned(tg.scan(self.repo)), {("scripts/new.py", "SHADOW_ABSOLUTE_PATH")})
        # a plant in an existing tracked file is seen before any commit
        (self.repo / "scripts" / "clean.py").write_text(f"X = 1\n{ADD} y\n", encoding="utf-8")
        self.assertIn(("scripts/clean.py", "WORKTREE_ADD"), self.owned(tg.scan(self.repo)))

    def test_not_a_checkout_is_unknown(self) -> None:
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        report = tg.scan(plain)
        self.assertEqual([code for code, _ in report.unknown], ["NOT_A_CHECKOUT"])
        proc = subprocess.run([sys.executable, str(GUARD), "--root", str(plain)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 75, proc.stdout + proc.stderr)
        self.assertIn("UNKNOWN[NOT_A_CHECKOUT]", proc.stdout)


class ResidueCase(RepoCase):
    """A foreign pinned copy is admitted only while its pin holds and its hit count is exact."""

    def ledger(self, rows: str) -> None:
        self.write({"scripts/topology_guard.toml": rows})

    def test_sha256_pin_admits_only_the_pinned_bytes(self) -> None:
        body = f'<urn:x> <urn:y> "{ABS}" .\n<urn:x> <urn:z> "{ABS}/b" .\n'
        digest = hashlib.sha256(body.encode()).hexdigest()
        self.ledger('[[residue]]\nid = "imp"\nkind = "sha256-pin"\npaths = ["imports/c.ttl"]\n'
                    'pin_file = "release.ttl"\nhits = 2\nowner = "o"\nedge = "e"\n')
        self.commit({"imports/c.ttl": body, "release.ttl": f'<urn:r> <urn:src> "sha256:{digest}" .\n'})
        report = tg.scan(self.repo)
        self.assertEqual((self.owned(report), report.refused, len(report.residue["imp"])), (set(), [], 2))
        # the copy drifts from its pin: the row lapses and the hits are the repository's own again
        self.commit({"imports/c.ttl": body + "# local edit\n"})
        report = tg.scan(self.repo)
        self.assertEqual(self.refused(report), ["RESIDUE_PIN_BROKEN", "RESIDUE_STALE"])
        self.assertEqual(self.owned(report), {("imports/c.ttl", "SHADOW_ABSOLUTE_PATH")})
        self.assertEqual(self.cli().returncode, 1)

    def test_hit_count_is_exact_and_a_stale_row_refuses(self) -> None:
        body = f'<urn:x> <urn:y> "{ABS}" .\n'
        digest = hashlib.sha256(body.encode()).hexdigest()
        self.ledger('[[residue]]\nid = "imp"\nkind = "sha256-pin"\npaths = ["imports/c.ttl"]\n'
                    'pin_file = "pins.toml"\nhits = 3\nowner = "o"\nedge = "e"\n\n'
                    '[[residue]]\nid = "gone"\nkind = "sha256-pin"\npaths = ["imports/fixed.ttl"]\n'
                    'pin_file = "pins.toml"\nhits = 1\nowner = "o"\nedge = "e"\n')
        self.commit({"imports/c.ttl": body, "imports/fixed.ttl": "<urn:x> <urn:y> <urn:z> .\n",
                     "pins.toml": f'c = "sha256:{digest}"\n'})
        report = tg.scan(self.repo)
        self.assertEqual(self.owned(report), set())
        self.assertEqual(sorted(self.refused(report)), ["RESIDUE_COUNT_CHANGED", "RESIDUE_STALE"])

    def test_vendored_copy_is_bound_to_the_recorded_tree(self) -> None:
        self.commit({"vendor/mk/packs/p/fixture.ttl": f'<urn:a> <urn:b> "{ABS}" .\n',
                     "vendor/mk/packs/p/pack.toml": 'name = "p"\n'})
        tree = git(self.repo, "rev-parse", "HEAD:vendor/mk/packs/p")
        self.ledger('[[residue]]\nid = "v"\nkind = "vendored"\npaths = ["vendor/mk/packs/p/*"]\n'
                    'vendor_file = "vendor/mk/VENDOR.toml"\nhits = 1\nowner = "o"\nedge = "e"\n')
        self.commit({"vendor/mk/VENDOR.toml": f'[[pack]]\nsubdir = "packs/p"\ntree = "{tree}"\n'})
        report = tg.scan(self.repo)
        self.assertEqual((self.owned(report), report.refused), (set(), []))
        # a file added inside the vendored pack moves its tree off the VENDOR.toml record
        self.commit({"vendor/mk/packs/p/local.txt": "fork\n"})
        report = tg.scan(self.repo)
        self.assertIn("RESIDUE_PIN_BROKEN", self.refused(report))
        self.assertEqual(self.owned(report), {("vendor/mk/packs/p/fixture.ttl", "SHADOW_ABSOLUTE_PATH")})

    def test_snapshot_copy_needs_its_writer_and_its_committed_bytes(self) -> None:
        self.ledger('[[residue]]\nid = "s"\nkind = "snapshot"\npaths = ["svc/src-snap/*"]\n'
                    'snapshot_root = "svc/src-snap"\nwriter = "svc/prep.sh"\nhits = 1\nowner = "o"\nedge = "e"\n')
        self.commit({"svc/src-snap/t.tmpl": f"{ADD} x\n",
                     "svc/prep.sh": '#!/bin/sh\ncp -R "$SRC" "$SELF/src-snap"\n'})
        self.assertEqual(tg.scan(self.repo).standing, "ALIVE")
        # a hand edit of the snapshot is not the snapshot any more
        (self.repo / "svc/src-snap/t.tmpl").write_text(f"{ADD} x\n# local\n", encoding="utf-8")
        self.assertIn("RESIDUE_PIN_BROKEN", self.refused(tg.scan(self.repo)))
        git(self.repo, "checkout", "--", "svc/src-snap/t.tmpl")
        # the writer stops writing it: the copy has no owner-side provenance left
        self.commit({"svc/prep.sh": "#!/bin/sh\ntrue\n"})
        report = tg.scan(self.repo)
        self.assertIn("RESIDUE_PIN_BROKEN", self.refused(report))
        self.assertEqual(self.owned(report), {("svc/src-snap/t.tmpl", "WORKTREE_ADD")})


if __name__ == "__main__":
    unittest.main()
