"""hardening.py: TAG-SUBJECT.json, receipts/chain.json, replay-receipt.json and the final
(PR-5) outputs are deterministic projections of committed bytes (+ the materialized tag subject).

Chicago style: the real projector over the committed hardening inputs, the real release
closure court over the projected closure-final.json with a real evidence root laid out from
committed bytes; no collaborator is replaced."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import REPO, RELEASE

from scripts.release_train.release_closure_court import court as closure_court
from scripts.release_train.root_crown import chain, final, hardening

HARDENING = REPO / "release" / RELEASE / "hardening"
SUBJECT = Path(os.environ.get("ROOT_CROWN_SUBJECT_TREE", "/nonexistent-subject"))
REPOSITORY = "seanchatmangpt/chatman-ecosystem"


def dump(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


@unittest.skipUnless((HARDENING / hardening.TAG_SUBJECT).is_file(), "hardening projection not committed")
class HardeningProjectionTest(unittest.TestCase):
    def test_committed_tag_subject_and_chain_are_current_and_deterministic(self):
        first = dump(hardening.project_tag_subject(HARDENING, RELEASE, REPOSITORY))
        second = dump(hardening.project_tag_subject(HARDENING, RELEASE, REPOSITORY))
        self.assertEqual(first, second)
        self.assertEqual((HARDENING / hardening.TAG_SUBJECT).read_bytes(), first)
        self.assertEqual((HARDENING / chain.CHAIN_FILE).read_bytes(), dump(chain.project(HARDENING, RELEASE)))
        record = json.loads(first)
        self.assertEqual(record["GENERATED"], hardening.GENERATED)
        self.assertEqual(record["tag"]["object_sha"], "337e839937c247de4ee58b744c8b8e43950d18e3")
        self.assertEqual(record["payload"]["tree_sha"], "a01b914de2e4b3503dc2126ce233654af764c362")

    def test_projection_carries_no_machine_local_path(self):
        for name in (hardening.TAG_SUBJECT, chain.CHAIN_FILE, hardening.REPLAY_RECEIPT):
            text = (HARDENING / name).read_text()
            with self.subTest(name=name):
                for marker in ("/Users/", "/tmp/", "/private/", "~/", "/home/"):
                    self.assertNotIn(marker, text)

    def test_check_refuses_a_hand_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "hardening"
            shutil.copytree(HARDENING, copy)
            rendered = {
                hardening.TAG_SUBJECT: dump(hardening.project_tag_subject(copy, RELEASE, REPOSITORY)),
                chain.CHAIN_FILE: dump(chain.project(copy, RELEASE)),
            }
            self.assertEqual(hardening.check(copy, rendered), [])
            path = copy / hardening.TAG_SUBJECT
            path.write_text(path.read_text().replace('"approval_run": "36161744816"', '"approval_run": "1"'))
            drift = hardening.check(copy, rendered)
        self.assertEqual(len(drift), 1)
        self.assertTrue(drift[0].startswith("REFUSED:PROJECTION_DRIFT:") and drift[0].endswith(hardening.TAG_SUBJECT))

    def test_two_tag_objects_for_one_release_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "hardening"
            shutil.copytree(HARDENING, copy)
            from scripts.release_train.root_crown import gitobj

            body = (copy / hardening.OBJECTS / "337e839937c247de4ee58b744c8b8e43950d18e3.tag.raw").read_bytes()
            other = body.replace(b"approval run", b"approval  run")
            (copy / hardening.OBJECTS / f"{gitobj.object_sha('tag', other)}.tag.raw").write_bytes(other)
            with self.assertRaises(hardening.HardeningError) as ctx:
                hardening.project_tag_subject(copy, RELEASE, REPOSITORY)
        self.assertIn("TAG_UNRECORDED", str(ctx.exception))

    @unittest.skipUnless(
        (SUBJECT / "scripts").is_dir(), "ROOT_CROWN_SUBJECT_TREE (git archive of 68bacd8d) not provided"
    )
    def test_replay_receipt_is_current(self):
        rendered = hardening.outputs(HARDENING, RELEASE, REPOSITORY, SUBJECT, REPO)
        self.assertEqual(hardening.check(HARDENING, rendered), [])
        replay = json.loads(rendered[hardening.REPLAY_RECEIPT])
        self.assertTrue(replay["historical"]["replay"]["exact"])
        self.assertEqual(replay["historical"]["replay_standing"], "HISTORICAL_RELEASE_REPLAY_EXACT")


MATRIX_FIELDS = {
    "id", "term", "owner_repo", "required_state", "observed_state", "subject_sha", "evidence_digest",
    "evidence_container", "command", "exit", "falsifier", "authority", "standing", "standing_ceiling",
}
MACHINE = ("/Users/", "/tmp/", "/private/", "~/", "/home/")
E1 = "c599667a84ec79d832bb779bce1730b33b43fdd4"
TAG_COMMIT = "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"
E3 = json.loads((HARDENING / "inputs" / "final-lanes.json").read_text())["containers"]["e3"]["commit"] if (HARDENING / "inputs" / "final-lanes.json").is_file() else None


def stage_chatman(closure: dict, dest: Path) -> set[str]:
    """Lay the root repository's evidence-only containers out at <dest>/<owner>/<repo>/<sha>/<path>.

    Only the E1 / E3 evidence commits (whose bytes this tree never rewrites) come from the
    committed tree, and the tag commit from the materialized tag subject; any other root
    container (e.g. main's mutation report, since regenerated) stays unstaged, exactly like a
    foreign repository. The court recomputes every digest.
    """
    import re

    grammar = re.compile(r"^git:(?P<repo>[^@]+)@(?P<sha>[0-9a-f]{40}):(?P<path>\S+)$")
    staged = set()
    for row in closure["subjects"]:
        for court in row.get("courts", []):
            for field in ("evidence_locator", "log_locator", "output_locator"):
                match = grammar.fullmatch(str(court.get(field, "")))
                if match is None or match["repo"] != REPOSITORY or match["sha"] not in (E1, E3, TAG_COMMIT):
                    continue
                src = (SUBJECT if match["sha"] == TAG_COMMIT else REPO) / match["path"]
                target = dest / match["repo"] / match["sha"] / match["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, target)
                staged.add(court[field])
    return staged


@unittest.skipUnless((HARDENING / final.FINAL_LANES).is_file(), "final-lanes input not committed")
class FinalOutputsTest(unittest.TestCase):
    def load(self, name: str):
        return json.loads((HARDENING / name).read_text())

    def test_matrix_has_exactly_33_rows_with_the_contract_fields(self):
        matrix = self.load(final.MATRIX)
        self.assertEqual(len(matrix["rows"]), 33)
        self.assertEqual([r["id"] for r in matrix["rows"]], [r["id"] for r in json.loads((REPO / "release" / RELEASE / "requirements.json").read_text())["requirements"]])
        for row in matrix["rows"]:
            with self.subTest(id=row["id"]):
                self.assertEqual(set(row), MATRIX_FIELDS)
                self.assertEqual(set(row["observed_state"]), {"historical", "hardened", "current"})
                self.assertTrue(row["evidence_container"].startswith("git:"))
                ok = all(v == "PASS" for k, v in row["observed_state"].items() if k != "historical")
                self.assertEqual(row["standing"] == "ALIVE", ok)
                if not ok:
                    self.assertRegex(row["standing"], r"^BLOCKED\(.+;(R_[a-z_]+|mu_[a-zA-Z_]+|admission_vacuous);[A-Z_]+_FAILURE\)$")

    def test_closure_final_carries_the_final_dispositions(self):
        closure = self.load(final.CLOSURE_FINAL)
        self.assertEqual(closure["evidence_profile"], "durable/v1")
        rows = {r["subject_id"]: r for r in closure["subjects"]}
        rfc = rows["RFC-0004"]
        self.assertEqual((rfc["impl_standing"], rfc["successor"]["sha"]), ("SUPERSEDED", TAG_COMMIT))
        self.assertTrue(rfc["successor"]["receipt_digest"].startswith("sha256:2323f877"))
        root = rows["CHATMAN_ECOSYSTEM"]
        self.assertEqual((root["impl_standing"], root["sha"]), ("ALIVE", TAG_COMMIT))
        (court,) = root["courts"]
        self.assertEqual((court["result"], court["sha"]), ("PASS", TAG_COMMIT))
        self.assertTrue(court["evidence_locator"].startswith(f"git:{REPOSITORY}@{E1}:"))
        self.assertIn("EVIDENCE_DELTA_UNBOUNDED", rows["AUTOFDE_LAB"]["impl_type"])
        tagged = json.loads((REPO / "release" / RELEASE / "closure.json").read_text())["subjects"]
        self.assertEqual([r["subject_id"] for r in closure["subjects"][: len(tagged)]], [r["subject_id"] for r in tagged])
        post = [r for r in closure["subjects"] if r["row_origin"] == "post-tag"]
        self.assertTrue(post and all(r["subject_id"].startswith("POST-TAG:") for r in post))

    def test_new_outputs_carry_no_machine_local_path(self):
        tagged = (REPO / "release" / RELEASE / "closure.json").read_text()
        for name in final.OUTPUTS:
            text = (HARDENING / name).read_text()
            for line in text.splitlines():
                with self.subTest(name=name, line=line[:80]):
                    if any(m in line for m in MACHINE):
                        # only bytes carried verbatim from the tagged closure rows
                        self.assertEqual(name, final.CLOSURE_FINAL)
                        self.assertIn(line.strip().rstrip(",").split(": ", 1)[-1].strip('"'), tagged)

    def test_court_refuses_every_pass_without_an_evidence_root(self):
        verdict = closure_court.evaluate(self.load(final.CLOSURE_FINAL))
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertTrue(verdict.refusals)
        for refusal in verdict.refusals:
            self.assertTrue(refusal.startswith("REFUSED:EVIDENCE_NOT_DURABLE:"), refusal)

    def test_payload_freeze_holds_and_a_payload_edit_is_reported(self):
        from types import SimpleNamespace

        record = hardening.project_tag_subject(HARDENING, RELEASE, REPOSITORY)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(REPO / "release" / RELEASE, root / "release" / RELEASE, ignore=shutil.ignore_patterns("hardening"))
            ctx = SimpleNamespace(root=root, record=record)
            self.assertEqual(final.payload_freeze(ctx)["result"], "HOLDS")
            (root / "release" / RELEASE / "hardening").mkdir()
            (root / "release" / RELEASE / "hardening" / "x.json").write_text("{}")
            self.assertEqual(final.payload_freeze(ctx)["result"], "HOLDS")
            pins = root / "release" / RELEASE / "pins.json"
            pins.write_text(pins.read_text() + " ")
            frozen = final.payload_freeze(ctx)
        self.assertEqual(frozen["result"], "REFUSED:PAYLOAD_MUTATED_POST_TAG")
        self.assertNotEqual(frozen["recomputed_tree_sha"], frozen["tagged_tree_sha"])

    @unittest.skipUnless((SUBJECT / "scripts").is_dir(), "ROOT_CROWN_SUBJECT_TREE (git archive of 68bacd8d) not provided")
    def test_final_outputs_are_current_and_a_hand_edit_is_refused(self):
        rendered = hardening.outputs(HARDENING, RELEASE, REPOSITORY, SUBJECT, REPO)
        self.assertTrue(set(final.OUTPUTS) <= set(rendered))
        self.assertEqual(hardening.check(HARDENING, rendered), [])
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "hardening"
            shutil.copytree(HARDENING, copy)
            path = copy / final.SCORECARD
            path.write_text(path.read_text().replace('"UNSUPPORTED(no admitted ordering)"', '"ALIVE"'))
            drift = hardening.check(copy, rendered)
        self.assertEqual(drift, [f"REFUSED:PROJECTION_DRIFT:{(copy / final.SCORECARD).as_posix()}"])

    @unittest.skipUnless((SUBJECT / "scripts").is_dir(), "ROOT_CROWN_SUBJECT_TREE (git archive of 68bacd8d) not provided")
    def test_court_resolves_the_root_repository_evidence_and_refuses_a_flipped_byte(self):
        closure = self.load(final.CLOSURE_FINAL)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            staged = stage_chatman(closure, dest)
            self.assertTrue(staged)
            verdict = closure_court.evaluate(closure, dest)
            staged_refused = [r for r in verdict.refusals if any(loc in r for loc in staged)]
            self.assertEqual(staged_refused, [])
            for refusal in verdict.refusals:
                self.assertIn(":unresolved:git:seanchatmangpt/", refusal)
            target = next(p for p in sorted(dest.rglob("crown-receipt.json")) if E1 in p.as_posix())
            target.write_bytes(target.read_bytes() + b" ")
            flipped = closure_court.evaluate(closure, dest)
        self.assertIn("REFUSED:EVIDENCE_DIGEST_MISMATCH:CHATMAN_ECOSYSTEM:", "\n".join(flipped.refusals))


if __name__ == "__main__":
    unittest.main()
