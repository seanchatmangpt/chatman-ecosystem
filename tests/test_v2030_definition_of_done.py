from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "v2030_definition_of_done", ROOT / "scripts" / "v2030_definition_of_done.py"
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class V2030DefinitionOfDoneTest(unittest.TestCase):
    def assert_refused(self, fn, expected: str) -> None:
        with self.assertRaises(mod.Refusal) as ctx:
            fn()
        self.assertEqual(ctx.exception.code, expected)

    def test_repository_contract_is_bound_to_capability_graph_and_tpcs(self) -> None:
        mod.validate_repository_contract()

    def test_full_definition_of_done_reaches_alive(self) -> None:
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        result = mod.run(mod.reference_request(), store, world.actuate, world.observe)
        self.assertEqual(result["standing"], "ALIVE")
        self.assertEqual(result["replay"], "REPLAY_MATCH")
        self.assertEqual(result["stages"], list(mod.STAGES))
        self.assertEqual(world.actuation_count, 1)
        self.assertTrue(result["receipt"].startswith("sha256:"))

    def test_dfcm_preserves_all_reversible_lawful_candidates(self) -> None:
        frontier, excluded = mod.preserve_dfcm_frontier(mod.reference_request().candidates)
        self.assertEqual(
            [item.id for item in frontier],
            ["candidate:portable-b", "candidate:portable-a"],
        )
        self.assertEqual(excluded["candidate:blocked-edge"], "EXCLUDED_CONSTRAINT")
        self.assertEqual(excluded["candidate:irreversible-edge"], "EXCLUDED_IRREVERSIBLE")

    def test_selection_outside_frontier_is_refused(self) -> None:
        request = mod.reference_request()
        frontier, _ = mod.preserve_dfcm_frontier(request.candidates)
        self.assert_refused(
            lambda: mod.select_candidate(frontier, "candidate:blocked-edge"),
            "REFUSED_SELECTION_OUTSIDE_FRONTIER",
        )

    def test_invalid_exact_subject_refuses_before_actuation(self) -> None:
        base = mod.reference_request()
        request = mod.DefinitionOfDoneRequest(
            **{**base.__dict__, "subject": "HEAD"}
        )
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.run(request, mod.ReceiptStore(), world.actuate, world.observe),
            "REFUSED_INVALID_SUBJECT",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_authority_must_bind_exact_subject_and_consequence(self) -> None:
        base = mod.reference_request()
        bad_grant = mod.AuthorityGrant(
            grant_id="authority:bad",
            subject="f" * 40,
            consequence="deployed",
            scope="memory-world/reference",
        )
        request = mod.DefinitionOfDoneRequest(**{**base.__dict__, "authority": bad_grant})
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.run(request, mod.ReceiptStore(), world.actuate, world.observe),
            "REFUSED_AUTHORITY_SUBJECT_MISMATCH",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_missing_receipt_capability_refuses_before_do(self) -> None:
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.run(
                mod.reference_request(),
                mod.ReceiptStore(available=False),
                world.actuate,
                world.observe,
            ),
            "REFUSED_RECEIPT_CAPABILITY_UNAVAILABLE",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_verification_requires_evidence(self) -> None:
        base = mod.reference_request()
        request = mod.DefinitionOfDoneRequest(
            **{**base.__dict__, "verification_evidence": ()}
        )
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.run(request, mod.ReceiptStore(), world.actuate, world.observe),
            "REFUSED_VERIFICATION_EVIDENCE_MISSING",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_postcondition_failure_is_receipted_but_not_alive(self) -> None:
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()

        def wrong_actuator(_: str) -> str:
            world.actuation_count += 1
            world.state = "wrong-state"
            return world.state

        result = mod.run(mod.reference_request(), store, wrong_actuator, world.observe)
        self.assertEqual(result["standing"], "BLOCKED")
        self.assertEqual(result["replay"], "REPLAY_MATCH")
        self.assertEqual(world.actuation_count, 1)
        receipt = store.receipts["v2030-reference-1"]
        self.assertFalse(receipt["postcondition_verified"])
        self.assertEqual(receipt["outcome"], "blocked")

    def test_replay_and_idempotent_rerun_do_not_reactuate(self) -> None:
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        request = mod.reference_request()
        first = mod.run(request, store, world.actuate, world.observe)
        count = world.actuation_count
        second = mod.run(request, store, world.actuate, world.observe)
        self.assertEqual(first["receipt"], second["receipt"])
        self.assertEqual(world.actuation_count, count)

    def test_receipt_tampering_is_refused(self) -> None:
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        mod.run(mod.reference_request(), store, world.actuate, world.observe)
        receipt = copy.deepcopy(store.receipts["v2030-reference-1"])
        receipt["observed_postcondition"] = "tampered"
        self.assert_refused(
            lambda: store.verify(receipt),
            "REFUSED_RECEIPT_TAMPERED",
        )

    def test_precondition_mismatch_refuses_before_actuation(self) -> None:
        world = mod.MemoryWorld("unexpected")
        store = mod.ReceiptStore()
        self.assert_refused(
            lambda: mod.run(mod.reference_request(), store, world.actuate, world.observe),
            "REFUSED_PRECONDITION_MISMATCH",
        )
        self.assertEqual(world.actuation_count, 0)
        self.assertIn("v2030-reference-1", store.reservations)
        self.assertNotIn("v2030-reference-1", store.receipts)


if __name__ == "__main__":
    unittest.main()
