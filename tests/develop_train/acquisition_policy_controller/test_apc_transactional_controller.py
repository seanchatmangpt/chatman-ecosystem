from datetime import datetime, timedelta, timezone
import os
import tempfile
import unittest

from scripts.develop_train.acquisition_policy_controller.controller import qualify_and_commit
from scripts.develop_train.acquisition_policy_controller.dependency import DependencyGraph
from scripts.develop_train.acquisition_policy_controller.frontier import PolicyFrontier
from scripts.develop_train.acquisition_policy_controller.policy import Policy
from scripts.develop_train.acquisition_policy_controller.realization import Realization
from scripts.develop_train.acquisition_policy_controller.state import MemoryStateStore, SQLiteStateStore
from scripts.develop_train.acquisition_policy_controller.subject import Refusal, Subject

S = Subject("seanchatmangpt/chatman-ecosystem", "b" * 40)
OBSERVED = datetime.now(timezone.utc) - timedelta(seconds=2)
GRAPH = DependencyGraph({"root": ()}, {})


def row(strategy, gain, candidate_id, generation):
    return Realization(
        S,
        f"plan-{generation}",
        candidate_id,
        strategy,
        generation,
        0.2,
        gain,
        1.0,
        1.0,
        10.0,
        10.0,
        OBSERVED,
        "PASS",
    )


def inputs(generation, gains=(0.5, 0.2, 0.1)):
    policy = Policy(generation, 0.0, 1, 10.0, 100.0, 0.5)
    frontier = PolicyFrontier(generation, policy.digest, f"{generation:x}" * 64)
    rows = [
        row("MAX_INFORMATION_GAIN", gains[0], f"gain-{generation}", generation),
        row("MAX_INFORMATION_PER_COST", gains[1], f"cost-{generation}", generation),
        row("MIN_EXPECTED_ENTROPY", gains[2], f"entropy-{generation}", generation),
    ]
    return policy, frontier, rows


class TransactionalControllerCourt(unittest.TestCase):
    def test_exact_retry_is_idempotent_and_receipt_is_state_chained(self):
        store = MemoryStateStore()
        policy, frontier, rows = inputs(1)
        first = qualify_and_commit(S, policy, rows, frontier, GRAPH, "root", 1, store, None)
        retry = qualify_and_commit(S, policy, rows, frontier, GRAPH, "root", 1, store, None)
        self.assertEqual(retry.state, first.state)
        self.assertEqual(len(store.audit(S)), 1)
        self.assertIsNone(first.qualification.receipt.parent)
        self.assertFalse(first.qualification.receipt.actuation_performed)

        policy2, frontier2, rows2 = inputs(2, (0.1, 0.6, 0.2))
        second = qualify_and_commit(
            S, policy2, rows2, frontier2, GRAPH, "root", 2, store, first.state.token
        )
        self.assertEqual(second.state.previous_digest, first.state.digest)
        self.assertEqual(second.qualification.receipt.parent, first.state.digest)
        self.assertEqual(second.state.receipt_digest, second.qualification.receipt.digest)
        self.assertEqual(len(store.audit(S)), 2)

    def test_lost_update_refuses_and_preserves_committed_state(self):
        store = MemoryStateStore()
        policy, frontier, rows = inputs(1)
        first = qualify_and_commit(S, policy, rows, frontier, GRAPH, "root", 1, store, None)
        policy2, frontier2, rows2 = inputs(2, (0.1, 0.6, 0.2))
        second = qualify_and_commit(
            S, policy2, rows2, frontier2, GRAPH, "root", 2, store, first.state.token
        )
        policy3, frontier3, rows3 = inputs(3, (0.9, 0.1, 0.1))
        with self.assertRaisesRegex(Refusal, "REFUSED_STALE_STATE_TOKEN"):
            qualify_and_commit(
                S, policy3, rows3, frontier3, GRAPH, "root", 3, store, first.state.token
            )
        self.assertEqual(store.load(S), second.state)
        self.assertEqual(len(store.audit(S)), 2)

    def test_sqlite_controller_survives_process_style_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "controller.sqlite3")
            store = SQLiteStateStore(path)
            policy, frontier, rows = inputs(1)
            first = qualify_and_commit(S, policy, rows, frontier, GRAPH, "root", 1, store, None)
            reopened = SQLiteStateStore(path)
            self.assertEqual(reopened.load(S), first.state)
            policy2, frontier2, rows2 = inputs(2, (0.1, 0.6, 0.2))
            second = qualify_and_commit(
                S,
                policy2,
                rows2,
                frontier2,
                GRAPH,
                "root",
                2,
                reopened,
                first.state.token,
            )
            final = SQLiteStateStore(path)
            self.assertEqual(final.load(S), second.state)
            self.assertEqual([state.revision for state in final.audit(S)], [1, 2])


if __name__ == "__main__":
    unittest.main()
