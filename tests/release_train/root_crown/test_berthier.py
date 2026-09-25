"""Berthier recompile court (RFC-0004 §8/§9): the crown test plus one refusing mutant per rule."""

from __future__ import annotations

from dataclasses import replace
import json
import unittest

from _support import committed_tree

from scripts.release_train.invalidation_promotion.subject import Refusal
from scripts.release_train.root_crown import berthier, evidence
from scripts.release_train.root_crown.model import BERTHIER_CAMPAIGN_RULES, BERTHIER_RULES, code_of
from scripts.release_train.root_crown.requirements import premise_sections


class BerthierTest(unittest.TestCase):
    def setUp(self):
        self.tree = committed_tree()
        self.inputs = self.tree.inputs()
        self.graph = self.inputs.prior_berthier
        self.edges = berthier.edges_from_json(self.graph["edges"])
        self.packets = json.loads((self.tree.release_dir / "out/packets.json").read_text())["packets"]

    def tearDown(self):
        self.tree.cleanup()

    def current(self, text=None):
        cur = berthier.source_digests(text or self.inputs.rfc_text, self.inputs.requirements)
        for name in berthier.PROJECTED_OUTPUTS:
            cur[f"proj:{name}"] = berthier.sha256_bytes((self.tree.release_dir / name).read_bytes())
        return cur

    def judge(self, edges=None, current=None, packets=None, observed=None, failures=()):
        return berthier.judge(
            self.edges if edges is None else edges,
            self.current() if current is None else current,
            self.packets if packets is None else packets,
            self.graph["baseline"],
            observed,
            failures,
        )

    def test_committed_graph_is_alive(self):
        """RFC §8: packets cover exactly the owners the committed strategic delta reaches.

        Genesis (every premise section in the delta) reaches every owner; a renewal that
        changes one requirement row reaches only that row's owner. The expected owner set
        is computed here from the delta keys and the requirement rows, not by the projector.
        """
        verdict = self.judge()
        self.assertEqual((verdict.standing, verdict.refusals), ("ALIVE", ()))
        doc = json.loads((self.tree.release_dir / "out/packets.json").read_text())
        changed = set(doc["strategic_delta"])
        self.assertTrue(changed, "committed packets carry no strategic delta")
        owners = sorted(
            {
                r.owner_repo
                for r in self.inputs.requirements
                if f"req:{r.id}" in changed or any(f"premise:RFC-0004#{ref}" in changed for ref in r.premise_refs)
            }
        )
        self.assertTrue(owners)
        self.assertEqual(list(verdict.required_owners), owners)
        self.assertEqual(sorted(p["subject"]["repository"] for p in self.packets), owners)

    def test_rfc9_crown_test_default_section_fans_out_to_every_owner(self):
        ok, detail = evidence.crown_test(self.inputs)
        self.assertTrue(ok, detail)
        self.assertIn("ManualRestatementCount=0", detail)
        self.assertIn("section=§3", detail)

    def test_rfc9_crown_test_exact_dependents_for_each_referenced_section(self):
        sections = sorted({ref for r in self.inputs.requirements for ref in r.premise_refs})
        for section in sections:
            with self.subTest(section=section):
                ok, detail = evidence.crown_test(self.inputs, section)
                self.assertTrue(ok, detail)

    def test_premise_mutation_refuses_exactly_dependents_then_recompile_is_alive(self):
        section = "§22"
        original = premise_sections(self.inputs.rfc_text)[section]
        mutated = self.inputs.rfc_text.replace(original, original + "\nchanged once", 1)
        verdict = self.judge(current=self.current(mutated))
        stale = {code.split(":", 2)[2] for code in verdict.refusals if code_of(code) == "STALE_PROJECTION"}
        expected = set()
        for req in self.inputs.requirements:
            if section in req.premise_refs:
                expected |= {f"req:{req.id}", f"packet:{req.owner_repo}", f"artifact:{req.evidence_locator}"}
        expected |= {f"proj:{o}" for o in berthier.PROJECTED_OUTPUTS}
        self.assertEqual(stale, expected)
        self.assertEqual(set(verdict.stale), expected)
        # Regenerate from the mutated premise only: ALIVE, packets exactly for the affected owner.
        from scripts.release_train.root_crown import projector

        out = projector.compile_graph(self.inputs, rfc_text=mutated)
        graph = json.loads(out["berthier.json"])
        packets = json.loads(out["out/packets.json"])["packets"]
        cur = berthier.source_digests(mutated, self.inputs.requirements)
        cur["proj:out/packets.json"] = berthier.sha256_bytes(out["out/packets.json"])
        cur["proj:out/requirements.ttl"] = berthier.sha256_bytes(out["out/requirements.ttl"])
        after = berthier.judge(berthier.edges_from_json(graph["edges"]), cur, packets, graph["baseline"])
        self.assertEqual(after.refusals, ())
        self.assertEqual([p["subject"]["repository"] for p in packets], ["seanchatmangpt/xaas"])
        self.assertEqual(json.loads(out["out/packets.json"])["strategic_delta"], ["premise:RFC-0004#§22"])

    # --- one refusing mutant per rule -------------------------------------------------
    def m_stale(self):
        original = premise_sections(self.inputs.rfc_text)["§9"]
        return self.judge(current=self.current(self.inputs.rfc_text.replace(original, original + "!", 1)))

    def m_artifact(self):
        edges = tuple(
            berthier.Edge(e.producer, e.consumer, e.receipt, e.schema, "d" * 64)
            if e.consumer.key.startswith("artifact:")
            else e
            for e in self.edges
        )
        key = next(e.consumer.key for e in edges if e.consumer.key.startswith("artifact:"))
        return self.judge(edges=edges, observed={key: "e" * 64})

    def m_omitted(self):
        return self.judge(packets=self.packets[1:])

    def m_unevidenced(self):
        extra = dict(self.packets[0], subject={"repository": "seanchatmangpt/beam4pm"})
        return self.judge(packets=self.packets + [extra])

    def m_authority(self):
        return self.judge(packets=[dict(self.packets[0], authority_ceiling="DO")] + self.packets[1:])

    def m_break_glass(self):
        return self.judge(packets=[dict(self.packets[0], mode="break_glass")] + self.packets[1:])

    def m_premise_unbound(self):
        edge = berthier.Edge(
            berthier.Node("premise:RFC-0004#§99"), berthier.Node("req:AC-01"), "f" * 64, berthier.SCHEMA, ""
        )
        return self.judge(edges=self.edges + (edge,))

    def m_cycle(self):
        edge = berthier.Edge(
            berthier.Node("proj:out/packets.json"), berthier.Node("req:AC-01"), "f" * 64, berthier.SCHEMA, ""
        )
        return self.judge(edges=self.edges + (edge,))

    def test_one_refusing_mutant_per_rule(self):
        table = {
            "STALE_PROJECTION": self.m_stale,
            "ARTIFACT_DIGEST_MISMATCH": self.m_artifact,
            "OMITTED_SUBJECT": self.m_omitted,
            "UNEVIDENCED_WORK": self.m_unevidenced,
            "AUTHORITY_INCREASE": self.m_authority,
            "BREAK_GLASS_AS_NORMAL": self.m_break_glass,
            "PREMISE_UNBOUND": self.m_premise_unbound,
            "DEPENDENCY_CYCLE": self.m_cycle,
        }
        self.assertEqual(
            set(table) | {"NO_RENEWAL_DELTA"} | set(BERTHIER_CAMPAIGN_RULES),
            set(BERTHIER_RULES),
        )
        for rule, mutant in table.items():
            with self.subTest(rule=rule):
                verdict = mutant()
                self.assertEqual(verdict.standing, "REFUSED")
                self.assertIn(rule, {code_of(r) for r in verdict.refusals})

    def test_break_glass_with_recorded_live_failure_is_admitted(self):
        packets = [dict(self.packets[0], mode="break_glass")] + self.packets[1:]
        owner = packets[0]["subject"]["repository"]
        self.assertEqual(self.judge(packets=packets, failures=[owner]).refusals, ())

    def test_renewal_requires_a_real_delta(self):
        edge = self.edges[0]
        with self.assertRaisesRegex(Refusal, "NO_RENEWAL_DELTA"):
            berthier.renew_projection(edge, edge.compiled_from, edge.consumer_digest)
        renewed = berthier.renew_projection(edge, "1" * 64, "2" * 64)
        self.assertEqual((renewed.compiled_from, renewed.consumer_digest), ("1" * 64, "2" * 64))


