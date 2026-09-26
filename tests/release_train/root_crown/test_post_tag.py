"""POST_TAG crown: history is replayed, the head is attested, the tag is immutable.

Fixture: the committed release tree + docs/jira/v26.9.25 + the committed hardening dir,
evaluated at a post-tag head (``c`` * 40) with the real tag-time observations. Every
post-tag refusal has a refusing mutant; the defect this closes (every post-tag commit
REFUSED CROWN_SHA_SPLIT/TAG_SHA_SPLIT) is reproduced in PRE_TAG on the same inputs.
"""

from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

from _support import REPO, RELEASE, committed_tree

from scripts.release_train.root_crown import crown, evidence, posttag
from scripts.release_train.root_crown.model import POST_TAG_BLOCKERS, POST_TAG_RULES, code_of

HARDENING = REPO / "release" / RELEASE / "hardening"
SUBJECT = Path(os.environ.get("ROOT_CROWN_SUBJECT_TREE", "/nonexistent-subject"))
HAVE_SUBJECT = (SUBJECT / "scripts").is_dir()
HEAD = "c" * 40
TAG_OBJECT = "337e839937c247de4ee58b744c8b8e43950d18e3"
TAG_COMMIT = "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"


# Evidence binding (PR-4): the tag-time producer receipts were read at container heads that
# add non-receipt paths (observed in hardening/inputs/delta-observations.json), so their
# standing is not inherited: typed BLOCKED EVIDENCE_DELTA_UNBOUNDED; affidavit's delta is
# receipt-only and stays PASS.
UNBOUNDED_IDS = {
    "AC-03", "AC-04", "AC-07", "AC-13", "AC-14", "AC-15", "AC-16",
    "F-01", "F-02", "F-08", "F-09", "F-12", "F-13",
}  # fmt: skip


def local_tag(**fields):
    return {
        "name": RELEASE,
        "sha": TAG_COMMIT,
        "object_sha": TAG_OBJECT,
        "object_type": "tag",
        "source": "local-git",
    } | fields


