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

    def test_repository_contract_reuses_canonical_dfcm_owner(self) -> None:
        mod.validate_repository_contract()
        self.assertTrue(callable(mod.dfcm.definition_of_done))
        self.assertTrue(callable(mod.dfcm.admit_do))
        self.assertTrue(callable(mod.dfcm.replay_receipts))

    def test_prepare_is_construct_only_and_execution_reaches_alive(self) -> None:
        request = mod.reference_request()
        prepared = mod.prepare(request)
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        self.assertEqual(world.actuation_count, 0)
        grant = mod.reference_grant(prepared)
        result = mod.execute(prepared, grant, store, world.actuate, world.observe)
        self.assertEqual(result["standing"], "ALIVE")
        self.assertTrue(result["replay"].startswith("ALIVE:REPLAY:"))
        self.assertEqual(result["stages"], list(mod.STAGES))
        self.assertEqual(world.actuation_count, 1)
        self.assertEqual(result["intent_digest"], prepared.intent["intent_digest"])

    def test_dfcm_action_frontier_preserves_all_reversible_lawful_edges(self) -> None:
        frontier, excluded = mod.preserve_action_frontier(mod.reference_request().candidates)
        self.assertEqual(
            [item.id for item in frontier],
            ["candidate:portable-b", "candidate:portable-a"],
        )
        self.assertEqual(excluded["candidate:blocked-edge"], "EXCLUDED_CONSTRAINT")
        self.assertEqual(excluded["candidate:irreversible-edge"], "EXCLUDED_IRREVERSIBLE")

    def test_selection_outside_frontier_is_refused(self) -> None:
        request = mod.reference_request()
        frontier, _ = mod.preserve_action_frontier(request.candidates)
        self.assert_refused(
            lambda: mod.select_candidate(frontier, "candidate:blocked-edge"),
            "REFUSED_SELECTION_OUTSIDE_FRONTIER",
        )

    def test_invalid_exact_subject_refuses_before_authority_or_actuation(self) -> None:
        base = mod.reference_request()
        request = mod.DefinitionOfDoneRequest(**{**base.__dict__, "subject": "HEAD"})
        world = mod.MemoryWorld("planned")
        self.assert_refused(lambda: mod.prepare(request), "REFUSED_INVALID_SUBJECT")
        self.assertEqual(world.actuation_count, 0)

    def test_exact_dfcm_authority_must_bind_prepared_intent(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        bad_grant = mod.AuthorityGrant(
            authority_id="authority:bad",
            subject_sha=prepared.request.subject,
            intent_digest="0" * 64,
            consequence=prepared.selected.consequence,
        )
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.execute(prepared, bad_grant, mod.ReceiptStore(), world.actuate, world.observe),
            "REFUSED_DFCM_DO_INTENT_DRIFT",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_authority_consequence_mismatch_refuses_before_do(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.AuthorityGrant(
            authority_id="authority:bad-consequence",
            subject_sha=prepared.request.subject,
            intent_digest=prepared.intent["intent_digest"],
            consequence="destroyed",
        )
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.execute(prepared, grant, mod.ReceiptStore(), world.actuate, world.observe),
            "REFUSED_AUTHORITY_CONSEQUENCE_MISMATCH",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_missing_receipt_capability_refuses_before_do(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.reference_grant(prepared)
        world = mod.MemoryWorld("planned")
        self.assert_refused(
            lambda: mod.execute(
                prepared,
                grant,
                mod.ReceiptStore(available=False),
                world.actuate,
                world.observe,
            ),
            "REFUSED_RECEIPT_CAPABILITY_UNAVAILABLE",
        )
        self.assertEqual(world.actuation_count, 0)

    def test_verification_requires_evidence(self) -> None:
        base = mod.reference_request()
        request = mod.DefinitionOfDoneRequest(**{**base.__dict__, "verification_evidence": ()})
        self.assert_refused(
            lambda: mod.prepare(request),
            "REFUSED_VERIFICATION_EVIDENCE_MISSING",
        )

    def test_postcondition_failure_is_receipted_but_not_alive(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.reference_grant(prepared)
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()

        def wrong_actuator(_: str) -> str:
            world.actuation_count += 1
            world.state = "wrong-state"
            return world.state

        result = mod.execute(prepared, grant, store, wrong_actuator, world.observe)
        self.assertEqual(result["standing"], "BLOCKED")
        self.assertTrue(result["replay"].startswith("ALIVE:REPLAY:"))
        self.assertEqual(world.actuation_count, 1)
        event = store.receipts["v2030-reference-1"]["envelope"]["event"]
        self.assertFalse(event["postcondition_verified"])
        self.assertEqual(event["outcome"], "blocked")

    def test_replay_and_idempotent_rerun_do_not_reactuate(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.reference_grant(prepared)
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        first = mod.execute(prepared, grant, store, world.actuate, world.observe)
        count = world.actuation_count
        second = mod.execute(prepared, grant, store, world.actuate, world.observe)
        self.assertEqual(first["receipt"], second["receipt"])
        self.assertEqual(world.actuation_count, count)

    def test_receipt_tampering_is_refused_by_canonical_replay(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.reference_grant(prepared)
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        mod.execute(prepared, grant, store, world.actuate, world.observe)
        stored = copy.deepcopy(store.receipts["v2030-reference-1"])
        stored["envelope"]["event"]["observed_postcondition"] = "tampered"
        self.assert_refused(lambda: store.verify(stored), "REFUSED_RECEIPT_NOT_PERSISTED")

    def test_persisted_receipt_tamper_hits_dfcm_replay_court(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.reference_grant(prepared)
        world = mod.MemoryWorld("planned")
        store = mod.ReceiptStore()
        mod.execute(prepared, grant, store, world.actuate, world.observe)
        stored = store.receipts["v2030-reference-1"]
        stored["envelope"]["event"]["observed_postcondition"] = "tampered"
        self.assert_refused(lambda: store.verify(stored), "REFUSED_RECEIPT_TAMPERED")

    def test_precondition_mismatch_refuses_after_reservation_before_actuation(self) -> None:
        prepared = mod.prepare(mod.reference_request())
        grant = mod.reference_grant(prepared)
        world = mod.MemoryWorld("unexpected")
        store = mod.ReceiptStore()
        self.assert_refused(
            lambda: mod.execute(prepared, grant, store, world.actuate, world.observe),
            "REFUSED_PRECONDITION_MISMATCH",
        )
        self.assertEqual(world.actuation_count, 0)
        self.assertIn("v2030-reference-1", store.reservations)
        self.assertNotIn("v2030-reference-1", store.receipts)


if __name__ == "__main__":
    unittest.main()