class BerthierCampaignTest(unittest.TestCase):
    """RFC-native campaign compiler: doctrine -> isolated candidates -> court -> SELECT."""

    def setUp(self):
        self.global_premises = {
            "premise:RFC-0004#§3": "3" * 64,
            "premise:RFC-0004#§8": "8" * 64,
        }
        self.local = {
            "instance:cost-model": "a" * 64,
            "instance:nondeterminism": "b" * 64,
            "instance:latency-model": "c" * 64,
        }
        self.doctrine = berthier.compile_doctrine(
            "release:v26.9.25",
            self.global_premises,
            (
                "SELECT != CONSTRUCT != DO",
                "authority ceiling CONSTRUCT",
                "zero unreceipted actuation",
            ),
            ("HDDL", "FOND", "XPROD"),
        )
        self.partitions = (
            berthier.partition_strategy(
                self.doctrine,
                "hddl",
                "hierarchical decomposition",
                {"instance:cost-model": self.local["instance:cost-model"]},
                ("prefer reusable methods",),
            ),
            berthier.partition_strategy(
                self.doctrine,
                "fond",
                "nondeterministic recovery",
                {"instance:nondeterminism": self.local["instance:nondeterminism"]},
                ("all outcomes have recovery",),
            ),
            berthier.partition_strategy(
                self.doctrine,
                "or",
                "objective optimization",
                {"instance:latency-model": self.local["instance:latency-model"]},
                ("minimize measured cost",),
            ),
        )
        costs = {"hddl": 5.0, "fond": 7.0, "or": 3.0}
        self.candidates = tuple(
            berthier.candidate_from_partition(
                self.doctrine,
                partition,
                f"candidate:{partition.strategy_id}",
                f"counterexample to {partition.strategy_id}",
                {"cost": costs[partition.strategy_id], "information_gain": 1.0},
            )
            for partition in self.partitions
        )

    def court(self, candidates=None, partitions=None, current=None):
        candidates = self.candidates if candidates is None else tuple(candidates)
        partitions = self.partitions if partitions is None else tuple(partitions)
        by_strategy = {p.strategy_id: p for p in partitions}
        current = self.local if current is None else current
        return tuple(
            berthier.judge_campaign_candidate(
                self.doctrine,
                by_strategy[c.strategy_id],
                c,
                current,
            )
            for c in candidates
        )

    def test_three_isolated_candidates_are_alive_and_select_is_non_actuating(self):
        verdicts = self.court()
        self.assertEqual([v.standing for v in verdicts], ["ALIVE", "ALIVE", "ALIVE"])
        self.assertEqual(
            len({c.observed_partition_digests for c in self.candidates}),
            3,
            "each candidate must observe exactly its own sealed partition",
        )
        selection = berthier.select_campaign(self.candidates, verdicts, "cost")
        self.assertIsNotNone(selection)
        self.assertEqual(selection.candidate_id, "candidate:or")
        artifacts = berthier.campaign_artifacts(
            self.doctrine, self.partitions, self.candidates, verdicts, selection
        )
        campaign = json.loads(artifacts["out/campaign.json"])
        self.assertEqual(campaign["actuation"], "NONE")
        self.assertEqual(campaign["authority_ceiling"], "CONSTRUCT")
        self.assertIn("BRCE", campaign["successor_boundary"])

    def test_constraint_weakening_is_refused(self):
        bad = replace(self.candidates[0], invariants=self.candidates[0].invariants[:-1])
        verdict = berthier.judge_campaign_candidate(
            self.doctrine, self.partitions[0], bad, self.local
        )
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("CONSTRAINT_WEAKENING", {code_of(r) for r in verdict.refusals})

    def test_cross_partition_contamination_is_refused(self):
        bad = replace(
            self.candidates[0],
            observed_partition_digests=(
                self.partitions[0].partition_digest,
                self.partitions[1].partition_digest,
            ),
        )
        verdict = berthier.judge_campaign_candidate(
            self.doctrine, self.partitions[0], bad, self.local
        )
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("CROSS_PARTITION_CONTAMINATION", {code_of(r) for r in verdict.refusals})

    def test_do_is_refused_even_when_authority_field_claims_construct(self):
        bad = replace(self.candidates[0], actions=self.candidates[0].actions + ("DO",))
        verdict = berthier.judge_campaign_candidate(
            self.doctrine, self.partitions[0], bad, self.local
        )
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("STRATEGY_UNBOUNDED", {code_of(r) for r in verdict.refusals})

    def test_authority_increase_is_refused(self):
        bad = replace(self.candidates[0], authority_ceiling="DO")
        verdict = berthier.judge_campaign_candidate(
            self.doctrine, self.partitions[0], bad, self.local
        )
        self.assertEqual(verdict.standing, "REFUSED")
        self.assertIn("AUTHORITY_INCREASE", {code_of(r) for r in verdict.refusals})

    def test_selection_excludes_a_refused_candidate_even_if_objective_is_better(self):
        bad = replace(
            self.candidates[2],
            actions=self.candidates[2].actions + ("DO",),
            objectives=(("cost", 0.0), ("information_gain", 1.0)),
        )
        candidates = self.candidates[:2] + (bad,)
        verdicts = self.court(candidates=candidates)
        selection = berthier.select_campaign(candidates, verdicts, "cost")
        self.assertIsNotNone(selection)
        self.assertEqual(selection.candidate_id, "candidate:hddl")

    def test_local_premise_mutation_invalidates_exact_branch_and_preserves_other_bytes(self):
        before_verdicts = self.court()
        before_selection = berthier.select_campaign(self.candidates, before_verdicts, "cost")
        before = berthier.campaign_artifacts(
            self.doctrine, self.partitions, self.candidates, before_verdicts, before_selection
        )

        mutated_local = dict(self.local, **{"instance:nondeterminism": "d" * 64})
        self.assertEqual(
            berthier.campaign_dependents(self.partitions, ("instance:nondeterminism",)),
            ("fond",),
        )
        stale = self.court(current=mutated_local)
        self.assertEqual(
            [v.standing for v in stale],
            ["ALIVE", "REFUSED", "ALIVE"],
        )
        self.assertIn("STALE_PROJECTION", {code_of(r) for r in stale[1].refusals})

        rebuilt_fond = berthier.partition_strategy(
            self.doctrine,
            "fond",
            "nondeterministic recovery",
            {"instance:nondeterminism": mutated_local["instance:nondeterminism"]},
            ("all outcomes have recovery",),
        )
        rebuilt_candidate = berthier.candidate_from_partition(
            self.doctrine,
            rebuilt_fond,
            "candidate:fond",
            "counterexample to fond",
            {"cost": 7.0, "information_gain": 1.0},
        )
        after_partitions = (self.partitions[0], rebuilt_fond, self.partitions[2])
        after_candidates = (self.candidates[0], rebuilt_candidate, self.candidates[2])
        after_verdicts = tuple(
            berthier.judge_campaign_candidate(
                self.doctrine,
                p,
                c,
                mutated_local,
            )
            for p, c in zip(after_partitions, after_candidates)
        )
        self.assertEqual([v.standing for v in after_verdicts], ["ALIVE", "ALIVE", "ALIVE"])
        after_selection = berthier.select_campaign(after_candidates, after_verdicts, "cost")
        after = berthier.campaign_artifacts(
            self.doctrine, after_partitions, after_candidates, after_verdicts, after_selection
        )

        self.assertEqual(before["out/strategies/hddl.json"], after["out/strategies/hddl.json"])
        self.assertEqual(before["out/strategies/or.json"], after["out/strategies/or.json"])
        self.assertNotEqual(before["out/strategies/fond.json"], after["out/strategies/fond.json"])
        self.assertEqual(before["out/courts/hddl.json"], after["out/courts/hddl.json"])
        self.assertEqual(before["out/courts/or.json"], after["out/courts/or.json"])
        self.assertNotEqual(before["out/courts/fond.json"], after["out/courts/fond.json"])

    def test_campaign_rule_set_has_a_refusing_mutant_per_new_rule(self):
        mutants = {
            "CONSTRAINT_WEAKENING": replace(
                self.candidates[0], invariants=self.candidates[0].invariants[:-1]
            ),
            "CROSS_PARTITION_CONTAMINATION": replace(
                self.candidates[0],
                observed_partition_digests=(
                    self.partitions[0].partition_digest,
                    self.partitions[1].partition_digest,
                ),
            ),
            "STRATEGY_UNBOUNDED": replace(
                self.candidates[0], actions=self.candidates[0].actions + ("DO",)
            ),
        }
        self.assertEqual(set(mutants), set(BERTHIER_CAMPAIGN_RULES))
        for rule, mutant in mutants.items():
            with self.subTest(rule=rule):
                verdict = berthier.judge_campaign_candidate(
                    self.doctrine, self.partitions[0], mutant, self.local
                )
                self.assertIn(rule, {code_of(r) for r in verdict.refusals})


if __name__ == "__main__":
    unittest.main()
