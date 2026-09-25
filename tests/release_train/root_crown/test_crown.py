"""Root crown: ALIVE iff C∧A∧R∧X∧F∧M; one refusing mutant per crown rule; §39 class map total."""

from __future__ import annotations

import copy
import unittest

from _support import CROWN_SHA, alive_observations, alive_tree, dump, load

from scripts.release_train.root_crown import crown, evidence
from scripts.release_train.root_crown.model import (
    ALL_CODES,
    BROKEN_TERMS,
    CROWN_RULES,
    FAILURE_CLASS,
    FAILURE_CLASSES,
    PASS,
    TERMS,
    ReqState,
    code_of,
)


class CrownTest(unittest.TestCase):
    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)

    def tearDown(self):
        self.tree.cleanup()

    def run_crown(self, obs=None, previous=None, crown_sha=CROWN_SHA, evaluators=None):
        return crown.evaluate(
            self.tree.release_dir,
            self.obs if obs is None else obs,
            previous,
            crown_sha,
            root=self.tree.root,
            evaluators=evaluators,
        )

    def test_all_pass_is_alive_with_stable_digest(self):
        first, second = self.run_crown(), self.run_crown()
        self.assertEqual(first.standing, "ALIVE", first.remaining)
        self.assertEqual(first.terms, {t: "PASS" for t in TERMS})
        self.assertEqual(first.receipt["receipt_digest"], second.receipt["receipt_digest"])
        self.assertTrue(crown.verify_receipt(first.receipt))
        self.assertEqual(first.receipt["authority"], "NONE")
        self.assertIn("ManualRestatementCount=0", first.receipt["requirements"]["AC-05"]["detail"])

    def test_breaking_one_requirement_flips_exactly_its_term(self):
        reqs = self.tree.inputs().requirements
        for term in TERMS:
            target = next(r for r in reqs if r.term == term and r.evidence_kind != "crown_self")
            registry = dict(evidence.EVALUATORS)
            real = registry[target.evidence_kind]
            registry[target.evidence_kind] = (
                lambda req, ctx, real=real, rid=target.id: evidence.BLOCKED("EVIDENCE_ABSENT", "fixture")
                if req.id == rid
                else real(req, ctx)
            )
            with self.subTest(term=term, req=target.id):
                verdict = self.run_crown(evaluators=registry)
                self.assertEqual(verdict.standing, "BLOCKED")
                broken = {t for t, s in verdict.terms.items() if s != "PASS"}
                # AC-18 (crown_self) sits in C and is BLOCKED whenever anything else is open.
                self.assertEqual(broken, {term, "C"})

    def test_typed_blocked_is_lawful_untyped_is_refused(self):
        registry = dict(evidence.EVALUATORS)
        registry["manifest_valid"] = lambda req, ctx: ReqState("BLOCKED", None, "untyped")
        verdict = self.run_crown(evaluators=registry)
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("REFUSED:BLOCKED_WITHOUT_TYPE:AC-01", verdict.refusals)

    # --- evaluator mutants ---------------------------------------------------------------
    def ctx(self, obs=None):
        return evidence.Context(
            root=self.tree.root,
            release_dir=self.tree.release_dir,
            observations=self.obs if obs is None else obs,
            crown_sha=CROWN_SHA,
            inputs=self.tree.inputs(),
        )

    def req(self, rid):
        return next(r for r in self.tree.inputs().requirements if r.id == rid)

    def evaluate(self, rid, obs=None):
        req = self.req(rid)
        return evidence.EVALUATORS[req.evidence_kind](req, self.ctx(obs))

    def remote(self, rid, **json_fields):
        obs = copy.deepcopy(self.obs)
        obs["artifacts"][self.req(rid).evidence_locator]["json"].update(json_fields)
        return obs

    def mut_closure(self, fn):
        closure = load(self.tree.release_dir / "closure.json")
        fn(closure)
        dump(self.tree.release_dir / "closure.json", closure)

    def m_manifest(self):
        (self.tree.release_dir / "manifest.toml").write_text("[release]\nversion = 1\n")
        return self.evaluate("AC-01")

    def m_subject_not_terminal(self):
        self.mut_closure(lambda c: c["subjects"][1].update(impl_standing="WIP"))
        return self.evaluate("AC-02")

    def m_origin(self):
        def second_owner(c):
            row = copy.deepcopy(c["subjects"][0])
            row.update(subject_id="RFC-0004-COPY", repository="seanchatmangpt/chatman-ecosystem", artifact="docs/x.md")
            c["subjects"].append(row)

        self.mut_closure(second_owner)
        return self.evaluate("AC-03")

    def m_artifact_refused(self):
        return self.evaluate("AC-04", self.remote("AC-04", standing="REFUSED"))

    def m_artifact_split(self):
        obs = copy.deepcopy(self.obs)
        obs["artifacts"][self.req("AC-07").evidence_locator]["subject_compare"] = "diverged"
        return self.evaluate("AC-07", obs)

    def m_worktree(self):
        obs = copy.deepcopy(self.obs)
        obs["local_worktrees"]["worktrees"] = [{"repo": "zoela", "path": "/Users/sac/zoela-wt/1"}]
        return self.evaluate("AC-09", obs)

    def m_transient(self):
        pins = load(self.tree.release_dir / "pins.json")
        pins["repos"]["ggen-marketplace"]["sha"] = "76774bbaf83ec92e6e52b81ceb6a165b00de8b93"
        dump(self.tree.release_dir / "pins.json", pins)
        return self.evaluate("AC-11")

    def m_not_merged(self):
        obs = copy.deepcopy(self.obs)
        obs["repos"]["seanchatmangpt/xaas"]["compare_status"] = "diverged"
        return self.evaluate("AC-17", obs)

    def m_cold(self):
        path = self.tree.release_dir / "out/requirements.ttl"
        path.write_text(path.read_text() + "# hand edit\n")
        return self.evaluate("AC-12")

    def m_berthier(self):
        path = self.tree.release_dir / "out/packets.json"
        doc = load(path)
        doc["packets"] = doc["packets"][1:]
        dump(path, doc)
        return self.evaluate("AC-05")

    def m_xprod(self):
        path = self.tree.root / "docs/jira/v26.9.25/xprod-cases/XPROD-001.json"
        case = load(path)
        case["evidence"][0]["subject_sha"] = "9" * 40
        dump(path, case)
        return self.evaluate("AC-06")

    def m_tag(self):
        obs = copy.deepcopy(self.obs)
        obs["tag"]["sha"] = "d" * 40
        return self.evaluate("AC-19", obs)

    def m_claim(self):
        return self.evaluate("F-09", self.remote("F-09", transport_receipt=None))

    def m_chain(self):
        good = self.run_crown().receipt
        tampered = dict(good, standing="ALIVE", crown_sha="e" * 40)
        return self.run_crown(previous=tampered)

    def m_crown_split(self):
        obs = copy.deepcopy(self.obs)
        obs["repos"]["seanchatmangpt/chatman-ecosystem"]["head_sha"] = "f" * 40
        return self.run_crown(obs=obs)

    def m_untyped(self):
        registry = dict(evidence.EVALUATORS)
        registry["tag_binding"] = lambda req, ctx: ReqState("BLOCKED", None)
        return self.run_crown(evaluators=registry)

    def m_unknown_kind(self):
        registry = dict(evidence.EVALUATORS)
        del registry["xprod_case"]
        return self.run_crown(evaluators=registry)

    def m_private_digest(self):
        from test_private_observation import private_obs

        obs = private_obs(self.obs)
        receipt = obs["private_repos"]["repos"]["seanchatmangpt/zoela"]["receipts"][0]
        receipt["sha256"] = "0" * 64
        return self.run_crown(obs=obs)

    def m_private_split(self):
        from test_private_observation import private_obs

        obs = private_obs(self.obs)
        obs["private_public_compare"] = {"seanchatmangpt/zoela": "diverged"}
        return self.run_crown(obs=obs)

    def test_one_refusing_mutant_per_crown_rule(self):
        table = {
            "MANIFEST_INVALID": self.m_manifest,
            "SUBJECT_NOT_TERMINAL": self.m_subject_not_terminal,
            "ORIGIN_AUTHORITY_NOT_UNIQUE": self.m_origin,
            "ARTIFACT_REFUSED": self.m_artifact_refused,
            "ARTIFACT_SUBJECT_SPLIT": self.m_artifact_split,
            "UNAUTHORIZED_WORKTREE": self.m_worktree,
            "TRANSIENT_DEPENDENCY": self.m_transient,
            "SHA_NOT_MERGED": self.m_not_merged,
            "COLD_RECONSTRUCTION_DIVERGED": self.m_cold,
            "BERTHIER_COURT_FAILED": self.m_berthier,
            "XPROD_REFUSED": self.m_xprod,
            "TAG_SHA_SPLIT": self.m_tag,
            "CLAIM_WITHOUT_RECEIPT": self.m_claim,
            "RECEIPT_CHAIN_BROKEN": self.m_chain,
            "CROWN_SHA_SPLIT": self.m_crown_split,
            "BLOCKED_WITHOUT_TYPE": self.m_untyped,
            "UNKNOWN_EVIDENCE_KIND": self.m_unknown_kind,
            "PRIVATE_OBSERVATION_DIGEST_MISMATCH": self.m_private_digest,
            "PRIVATE_HEAD_SPLIT": self.m_private_split,
        }
        self.assertEqual(set(table), set(CROWN_RULES))
        for rule, mutant in table.items():
            with self.subTest(rule=rule):
                self.tree.cleanup()
                self.tree = alive_tree()
                self.obs = alive_observations(self.tree)
                result = mutant()
                if isinstance(result, crown.Verdict):
                    self.assertEqual(result.standing, "REFUSED")
                    self.assertIn(rule, {code_of(r) for r in result.refusals})
                else:
                    self.assertEqual((result.state, result.code), ("REFUSED", rule), result.detail)

    def test_every_code_maps_to_a_section39_class_and_broken_term(self):
        self.assertEqual(set(ALL_CODES), set(FAILURE_CLASS))
        for code, (cls, term) in FAILURE_CLASS.items():
            with self.subTest(code=code):
                self.assertIn(cls, FAILURE_CLASSES)
                self.assertIn(term, BROKEN_TERMS)

    def test_pass_states_carry_no_code(self):
        self.assertIsNone(PASS().code)


if __name__ == "__main__":
    unittest.main()
