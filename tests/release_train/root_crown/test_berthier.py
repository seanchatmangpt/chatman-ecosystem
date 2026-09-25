"""Berthier recompile court (RFC-0004 §8/§9): the crown test plus one refusing mutant per rule."""

from __future__ import annotations

import json
import unittest

from _support import committed_tree

from scripts.release_train.invalidation_promotion.subject import Refusal
from scripts.release_train.root_crown import berthier, evidence
from scripts.release_train.root_crown.model import BERTHIER_RULES, code_of
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
        verdict = self.judge()
        self.assertEqual((verdict.standing, verdict.refusals), ("ALIVE", ()))
        owners = sorted({r.owner_repo for r in self.inputs.requirements})
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
        self.assertEqual(set(table) | {"NO_RENEWAL_DELTA"}, set(BERTHIER_RULES))
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


if __name__ == "__main__":
    unittest.main()