@unittest.skipUnless((HARDENING / "TAG-SUBJECT.json").is_file(), "hardening/TAG-SUBJECT.json not committed")
class PostTagTest(unittest.TestCase):
    def setUp(self):
        self.tree = committed_tree()
        shutil.copytree(REPO / "docs/jira" / RELEASE, self.tree.root / "docs/jira" / RELEASE)
        shutil.copytree(HARDENING, self.tree.release_dir / "hardening")
        self.hardening = self.tree.release_dir / "hardening"
        self.obs = json.loads((HARDENING / "receipts/run-36161856985/observations.json").read_text())
        self.obs["tag"] = {"name": RELEASE, "sha": TAG_COMMIT, "object_sha": TAG_OBJECT, "object_type": "tag"}

    def tearDown(self):
        self.tree.cleanup()

    def attest(self, obs=None, mode="auto", subject=SUBJECT if HAVE_SUBJECT else None, tag=None, ancestry=None):
        return crown.attest(
            self.tree.release_dir,
            self.obs if obs is None else obs,
            None,
            HEAD,
            root=self.tree.root,
            requested_mode=mode,
            head_sha=HEAD,
            subject_dir=subject,
            tag_observation=local_tag() if tag is None else tag,
            ancestry={TAG_COMMIT, HEAD} if ancestry is None else ancestry,
        )

    def codes(self, verdict):
        return {code_of(r) for r in verdict.refusals}

    def record(self):
        return posttag.load_record(self.hardening)

    # --- the defect and its fix -------------------------------------------------------------
    def test_pre_tag_semantics_refuse_every_post_tag_commit(self):
        verdict = self.attest(mode="PRE_TAG")
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertTrue({"CROWN_SHA_SPLIT", "TAG_SHA_SPLIT"} <= self.codes(verdict))

    def test_post_tag_head_is_attested_not_refused(self):
        verdict = self.attest()
        receipt = verdict.receipt
        self.assertEqual(receipt["mode"], "POST_TAG")
        self.assertEqual(receipt["refusals"], [])
        core = receipt["current"]["core"]
        self.assertEqual(receipt["current"]["standing"], "BLOCKED", core["remaining"])
        unbounded = {r["id"] for r in core["remaining"] if r["code"] == "EVIDENCE_DELTA_UNBOUNDED"}
        self.assertEqual(unbounded, UNBOUNDED_IDS)
        self.assertEqual({r["id"] for r in core["remaining"]} - unbounded, {"AC-18"})
        self.assertEqual(core["requirements"]["AC-08"]["binding"]["lineage_proof"]["delta_class"], "RECEIPT_ONLY")
        self.assertEqual(core["requirements"]["AC-19"]["state"], "PASS")
        self.assertEqual(core["requirements"]["AC-19"]["binding"]["kind"], "IN_TREE_DERIVED")
        self.assertEqual(receipt["subject"], {
            "tag": RELEASE, "tag_object_sha": TAG_OBJECT, "commit_sha": TAG_COMMIT,
            "tree_sha": "8553eb9ea7ab45227169eec1f57204f2ff12ad53",
        })  # fmt: skip
        self.assertEqual((receipt["attestation_head_sha"], receipt["crown_sha"]), (HEAD, TAG_COMMIT))
        self.assertEqual(
            receipt["previous_receipt_digest"],
            "sha256:7e7e9c80c3cd4649d9e00039d2336c8b5ff477b53227332dd4b445de3c2cc856",
        )
        self.assertTrue(crown.verify_receipt(receipt))
        if HAVE_SUBJECT:
            self.assertEqual(verdict.standing, "BLOCKED")
            self.assertTrue(receipt["historical"]["replay"]["exact"])
            self.assertEqual(receipt["historical"]["standing"], "ALIVE")
            self.assertEqual(receipt["historical"]["standing_ceiling"], "BLOCKED")
        else:
            self.assertEqual(verdict.standing, "BLOCKED")
            self.assertIn("SUBJECT_ABSENT", {b["code"] for b in receipt["blockers"]})

    def test_without_delta_observations_inheritance_is_refused(self):
        """No lineage proof -> every producer receipt read at a descendant head is REFUSED."""
        (self.hardening / posttag.DELTA_OBSERVATIONS).unlink()
        verdict = self.attest()
        missing = {r.split(":")[2] for r in verdict.receipt["current"]["refusals"] if "EVIDENCE_LINEAGE_MISSING" in r}
        self.assertEqual(missing, UNBOUNDED_IDS | {"AC-08", "F-05"})

    def test_subject_absent_is_typed_blocked(self):
        verdict = self.attest(subject=None)
        self.assertEqual(verdict.standing, "BLOCKED")
        self.assertEqual(verdict.receipt["historical"]["replay_standing"], posttag.HISTORICAL_DIVERGED)
        self.assertIn("SUBJECT_ABSENT", {b["code"] for b in verdict.receipt["blockers"]})

    # --- mode selection ----------------------------------------------------------------------
    def test_select_mode_is_keyed_on_the_record(self):
        record = self.record()
        tags = [local_tag()]
        self.assertEqual(posttag.select_mode("auto", record, tags, HEAD), ("POST_TAG", []))
        self.assertEqual(posttag.select_mode("auto", None, tags, HEAD), ("PRE_TAG", []))
        self.assertEqual(posttag.select_mode("PRE_TAG", record, tags, HEAD), ("PRE_TAG", []))
        mode, blockers = posttag.select_mode("POST_TAG", None, tags, HEAD)
        self.assertEqual(mode, "POST_TAG")
        self.assertEqual([code_of(b) for b in blockers], ["TAG_UNRECORDED"])

    # --- one refusing mutant per post-tag rule ----------------------------------------------
    def m_tag_object_digest(self):
        raw = self.hardening / f"inputs/objects/{TAG_COMMIT}.commit.raw"
        body = bytearray(raw.read_bytes())
        body[0:4] = b"TREE"
        raw.write_bytes(bytes(body))
        return self.codes(self.attest())

    def m_tag_mutated(self):
        return self.codes(self.attest(tag=local_tag(object_sha="e" * 40)))

    def m_tag_deleted(self):
        obs = dict(self.obs, tag={"name": RELEASE, "sha": None})
        return self.codes(self.attest(obs=obs))

    def m_tag_subject_split(self):
        return self.codes(self.attest(tag=local_tag(sha="d" * 40)))

    def m_tag_receipt_split(self):
        path = self.hardening / "TAG-SUBJECT.json"
        record = json.loads(path.read_text())
        record["tag_receipt"]["receipt_digest"] = "sha256:" + "0" * 64
        path.write_text(json.dumps(record))
        return self.codes(self.attest())

    def m_subject_tree(self):
        subject = self.tree.root / "subject"
        shutil.copytree(
            REPO / "release" / RELEASE, subject / "release" / RELEASE, ignore=shutil.ignore_patterns("hardening")
        )
        clean = {code_of(r) + ":" + r.split(":")[2] for r in posttag.verify_subject_tree(subject, self.record())}
        self.assertNotIn(f"SUBJECT_TREE_MISMATCH:release/{RELEASE}", clean)
        pins = subject / "release" / RELEASE / "pins.json"
        pins.write_bytes(pins.read_bytes() + b" ")
        return {code_of(r) + ":" + r.split(":")[2] for r in posttag.verify_subject_tree(subject, self.record())}

    def m_historical_observation_split(self):
        path = self.hardening / "receipts/run-36161744816/observations.json"
        obs = json.loads(path.read_text())
        obs["observed_at"] = "2026-09-25T16:36:09Z"  # a fresher substitute for the historical observation
        path.write_text(json.dumps(obs))
        historical = posttag.historical_standing(self.record(), self.hardening, None, self.tree.root)
        self.assertEqual(historical["standing"], "REFUSED")
        return {code_of(r) for r in historical["refusals"]}

    def m_payload_mutated(self):
        allow = self.tree.release_dir / "worktrees-allow.json"
        allow.write_bytes(allow.read_bytes() + b"\n")
        return self.codes(self.attest())

    def test_one_refusing_mutant_per_post_tag_rule(self):
        table = {
            "TAG_OBJECT_DIGEST_MISMATCH": (self.m_tag_object_digest, "TAG_OBJECT_DIGEST_MISMATCH"),
            "TAG_MUTATED": (self.m_tag_mutated, "TAG_MUTATED"),
            "TAG_SUBJECT_SPLIT": (self.m_tag_subject_split, "TAG_SUBJECT_SPLIT"),
            "TAG_RECEIPT_SPLIT": (self.m_tag_receipt_split, "TAG_RECEIPT_SPLIT"),
            "SUBJECT_TREE_MISMATCH": (self.m_subject_tree, f"SUBJECT_TREE_MISMATCH:release/{RELEASE}"),
            "HISTORICAL_OBSERVATION_SPLIT": (self.m_historical_observation_split, "HISTORICAL_OBSERVATION_SPLIT"),
            "PAYLOAD_MUTATED_POST_TAG": (self.m_payload_mutated, "PAYLOAD_MUTATED_POST_TAG"),
        }
        self.assertEqual(set(table), set(POST_TAG_RULES))
        for rule, (mutant, expected) in table.items():
            with self.subTest(rule=rule):
                self.tearDown()
                self.setUp()
                self.assertIn(expected, mutant())

    def test_verify_tag_subject_refuses_each_observation_breach_independently(self):
        record = self.record()

        def codes(tag):
            refusals, _ = posttag.verify_tag_subject(record, self.hardening, [tag])
            return {code_of(r) for r in refusals}

        self.assertEqual(codes(local_tag()), set())
        self.assertEqual(codes(local_tag(object_sha="e" * 40)), {"TAG_MUTATED"})
        self.assertEqual(codes(local_tag(sha="d" * 40)), {"TAG_SUBJECT_SPLIT"})
        self.assertEqual(codes(local_tag(sha=None)), {"TAG_MUTATED"})
        _, blockers = posttag.verify_tag_subject(record, self.hardening, [local_tag(object_sha=None)])
        self.assertEqual([code_of(b) for b in blockers], ["OBSERVATION_MISSING"])

    def test_post_tag_binding_requirement_refuses_on_its_own(self):
        """AC-19 / F-13 (tag_binding) in the current evaluation, independent of the subject section."""
        record = self.record()
        tag_reqs = [r for r in self.tree.inputs().requirements if r.evidence_kind == "tag_binding"]
        self.assertTrue(tag_reqs)
        table = {
            "PASS": [local_tag()],
            "TAG_MUTATED": [local_tag(object_sha="e" * 40)],
            "TAG_SUBJECT_SPLIT": [local_tag(sha="d" * 40)],
            "OBSERVATION_MISSING": [],
        }
        for expected, tags in table.items():
            with self.subTest(expected=expected):
                ctx = evidence.Context(
                    root=self.tree.root,
                    release_dir=self.tree.release_dir,
                    observations=self.obs,
                    crown_sha=HEAD,
                    inputs=self.tree.inputs(),
                )
                state = posttag.tag_binding_post(record, tags)(tag_reqs[0], None if expected != "PASS" else ctx)
                self.assertEqual(state.state if expected == "PASS" else state.code, expected)
                if expected == "PASS":
                    self.assertEqual(state.binding.kind, "IN_TREE_DERIVED")
        self.assertEqual(posttag.tag_binding_post(None, [local_tag()])(tag_reqs[0], None).code, "TAG_UNRECORDED")

    def test_deleted_tag_is_tag_mutated(self):
        self.assertIn("TAG_MUTATED", self.m_tag_deleted())

    def test_post_tag_blockers_are_all_emitted_somewhere(self):
        emitted = {"TAG_UNRECORDED", "REPLAY_DIVERGED", "SUBJECT_ABSENT"}  # test_cli, test_replay, above
        emitted.add(code_of(self.m_current_head_unattested()["current"]["blockers"][0]))
        self.assertEqual(emitted, set(POST_TAG_BLOCKERS))

    # --- current conformance: the observed root head must be the attested head ---------------
    def m_current_head_unattested(self):
        obs = json.loads(json.dumps(self.obs))
        obs["repos"]["seanchatmangpt/chatman-ecosystem"]["head_sha"] = "b" * 40
        return self.attest(obs=obs).receipt

    def test_current_head_unattested_is_a_typed_current_blocker(self):
        receipt = self.m_current_head_unattested()
        current = receipt["current"]
        self.assertFalse(current["drift"]["root_observed_head_is_attested"])
        self.assertEqual([code_of(b) for b in current["blockers"]], ["CURRENT_HEAD_UNATTESTED"])
        self.assertIn(f"observed head {'b' * 40} is not the attested head {HEAD}", current["blockers"][0])
        self.assertEqual(current["standing"], "BLOCKED")
        typed = {b["code"]: b for b in receipt["blockers"]}["CURRENT_HEAD_UNATTESTED"]
        self.assertEqual((typed["failure_class"], typed["broken_term"]), ("SUBJECT_FAILURE", "R_missing_identity"))
        self.assertIn("POST_TAG:CURRENT_HEAD_UNATTESTED", {r["id"] for r in receipt["remaining"]})
        self.assertEqual(receipt["refusals"], [], "an unattested head is never a refusal")
        self.assertTrue(crown.verify_receipt(receipt))

    def test_current_head_unattested_never_touches_history(self):
        attested = json.loads(json.dumps(self.obs))
        attested["repos"]["seanchatmangpt/chatman-ecosystem"]["head_sha"] = HEAD
        clean = self.attest(obs=attested).receipt
        self.assertTrue(clean["current"]["drift"]["root_observed_head_is_attested"])
        self.assertEqual(clean["current"]["blockers"], [])
        self.assertNotIn("CURRENT_HEAD_UNATTESTED", {b["code"] for b in clean["blockers"]})
        split = self.m_current_head_unattested()
        self.assertEqual(split["historical"], clean["historical"])

    def test_unattested_head_blocks_an_otherwise_alive_current_section(self):
        """With every evaluator a real PASS (a simple in-tree evaluator, not a patch), the
        current section is ALIVE exactly when the observed root head is the attested head."""
        registry = {k: (lambda req, ctx: evidence.in_tree_pass(req, ctx, "forced PASS", "test")) for k in evidence.EVALUATORS}
        record = self.record()
        tags = [local_tag()]

        def current(observed):
            obs = json.loads(json.dumps(self.obs))
            obs["repos"]["seanchatmangpt/chatman-ecosystem"]["head_sha"] = observed
            return posttag.current_conformance(
                self.tree.release_dir, obs, None, HEAD, record, tags,
                root=self.tree.root, evaluators=registry, hardening_dir=self.hardening,
            )  # fmt: skip

        attested = current(HEAD)
        self.assertEqual((attested["standing"], attested["refusals"], attested["blockers"]), ("ALIVE", [], []))
        split = current("b" * 40)
        self.assertEqual(split["standing"], "BLOCKED")
        self.assertEqual([code_of(b) for b in split["blockers"]], ["CURRENT_HEAD_UNATTESTED"])
        self.assertEqual(split["refusals"], [])

    def test_unobserved_root_head_is_not_an_unattested_head(self):
        obs = json.loads(json.dumps(self.obs))
        obs["repos"]["seanchatmangpt/chatman-ecosystem"].pop("head_sha", None)
        current = self.attest(obs=obs).receipt["current"]
        self.assertIsNone(current["drift"]["root_observed_head_is_attested"])
        self.assertNotIn("CURRENT_HEAD_UNATTESTED", {code_of(b) for b in current["blockers"]})

    # --- verify_tag_subject: each recompute clause refuses on its own --------------------------
    def tampered_record_codes(self, section, mutate_fn):
        record = json.loads(json.dumps(self.record()))
        mutate_fn(record[section])
        refusals, _ = posttag.verify_tag_subject(record, self.hardening, [local_tag()])
        return refusals

    def test_each_recomputed_section_refuses_independently(self):
        table = {
            "tag": ("TAG_MUTATED", lambda v: v.update(tagger="forged <f@example.invalid> 0 +0000")),
            "subject": ("TAG_SUBJECT_SPLIT", lambda v: v.update(tree_sha="d" * 40)),
            "payload": ("TAG_SUBJECT_SPLIT", lambda v: v.update(tree_sha="d" * 40)),
            "tag_receipt": ("TAG_RECEIPT_SPLIT", lambda v: v.update(observations_digest="sha256:" + "0" * 64)),
            "raw_objects": ("TAG_OBJECT_DIGEST_MISMATCH", lambda v: v.update({"f" * 40: "inputs/objects/forged.raw"})),
        }
        self.assertEqual(posttag.verify_tag_subject(self.record(), self.hardening, [local_tag()])[0], [])
        for section, (code, fn) in table.items():
            with self.subTest(section=section):
                self.assertEqual(
                    self.tampered_record_codes(section, fn),
                    [f"REFUSED:{code}:TAG-SUBJECT.json {section} does not recompute from raw objects"],
                )

    def rewrite_tag_receipt(self, **fields):
        record = self.record()
        path = self.hardening / record["tag_receipt"]["path"]
        receipt = json.loads(path.read_text())
        receipt.update(fields)
        path.write_text(json.dumps(receipt))
        refusals, _ = posttag.verify_tag_subject(record, self.hardening, [local_tag()])
        return refusals

    def test_tag_receipt_self_digest_must_recompute(self):
        refusals = self.rewrite_tag_receipt(evaluated_at="2099-01-01T00:00:00Z")
        self.assertIn("does not recompute to the tag message digest", " ".join(refusals))

    def test_tag_receipt_must_name_the_tag_target_alive(self):
        for field, value in (("crown_sha", "d" * 40), ("standing", "BLOCKED")):
            with self.subTest(field=field):
                self.tearDown()
                self.setUp()
                from scripts.release_train.root_crown.crown import receipt_digest_of

                record = self.record()
                path = self.hardening / record["tag_receipt"]["path"]
                receipt = json.loads(path.read_text())
                receipt[field] = value
                receipt["receipt_digest"] = record["tag"]["message_receipt_digest"]  # keep the lookup key
                path.write_text(json.dumps(receipt))
                refusals, _ = posttag.verify_tag_subject(record, self.hardening, [local_tag()])
                want = f"crown_sha={value}" if field == "crown_sha" else f"standing={value}"
                self.assertTrue(
                    any(r.startswith("REFUSED:TAG_RECEIPT_SPLIT:tag receipt crown_sha=") and want in r for r in refusals),
                    refusals,
                )
                self.assertNotEqual(receipt_digest_of(receipt), receipt["receipt_digest"])

    def test_payload_mutation_never_refuses_history(self):
        self.m_payload_mutated()
        verdict = self.attest()
        self.assertEqual(verdict.receipt["current"]["standing"], "REFUSED")
        self.assertNotEqual(verdict.receipt["historical"]["standing"], "REFUSED")
        self.assertEqual(verdict.receipt["historical"]["refusals"], [])

    def test_drift_is_reported(self):
        obs = json.loads(json.dumps(self.obs))
        repo = "seanchatmangpt/chatman-ecosystem"
        obs["repos"][repo]["head_sha"] = HEAD
        verdict = self.attest(obs=obs)
        drift = verdict.receipt["current"]["drift"]
        self.assertIn(repo, drift["moved_since_tag"])
        self.assertTrue(drift["root_observed_head_is_attested"])


if __name__ == "__main__":
    unittest.main()
