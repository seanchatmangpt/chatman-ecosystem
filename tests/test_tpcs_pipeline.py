from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tpcs_pipeline", ROOT / "scripts" / "tpcs_pipeline.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def item(
    work_id: str,
    subject_char: str,
    *,
    stream: str = "default",
    service: str = "standard",
    value: float = 0,
    urgency: float = 0,
    evidence: float = 0,
    risk: float = 0,
    cost: float = 0,
    cycle: float = 0,
    age: float = 0,
    acceptance_passed: bool = False,
):
    return mod.WorkItem(
        subject_char * 40,
        "python3 -m unittest tests.test_tpcs_pipeline -v",
        "CONSTRUCT",
        work_id=work_id,
        value_stream=stream,
        class_of_service=service,
        value=value,
        urgency=urgency,
        evidence=evidence,
        risk=risk,
        cost=cost,
        cycle_time=cycle,
        age=age,
        acceptance_passed=acceptance_passed,
    )


class ToyotaCodeProductionSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = mod.load_config()

    def test_config_preserves_constitutional_authority_boundaries(self) -> None:
        mod.validate_config(self.cfg)
        self.assertEqual(self.cfg["mode"], "pull")
        self.assertTrue(self.cfg["zero_unreceipted_actuation"])
        self.assertFalse(self.cfg["acceptance_mutation_authority"])
        self.assertFalse(self.cfg["planner_actuation_authority"])
        self.assertFalse(self.cfg["generated_projection_authority"])
        self.assertFalse(self.cfg["kaizen"]["auto_apply"])

    def test_stage_order_is_standard_work(self) -> None:
        self.assertEqual(
            [stage["id"] for stage in self.cfg["stage"]],
            ["observe", "admit", "construct", "verify", "receipt", "replay", "standing"],
        )

    def test_dfcm_frontier_prunes_only_dominated_candidates(self) -> None:
        strong = item("strong", "a", value=10, urgency=10, evidence=10, risk=1, cost=1, cycle=1)
        weak = item("weak", "b", value=1, urgency=1, evidence=1, risk=9, cost=9, cycle=9)
        tradeoff = item("tradeoff", "c", value=20, urgency=2, evidence=2, risk=5, cost=5, cycle=5)
        frontier = mod.pareto_frontier([weak, tradeoff, strong], self.cfg)
        self.assertEqual({x.id for x in frontier}, {"strong", "tradeoff"})

    def test_dfcm_plan_is_order_invariant_and_reversible(self) -> None:
        rows = [
            item("a", "a", stream="runtime", value=9, evidence=5, risk=2),
            item("b", "b", stream="semantic", value=5, evidence=9, risk=2),
            item("c", "c", stream="runtime", value=6, evidence=6, risk=1),
        ]
        forward = mod.plan(rows, self.cfg)
        reverse = mod.plan(list(reversed(rows)), self.cfg)
        self.assertEqual(forward, reverse)
        self.assertTrue(forward["selection_reversible"])
        self.assertEqual(forward["irreversible_selections"], 0)
        self.assertEqual(forward["planner_authority"], "SELECT")
        self.assertFalse(forward["actuation"])

    def test_heijunka_levels_value_streams_when_alternatives_exist(self) -> None:
        rows = [
            item("a1", "a", stream="a", value=10, risk=1),
            item("a2", "b", stream="a", value=9, risk=1),
            item("b1", "c", stream="b", value=8, risk=1),
        ]
        schedule = mod.level_schedule(mod.pareto_frontier(rows, self.cfg), self.cfg)
        streams = [x.value_stream for x in schedule]
        if len(streams) >= 2:
            self.assertNotEqual(streams[0], streams[1])

    def test_duplicate_work_id_is_poka_yoke_refusal(self) -> None:
        with self.assertRaises(mod.Refusal) as ctx:
            mod.pareto_frontier([item("dup", "a"), item("dup", "b")], self.cfg)
        self.assertEqual(str(ctx.exception), "REFUSED_DUPLICATE_WORK_ID")

    def test_identity_drift_is_refused(self) -> None:
        drift = mod.WorkItem(
            "a" * 40,
            "x",
            "SELECT",
            observed_subject="b" * 40,
        )
        with self.assertRaises(mod.Refusal) as ctx:
            mod.run(drift, self.cfg)
        self.assertEqual(str(ctx.exception), "REFUSED_IDENTITY_DRIFT")

    def test_kanban_pull_requires_downstream_capacity(self) -> None:
        token = mod.pull_token("construct", 3, self.cfg)
        self.assertEqual(token["token_count"], 1)
        self.assertFalse(token["actuation"])
        with self.assertRaises(mod.Refusal) as ctx:
            mod.pull_token("construct", 4, self.cfg)
        self.assertEqual(str(ctx.exception), "REFUSED_NO_KANBAN_CAPACITY")

    def test_jidoka_andon_stops_the_line(self) -> None:
        with self.assertRaises(mod.Refusal) as ctx:
            mod.pull_token("verify", 0, self.cfg, andon_active=True)
        self.assertEqual(str(ctx.exception), "REFUSED_ANDON_ACTIVE")
        with self.assertRaises(mod.Refusal) as ctx:
            mod.run(mod.WorkItem("a" * 40, "x", "SELECT", andon_active=True), self.cfg)
        self.assertEqual(str(ctx.exception), "REFUSED_ANDON_ACTIVE")

    def test_takt_and_littles_law_metrics(self) -> None:
        metrics = mod.flow_metrics(480, 12, 0.05, 10, self.cfg)
        self.assertEqual(metrics["takt_minutes_per_item"], 40)
        self.assertEqual(metrics["cycle_time_minutes"], 200)
        self.assertEqual(metrics["little_law_reconstructed_wip"], 10)
        self.assertTrue(metrics["meets_takt"])

    def test_invalid_flow_metrics_fail_closed(self) -> None:
        with self.assertRaises(mod.Refusal) as ctx:
            mod.flow_metrics(480, 0, 0.05, 10, self.cfg)
        self.assertEqual(str(ctx.exception), "REFUSED_INVALID_FLOW_METRIC")

    def test_bottleneck_detection_and_kaizen_do_not_auto_actuate(self) -> None:
        result = mod.bottleneck(
            {"observe": 2, "construct": 4, "verify": 2},
            self.cfg,
            throughput={"observe": 1.0, "construct": 0.2, "verify": 0.5},
            defects={"construct": 1},
        )
        self.assertEqual(result["stage"], "construct")
        proposal = mod.kaizen_proposal(result, self.cfg)
        assert proposal is not None
        self.assertEqual(proposal["authority"], "SELECT")
        self.assertTrue(proposal["reversible"])
        self.assertFalse(proposal["auto_apply"])
        self.assertFalse(proposal["may_mutate_acceptance"])
        self.assertFalse(proposal["may_mutate_wip_limits"])

    def test_acceptance_evidence_controls_standing(self) -> None:
        pending = mod.run(item("pending", "a"), self.cfg)
        alive = mod.run(item("alive", "b", acceptance_passed=True), self.cfg)
        self.assertEqual(pending["standing"], "PARTIAL_ALIVE")
        self.assertEqual(alive["standing"], "ALIVE")
        self.assertTrue(alive["receipt_verified"])

    def test_receipt_binds_config_work_frontier_schedule_and_chain(self) -> None:
        work = item("alive", "a", acceptance_passed=True)
        record = mod.run(
            work,
            self.cfg,
            frontier_ids=["alive", "other"],
            schedule_ids=["other", "alive"],
            previous_receipt="f" * 64,
        )
        self.assertTrue(mod.verify_receipt(record, self.cfg))
        self.assertRegex(record["config_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(record["work_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(record["frontier_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(record["schedule_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(record["previous_receipt"], "f" * 64)

        tampered = dict(record)
        tampered["subject"] = "b" * 40
        self.assertFalse(mod.verify_receipt(tampered, self.cfg))

    def test_acceptance_mutation_unreceipted_do_and_replay_mismatch_refuse(self) -> None:
        cases = [
            (mod.WorkItem("a" * 40, "x", "CONSTRUCT", acceptance_mutated=True), "REFUSED_ACCEPTANCE_MUTATION"),
            (mod.WorkItem("b" * 40, "x", "DO", actuation_receipted=False), "REFUSED_UNRECEIPTED_ACTUATION"),
            (mod.WorkItem("c" * 40, "x", "SELECT", replay_match=False), "REFUSED_REPLAY_MISMATCH"),
        ]
        for work, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(mod.Refusal) as ctx:
                    mod.run(work, self.cfg)
                self.assertEqual(str(ctx.exception), expected)

    def test_ontology_exposes_production_control_objects_and_authority_ceiling(self) -> None:
        text = (ROOT / "ontology" / "tpcs.ttl").read_text(encoding="utf-8")
        for token in (
            "tpcs:WorkItem",
            "tpcs:ParetoFrontier",
            "tpcs:KanbanToken",
            "tpcs:AndonSignal",
            "tpcs:KaizenProposal",
            "tpcs:ProductionReceipt",
            "tpcs:zeroUnreceiptedActuation true",
            "tpcs:plannerActuationAuthority false",
            "tpcs:acceptanceMutationAuthority false",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
