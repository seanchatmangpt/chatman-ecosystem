"""CE23-0 court: root identity clauses, judged on real git repositories.

Chicago style: every case runs the court's own functions (release/v26.9.23/courts/ce23_0/court.py)
over real repositories built with git in temporary directories (a bare "GitHub", a local-only lineage
and a checkout whose archive namespaces preserve it, exactly as the court's own corpus builds them),
the real vendored release pack gate runner, and the generated receipt validator CE23-9 pins (read
from the canonical ggen-marketplace checkout; the seal cases skip, named, without it). No
collaborator is replaced. The full subject run (live ls-remote of GitHub + the 33-case corpus) is
`sh release/v26.9.23/courts/CE23-0.sh`; these cases pin the verdict algebra it rests on.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURT_DIR = ROOT / "release" / "v26.9.23" / "courts" / "ce23_0"
SPEC = importlib.util.spec_from_file_location("ce23_0_court", COURT_DIR / "court.py")
assert SPEC is not None and SPEC.loader is not None
court = importlib.util.module_from_spec(SPEC)
sys.modules["ce23_0_court"] = court
SPEC.loader.exec_module(court)
SHADOW_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/wt(?:/|\b)")


class Scratch(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-0-test.")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = court.av_env(self.base / "home")

    def git(self, repo: Path, *args: str) -> str:
        return court.sh_git(repo, self.env, *args)

    def world(self, archive: bool = True) -> tuple[Path, Path, dict]:
        d = self.base / ("open" if archive else "bare")
        d.mkdir(exist_ok=True)
        return court.build_world(d, self.env, ROOT, with_archive=archive)

    def validator(self) -> dict:
        path, findings = court.validator_for(self.base)
        kind, code, text = findings[0]
        if path is None or kind != "OK":
            self.skipTest(f"pinned receipt validator not admitted here: {code} {text}")
        return {"path": path, "finding": findings[0]}

    def judge(self, work: Path, pins: dict, gh: Path | None, validator: dict | None = None) -> court.Judge:
        j = court.Judge(quiet=True)
        v = validator or {"path": None, "finding": ("SKIP", "", "no validation in this case")}
        scratch = self.base / f"s-{len(list(self.base.glob('s-*')))}"
        scratch.mkdir()
        court.judge(work, pins, j, self.env, scratch, v, transport=str(gh) if gh else None, law_root=ROOT)
        return j


class RelationCase(Scratch):
    def test_relation_is_total_over_real_histories(self) -> None:
        repo = self.base / "r"
        self.git(self.base, "init", "-q", "-b", "main", str(repo))
        a = court.commit_file(repo, self.env, "f", "a\n", "a")
        b = court.commit_file(repo, self.env, "f", "b\n", "b")
        self.git(repo, "checkout", "-q", "-b", "side", a)
        c = court.commit_file(repo, self.env, "f", "c\n", "c")
        self.git(repo, "checkout", "-q", "--orphan", "other")
        d = court.commit_file(repo, self.env, "f", "d\n", "d")
        g = court.Git(repo, self.env)
        self.assertEqual(g.relation(a, a), "equal")
        self.assertEqual(g.relation(a, b), "ancestor")
        self.assertEqual(g.relation(b, a), "descendant")
        self.assertEqual(g.relation(b, c), "diverged")
        self.assertEqual(g.relation(b, d), "unrelated")
        self.assertIsNone(g.relation(b, "0" * 40))
        self.assertEqual(g.roots(b, d), sorted([a, d]))


class UrlCase(unittest.TestCase):
    def test_only_the_subject_repository_on_github_binds(self) -> None:
        for url in ("https://github.com/seanchatmangpt/chatman-ecosystem.git", "https://github.com/seanchatmangpt/chatman-ecosystem",
                    "git@github.com:seanchatmangpt/chatman-ecosystem.git", "ssh://git@github.com/seanchatmangpt/chatman-ecosystem.git",
                    "https://x-access-token@github.com/seanchatmangpt/chatman-ecosystem.git"):
            self.assertEqual(court.github_slug(url), "seanchatmangpt/chatman-ecosystem", url)
        for url in ("https://gitlab.com/seanchatmangpt/chatman-ecosystem.git", "/Users/sac/chatman-ecosystem",
                    "https://github.com/seanchatmangpt/chatman-ecosystem.git/extra", "file:///tmp/github.git"):
            self.assertNotEqual(court.github_slug(url), "seanchatmangpt/chatman-ecosystem", url)


class ClauseCase(Scratch):
    def test_preserved_world_is_alive_and_publication_pending_is_no_edge(self) -> None:
        work, gh, pins = self.world()
        j = self.judge(work, pins, gh)
        self.assertEqual((j.verdict(), j.refused, j.unknown), ("ALIVE", [], []))
        line = [x["text"] for x in j.lines if x["clause"] == "I4"][0]
        self.assertIn("publication pending", line)

    def test_a_clone_without_the_archive_is_unknown_never_alive_never_refused(self) -> None:
        work, gh, pins = self.world(archive=False)
        j = self.judge(work, pins, gh)
        self.assertEqual(j.refused, [])
        self.assertEqual(sorted(set(j.unknown)), ["LINEAGE_EVIDENCE_ABSENT", "SHADOW_EVIDENCE_ABSENT"])

    def test_the_second_namespace_is_judged_as_strictly_as_the_first(self) -> None:
        work, gh, pins = self.world()
        second = pins["local_lineage"]["namespaces"][1]
        self.git(work, "update-ref", "-d", f"{second}side")
        self.assertIn("LINEAGE_UNPRESERVED", self.judge(work, pins, gh).refused)

    def test_every_committed_court_file_absent_is_refused(self) -> None:
        work, _, _ = self.world()
        j = court.Judge(quiet=True)
        court.c1_court_at_head(work, j)
        self.assertEqual(j.refused, ["COURT_NOT_AT_HEAD"])

    def test_the_seal_round_trips_through_its_own_receipt_clause(self) -> None:
        validator = self.validator()
        work, gh, pins = self.world()
        court.seal_world(work, self.env, pins, validator, str(gh), ROOT, self.base)
        j = self.judge(work, pins, gh, validator)
        self.assertEqual((j.verdict(), j.refused, j.unknown), ("ALIVE", [], []))
        doc = json.loads((work / pins["subject"]["receipt"]).read_text(encoding="utf-8"))
        self.assertEqual(doc["court"]["emitted_by"], court.WRAPPER)
        self.assertEqual(doc["standing"]["value"], "ALIVE")
        self.assertTrue(all(c["exit"] == 0 for c in doc["replay"]["commands"][1:]), doc["replay"]["commands"])
        self.assertEqual(doc["lineage"]["relation_to_subject"], {"main": "unrelated", "side": "unrelated"})
        # a sealed claim that no longer holds at its subject is refused: the shadow's unpublished int repointed
        sc = pins["shadow_clone"]
        self.git(work, "update-ref", f"{sc['prefix']}heads/release/v26.9.23-int", pins["subject"]["base_commit"])
        refused = self.judge(work, pins, gh, validator).refused
        self.assertIn("SHADOW_LINEAGE_UNPRESERVED", refused)
        self.assertIn("RECEIPT_CLAIM_MISMATCH", refused)


class ReceiptCase(Scratch):
    """R1 judges every receipt at HEAD but the pinned pre-court blob (the skeptic's r1_probe forgeries)."""

    SKIP = {"path": None, "finding": ("SKIP", "", "no validation in this case")}

    def sealed(self) -> tuple[Path, Path, dict]:
        work, gh, pins = self.world()
        court.seal_world(work, self.env, pins, self.SKIP, str(gh), ROOT, self.base)
        return work, gh, pins

    def forge(self, work: Path, pins: dict, fn) -> None:
        court.edit_json(work / pins["subject"]["receipt"], fn)
        self.git(work, "commit", "-q", "-am", "forged receipt")

    def test_only_the_pinned_pre_court_receipt_is_exempt(self) -> None:
        work, gh, pins = self.world()
        j = self.judge(work, pins, gh)
        self.assertEqual((j.verdict(), j.refused), ("ALIVE", []))
        self.assertIn("pinned pre-court receipt", [x["text"] for x in j.lines if x["clause"] == "R1"][0])
        unpinned = dict(pins, receipt_history={"superseded_blobs": []})
        self.assertEqual(self.judge(work, unpinned, gh).refused, ["RECEIPT_NOT_COURT_EMITTED"])

    def test_a_rewritten_marker_or_deleted_court_block_never_switches_r1_off(self) -> None:
        l1 = None
        for label, fn in (("marker", lambda d: (d["lineage"]["relation_to_base"].update({"main": "descendant"}),
                                                d["court"].update({"emitted_by": "hand"}))),
                          ("court block", lambda d: (d["lineage"]["relation_to_base"].update({"main": "descendant"}), d.pop("court"))),
                          ("subject", lambda d: (d["identity"].update({"subject_sha": l1}), d["court"].update({"emitted_by": "hand"})))):
            with self.subTest(label):
                self.base = Path(tempfile.mkdtemp(prefix=f"f-{label[:6]}.", dir=self.tmp.name))
                work, gh, pins = self.sealed()
                l1 = pins["local_lineage"]["heads"]["main"]
                self.assertEqual(self.judge(work, pins, gh).verdict(), "ALIVE")
                self.forge(work, pins, fn)
                j = self.judge(work, pins, gh)
                self.assertEqual((j.verdict(), j.refused), ("REFUSED", ["RECEIPT_NOT_COURT_EMITTED"]), j.lines)

    def test_the_court_digest_is_the_court_at_the_subject(self) -> None:
        work, gh, pins = self.sealed()
        key = f"{court.SDIR}/courts/ce23_0/court.py"
        self.forge(work, pins, lambda d: d["court"]["loaded_sha256"].update({key: "0" * 64}))
        self.assertEqual(self.judge(work, pins, gh).refused, ["RECEIPT_COURT_MISMATCH"])

    def test_standing_is_derived_from_the_recorded_run(self) -> None:
        work, gh, pins = self.sealed()
        doc = json.loads((work / pins["subject"]["receipt"]).read_text(encoding="utf-8"))
        subject = doc["identity"]["subject_sha"]
        self.assertEqual(court.standing_underived(doc, pins, subject), [])
        blocked = json.loads(json.dumps(doc))
        blocked["standing"]["value"] = "BLOCKED"
        self.assertTrue(court.standing_underived(blocked, pins, subject))
        touched = json.loads(json.dumps(doc))
        touched["predecessor"]["tree_at_subject"] = "0" * 40
        self.assertEqual(len(court.standing_underived(touched, pins, subject)), 1)
        related = json.loads(json.dumps(doc))
        related["lineage"]["relation_to_subject"]["main"] = "ancestor"
        self.assertEqual(len(court.standing_underived(related, pins, subject)), 1)
        self.forge(work, pins, lambda d: d["court"]["clauses"].append({"verdict": "REFUSED", "clause": "P1", "code": "X", "text": "t"}))
        self.assertEqual(self.judge(work, pins, gh).refused, ["RECEIPT_STANDING_UNDERIVED"])

    def test_the_superseded_record_is_recomputed_at_the_subject(self) -> None:
        work, gh, pins = self.sealed()
        doc = json.loads((work / pins["subject"]["receipt"]).read_text(encoding="utf-8"))
        self.assertEqual(doc["supersedes"]["blob"], pins["receipt_history"]["superseded_blobs"][0])
        self.forge(work, pins, lambda d: d["supersedes"].update({"blob": "0" * 40}))
        self.assertEqual(self.judge(work, pins, gh).refused, ["RECEIPT_CLAIM_MISMATCH"])


class OrderCase(Scratch):
    """O1 reads the goal and the compiled orders from HEAD's tree, never the working tree."""

    def test_an_untracked_orders_file_links_nothing(self) -> None:
        real = court.Git(ROOT, court.caller_env())
        law = self.base / "law"
        self.git(self.base, "init", "-q", "-b", "main", str(law))
        goal = f"{court.SDIR}/{court.SUBJ['goal']}"
        orders = f"{court.SDIR}/sjira/compiled/chatman-ce23/orders.ttl"
        for rel in (goal, orders):
            (law / rel).parent.mkdir(parents=True, exist_ok=True)
            (law / rel).write_bytes(real.blob(f"HEAD:{rel}") or b"")
        self.git(law, "add", "--", goal)
        self.git(law, "commit", "-q", "-m", "goal only; orders untracked")
        j = court.Judge(quiet=True)
        self.assertEqual(court.o1_orders(law, court.PINS, self.env, j), [])
        self.assertEqual(j.refused, ["ORDER_UNLINKED"])
        self.git(law, "add", "--", orders)
        self.git(law, "commit", "-q", "-m", "orders committed")
        j = court.Judge(quiet=True)
        linked = court.o1_orders(law, court.PINS, self.env, j)
        self.assertEqual(j.refused, [])
        self.assertTrue(linked and all(f"({orders}; subject " in o for o in linked), linked)
        self.assertEqual(linked, [o for o in court.o1_orders(ROOT, court.PINS, self.env, court.Judge(quiet=True)) if orders in o])


class SubjectCase(unittest.TestCase):
    """The committed receipt of this checkout, judged by R1 without the network (no live observation)."""

    def test_receipt_history_after_the_first_seal_is_court_emitted(self) -> None:
        g = court.Git(ROOT, court.caller_env())
        rel = court.SUBJ["receipt"]
        pinned = court.PINS["receipt_history"]["superseded_blobs"]
        commits = g.out("log", "--format=%H", "--reverse", "HEAD", "--", rel).split()
        self.assertTrue(commits, "no CE23-0 receipt in HEAD's history")
        sealed = False
        for c in commits:
            record, doc = court.receipt_record(g, rel, c)
            if record is None:
                continue
            if record.get("emitted_by_this_court"):
                sealed = True
                continue
            self.assertFalse(sealed, f"{c[:12]}: a receipt this court did not emit follows the court's first seal")
            self.assertIn(record["blob"], pinned, f"{c[:12]}: an unpinned receipt this court did not emit")

    def test_committed_receipt_is_court_emitted_and_replays(self) -> None:
        g = court.Git(ROOT, court.caller_env())
        record, doc = court.receipt_record(g, court.SUBJ["receipt"], "HEAD")
        self.assertIsNotNone(record, "no committed CE23-0 receipt")
        if record["blob"] in court.PINS["receipt_history"]["superseded_blobs"]:
            self.skipTest("the committed CE23-0 receipt is the pinned pre-court receipt (identity.toml [receipt_history])")
        self.assertTrue(record["emitted_by_this_court"], f"the committed receipt {record} was not emitted by this court")
        text = (g.blob(f"HEAD:{court.SUBJ['receipt']}") or b"").decode("utf-8")
        self.assertIsNone(SHADOW_PATH.search(text), "the sealed receipt names a retired shadow path")
        with tempfile.TemporaryDirectory(prefix="ce23-0-subject.") as tmp:
            path, findings = court.validator_for(Path(tmp))
            validator = ({"path": path, "finding": findings[0]} if path is not None and findings[0][0] == "OK" else
                         {"path": None, "finding": ("SKIP", "", f"pinned receipt validator not admitted here: {findings}")})
            j = court.Judge(quiet=True)
            court.r1_receipt(g, court.PINS, g.out("rev-parse", "HEAD"), None, Path(tmp), validator, j)
        self.assertEqual((j.refused, j.unknown), ([], []), j.lines)
        self.assertTrue(any("every recorded claim equals the recomputation" in x["text"] for x in j.lines), j.lines)

    def test_committed_identity_fact_names_no_shadow_path(self) -> None:
        data = court.Git(ROOT, court.caller_env()).blob(f"HEAD:{court.SUBJ['identity']}")
        if data is None:
            self.skipTest("no committed CE23-0 identity fact")
        self.assertIsNone(SHADOW_PATH.search(data.decode("utf-8")))
        self.assertIn('er:observedSha "', data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
