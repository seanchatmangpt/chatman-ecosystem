"""CE23-1 court: the release-subject falsifier and the predecessor fence, judged on real repositories.

Chicago style: every case builds a real git repository in a temporary directory (release/v26.9.1
materialized with `git archive` from this checkout's pinned base commit) and judges it with the
court's own judge() (release/v26.9.23/courts/ce23_1/court.py), running the real git and tar. No
collaborator is replaced. V1's publication typing is judged against real marketplace repositories
built here (published, pending fast-forward, diverged, off the line, unobserved) and, on the real
vendored pin, against the court's synthetic marketplaces over the canonical checkout's objects. The
full subject (ggen render, vendored pack, imports, verify_release, the mutant corpus) is judged by
`sh release/v26.9.23/courts/CE23-1.sh`, not here.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURT_DIR = ROOT / "release" / "v26.9.23" / "courts" / "ce23_1"
SPEC = importlib.util.spec_from_file_location("ce23_1_court", COURT_DIR / "court.py")
assert SPEC is not None and SPEC.loader is not None
court = importlib.util.module_from_spec(SPEC)
sys.modules["ce23_1_court"] = court
SPEC.loader.exec_module(court)


class SubjectCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-1-test.")
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        try:
            self.env = court.Env(tmp / "home")
        except court.Environment as exc:
            self.skipTest(f"court environment absent: {exc}")
        base_commit = court.SUBJ["base_commit"]
        if self.env.git_(ROOT, "cat-file", "-e", f"{base_commit}^{{commit}}").returncode != 0:
            self.skipTest(f"this checkout holds no base commit {base_commit}")
        self.repo = tmp / "repo"
        self.repo.mkdir()
        self.assertEqual(self.env.git_(self.repo, "init", "-q", "-b", "main").returncode, 0)
        self.env.archive(ROOT, base_commit, [court.PRED_DIR], self.repo)
        self.base = self.env.commit_all(self.repo, "base")
        self.work = tmp / "work"

    def judge(self) -> court.Verdict:
        return court.judge(self.repo, self.base, self.env, self.work)

    def test_no_subject_is_refused_while_predecessor_holds(self) -> None:
        self.env.commit_all(self.repo, "head without a v26.9.23 subject")
        v = self.judge()
        self.assertIn("SUBJECT_ABSENT", v.refused)
        self.assertNotIn("PREDECESSOR_CHANGED", v.refused)
        self.assertTrue(any(line.startswith("OK P1:") for line in v.lines), v.lines)
        self.assertFalse(v.alive)

    def test_predecessor_change_is_refused(self) -> None:
        (self.repo / court.PRED_DIR / "manifest.toml").write_text("[release]\nversion = \"26.9.1\"\n", encoding="utf-8")
        self.env.commit_all(self.repo, "head that rewrites the v26.9.1 manifest")
        v = self.judge()
        self.assertIn("PREDECESSOR_CHANGED", v.refused)
        refusal = next(line for line in v.lines if line.startswith("REFUSED[PREDECESSOR_CHANGED] P1"))
        self.assertIn("release/v26.9.1/manifest.toml", refusal)

    def test_uncommitted_predecessor_edit_is_refused(self) -> None:
        self.env.commit_all(self.repo, "head")
        with (self.repo / court.PRED_DIR / "fleet-policy.toml").open("a", encoding="utf-8") as f:
            f.write("# uncommitted\n")
        self.assertIn("PREDECESSOR_DIRTY", self.judge().refused)

    def test_orphan_base_is_refused(self) -> None:
        self.env.commit_all(self.repo, "head")
        v = court.judge(self.repo, "0" * 40, self.env, self.work)
        self.assertIn("BASE_NOT_ANCESTOR", v.refused)


class ClauseCase(unittest.TestCase):
    """A4 (closed-world ggen.toml), A5 (no symlink beyond the line pointers) and C1 (the judging
    court is the head's) on a small real repository judged from git objects; no ggen run."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-1-clause.")
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        try:
            self.env = court.Env(tmp / "home")
        except court.Environment as exc:
            self.skipTest(f"court environment absent: {exc}")
        self.outside = tmp / "outside"
        self.outside.mkdir()
        self.repo = tmp / "repo"
        self.repo.mkdir()
        self.assertEqual(self.env.git_(self.repo, "init", "-q", "-b", "main").returncode, 0)
        sub = self.sub = self.repo / court.SDIR
        pack = f"{court.SUBJ['vendor_dir']}/packs/p"
        for rel, text in {
            "release.ttl": "# release facts\n",
            "templates/.gitkeep": "",
            court.SUBJ["classification_import"]: "# classification bytes\n",
            f"{pack}/pack.toml": "[pack]\nname = \"p\"\n",
            "out/manifest.toml": "[release]\n",
            "out/constitutional-role-crosswalk.toml": "[constitutional]\n",
            "ggen.toml": ('[project]\nname = "t"\n\n[ontology]\nsource = "release.ttl"\n\n[templates]\ndir = "templates"\n\n'
                          f'[packs]\np = {{ path = "{pack}", lock = true, extra_ontologies = '
                          f'["{court.SUBJ["classification_import"]}"] }}\n'),
        }.items():
            (sub / rel).parent.mkdir(parents=True, exist_ok=True)
            (sub / rel).write_text(text, encoding="utf-8")
        for name, target in court.SUBJ["line_pointers"].items():
            (sub / name).symlink_to(target)
        for rel, data in court.COURT_BYTES.items():
            assert data is not None
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_bytes(data)

    def judged(self) -> court.Verdict:
        head = self.env.commit_all(self.repo, "head")
        v = court.Verdict()
        court.config_law(v, self.repo, head, self.env)
        court.self_contained(v, self.repo, head, self.env)
        court.court_identity(v, self.repo, head, self.env)
        return v

    def refusal(self, v: court.Verdict, prefix: str) -> str:
        for line in v.lines:
            if line.startswith(prefix):
                return line
        self.fail(f"no {prefix!r} line in {v.lines}")

    def test_contained_closed_world_subject_under_its_committed_court_is_admitted(self) -> None:
        v = self.judged()
        self.assertTrue(v.alive, v.lines)
        self.assertEqual([line.split(":")[0] for line in v.lines], ["OK A4", "OK A5", "OK C1"])

    def test_import_as_absolute_symlink_to_identical_bytes_is_refused(self) -> None:
        f = self.sub / court.SUBJ["classification_import"]
        (self.outside / f.name).write_bytes(f.read_bytes())
        f.unlink()
        f.symlink_to(self.outside / f.name)
        v = self.judged()
        a5 = self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A5")
        self.assertIn(f"{court.SDIR}/{court.SUBJ['classification_import']} (120000 symlink) -> {self.outside}", a5)
        self.assertNotIn(f"{court.SDIR}/manifest.toml (", a5)  # the pinned line pointers stay admitted
        a4 = self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A4")
        self.assertIn(f"{court.SUBJ['classification_import']!r} is ['120000', 'blob']", a4)

    def test_config_key_outside_the_judged_schema_is_refused(self) -> None:
        with (self.sub / "ggen.toml").open("a", encoding="utf-8") as fh:
            fh.write("\n[law]\nreflexive = true\n")
        v = self.judged()
        self.assertEqual(v.refused, ["CONFIG_UNJUDGED"], v.lines)
        self.assertIn("law.reflexive", self.refusal(v, "REFUSED[CONFIG_UNJUDGED] A4"))

    def test_read_path_not_committed_in_the_subject_is_refused(self) -> None:
        text = (self.sub / "ggen.toml").read_text(encoding="utf-8")
        (self.sub / "ggen.toml").write_text(text.replace("extra_ontologies = [", 'extra_ontologies = ["imports/absent.ttl", '),
                                            encoding="utf-8")
        v = self.judged()
        self.assertIn("imports/absent.ttl", self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A4"))
        self.assertIn("not committed", self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A4"))

    def test_committed_pins_other_than_the_judging_court_are_refused(self) -> None:
        with (self.repo / court.SDIR / "courts/ce23_1/subject.toml").open("a", encoding="utf-8") as fh:
            fh.write("# re-pinned\n")
        v = self.judged()
        self.assertEqual(v.refused, ["COURT_NOT_AT_HEAD"], v.lines)
        self.assertIn("courts/ce23_1/subject.toml (differs", self.refusal(v, "REFUSED[COURT_NOT_AT_HEAD] C1"))


class VendorCase(unittest.TestCase):
    """V1 on a real subject repository whose vendored pack is byte-identical to a real marketplace
    repository; only the marketplace refs (what is published, what the local line holds) vary."""

    REF = "release/line"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-1-vendor.")
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        try:
            self.env = court.Env(tmp / "home")
        except court.Environment as exc:
            self.skipTest(f"court environment absent: {exc}")
        self.market = tmp / "market"
        self.market.mkdir()
        self.assertEqual(self.env.git_(self.market, "init", "-q", "-b", "main").returncode, 0)
        (self.market / "README.md").write_text("marketplace\n", encoding="utf-8")
        self.parent = self.env.commit_all(self.market, "base")
        pack = {"pack.toml": "[pack]\nname = \"p\"\n", "gates/010.rq": "ASK {}\n"}
        for rel, text in pack.items():
            (self.market / "packs/p" / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.market / "packs/p" / rel).write_text(text, encoding="utf-8")
        self.pin = self.env.commit_all(self.market, "pack p")
        tree = self.env.out(self.market, "rev-parse", f"{self.pin}:packs/p")
        self.repo = tmp / "repo"
        self.repo.mkdir()
        self.assertEqual(self.env.git_(self.repo, "init", "-q", "-b", "main").returncode, 0)
        sub = self.sub = self.repo / court.SDIR
        vendored = sub / court.SUBJ["vendor_dir"] / "packs/p"
        for rel, text in pack.items():
            (vendored / rel).parent.mkdir(parents=True, exist_ok=True)
            (vendored / rel).write_text(text, encoding="utf-8")
        (sub / court.SUBJ["vendor_dir"] / "VENDOR.toml").write_text(
            f'[[pack]]\nname = "p"\nversion = "0.1.0"\nsubdir = "packs/p"\nrepository = "o/m"\nref = "{self.REF}"\n'
            f'commit = "{self.pin}"\ntree = "{tree}"\n', encoding="utf-8")
        (sub / "ggen.toml").write_text(f'[packs]\np = {{ path = "{court.SUBJ["vendor_dir"]}/packs/p", lock = true }}\n',
                                       encoding="utf-8")
        self.head = self.env.commit_all(self.repo, "subject")

    def refs(self, remote: str | None, local: str | None) -> None:
        for name, sha in ((f"refs/remotes/origin/{self.REF}", remote), (f"refs/heads/{self.REF}", local)):
            if sha:
                self.assertEqual(self.env.git_(self.market, "update-ref", name, sha).returncode, 0)

    def judged(self, market: Path | None = None) -> court.Verdict:
        v = court.Verdict()
        court.vendor(v, self.repo, self.head, self.sub, self.env, market or self.market)
        return v

    def v1(self, v: court.Verdict) -> list[str]:
        return [line.split(" V1:")[0] for line in v.lines if " V1:" in line]

    def test_published_pin_is_admitted(self) -> None:
        self.refs(self.pin, self.pin)
        v = self.judged()
        self.assertTrue(v.alive, v.lines)
        self.assertEqual(self.v1(v), ["OK", "OK"])

    def test_pending_fast_forward_is_an_edge_never_a_counterexample(self) -> None:
        self.refs(self.parent, self.pin)
        v = self.judged()
        self.assertEqual((v.refused, v.unknowns), ([], ["VENDOR_PUBLICATION_PENDING"]), v.lines)
        self.assertFalse(v.alive)
        pending = next(line for line in v.lines if line.startswith("UNKNOWN[VENDOR_PUBLICATION_PENDING]"))
        self.assertIn("fast-forwards", pending)

    def test_pin_off_the_published_line_is_refused(self) -> None:
        # the local line diverges from the published ref: publishing the pin would need a force
        sibling = self.env.run([self.env.git, "-C", str(self.market), "-c", "user.name=t", "-c", "user.email=t@localhost",
                                "commit-tree", f"{self.pin}^{{tree}}", "-p", self.parent, "-m", "sibling"]).stdout.strip()
        self.refs(sibling, self.pin)
        v = self.judged()
        self.assertEqual(v.refused, ["VENDOR_COMMIT_OFF_REF"], v.lines)
        self.assertIn("diverged", next(line for line in v.lines if line.startswith("REFUSED[VENDOR_COMMIT_OFF_REF]")))
        # neither the published ref nor the local line holds the pin
        self.refs(self.parent, self.parent)
        self.assertEqual(self.judged().refused, ["VENDOR_COMMIT_OFF_REF"])

    def test_unobserved_published_ref_is_unknown(self) -> None:
        self.refs(None, self.pin)
        v = self.judged()
        self.assertEqual((v.refused, v.unknowns), ([], ["MARKETPLACE_REF_UNOBSERVED"]), v.lines)

    def test_court_synthetic_marketplaces_type_the_real_vendored_pin(self) -> None:
        """The court's own AV instrument on the real vendored pin: only the refs differ."""
        real = court.marketplace_repo()
        rows = tomllib.loads((ROOT / court.SDIR / court.SUBJ["vendor_dir"] / "VENDOR.toml").read_text(encoding="utf-8"))["pack"]
        if self.env.git_(real, "cat-file", "-e", f"{rows[0]['commit']}^{{commit}}").returncode != 0:
            self.skipTest(f"canonical marketplace checkout {real} holds no vendored pin {rows[0]['commit']}")
        head = self.env.out(ROOT, "rev-parse", "HEAD")
        want = {"published": ([], []), "pending": ([], ["VENDOR_PUBLICATION_PENDING"]), "diverged": (["VENDOR_COMMIT_OFF_REF"], [])}
        for state, expected in want.items():
            market = court.synthetic_marketplace(self.env, ROOT, Path(self.tmp.name) / f"{state}.git", state)
            v = court.Verdict()
            court.vendor(v, ROOT, head, ROOT / court.SDIR, self.env, market)
            self.assertEqual((v.refused, v.unknowns), expected, (state, v.lines))
            # the synthetic marketplace borrows the canonical objects: its own store holds at most the sibling
            loose = [p for p in (market / "objects").rglob("*") if p.is_file() and p.parent.name not in ("info", "pack")]
            self.assertLessEqual(len(loose), 1, (state, loose))


class RenderCase(unittest.TestCase):
    def test_committed_render_binds_the_classification_to_the_xaas_component(self) -> None:
        manifest = ROOT / court.SDIR / "manifest.toml"
        if not manifest.is_file():
            self.skipTest(f"{manifest} absent")
        doc = tomllib.loads(manifest.read_text(encoding="utf-8"))
        match = court.SOURCE_RE.match(doc["release"]["classification_source"])
        self.assertIsNotNone(match, doc["release"]["classification_source"])
        pinned = {c["repository"]: c["sha"] for c in doc["components"] if c["required"] is True}
        self.assertEqual(pinned.get(match["repo"]), match["sha"])
        data = (ROOT / court.SDIR / court.SUBJ["classification_import"]).read_bytes()
        self.assertEqual(court.sha256(data), match["digest"])


if __name__ == "__main__":
    unittest.main()
