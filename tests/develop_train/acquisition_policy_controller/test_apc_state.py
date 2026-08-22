from dataclasses import dataclass
import os
import sqlite3
import tempfile
import threading
import unittest

from scripts.develop_train.acquisition_policy_controller.receipt import issue
from scripts.develop_train.acquisition_policy_controller.state import (
    MemoryStateStore,
    PolicyState,
    SQLiteStateStore,
)
from scripts.develop_train.acquisition_policy_controller.subject import Refusal, Subject

S = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)


@dataclass(frozen=True)
class Policy:
    generation: int
    digest: str


@dataclass(frozen=True)
class Frontier:
    digest: str


@dataclass(frozen=True)
class Qualification:
    selected_strategy: str
    standing: str
    drifted: bool
    blockers: tuple
    receipt: object


def candidate(*, generation=1, expected=None, strategy="MAX_INFORMATION_GAIN", marker="1", standing="PARTIAL_ALIVE"):
    policy = Policy(generation, marker * 64)
    frontier = Frontier(str((int(marker) + 1) % 10) * 64)
    receipt = issue(
        S,
        policy_generation=generation,
        policy_digest=policy.digest,
        frontier_digest=frontier.digest,
        selected_strategy=strategy,
        standing=standing,
        parent=expected.digest if expected else None,
    )
    qualification = Qualification(strategy, standing, False, (), receipt)
    return PolicyState.from_qualification(S, policy, frontier, qualification, expected)


class PolicyStateCourt(unittest.TestCase):
    def exercise_store(self, store):
        first = candidate(marker="1")
        committed = store.compare_and_swap(S, None, first)
        self.assertEqual(committed.revision, 1)

        # A retry of the exact same transition is idempotent rather than duplicative.
        self.assertEqual(store.compare_and_swap(S, None, first), committed)
        self.assertEqual(len(store.audit(S)), 1)

        second = candidate(generation=2, expected=committed.token, marker="2")
        committed2 = store.compare_and_swap(S, committed.token, second)
        self.assertEqual(committed2.revision, 2)
        self.assertEqual([state.revision for state in store.audit(S)], [1, 2])

        # Same expected token with a different candidate is a stale writer.
        stale = candidate(generation=2, expected=committed.token, marker="3")
        with self.assertRaisesRegex(Refusal, "REFUSED_STALE_STATE_TOKEN"):
            store.compare_and_swap(S, committed.token, stale)
        self.assertEqual(store.load(S), committed2)

    def test_memory_store_has_exact_cas_and_idempotent_retry(self):
        self.exercise_store(MemoryStateStore())

    def test_sqlite_restart_recovers_current_and_audit_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "policy-state.sqlite3")
            self.exercise_store(SQLiteStateStore(path))
            reopened = SQLiteStateStore(path)
            self.assertEqual(reopened.load(S).revision, 2)
            self.assertEqual(len(reopened.audit(S)), 2)

    def test_sqlite_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "policy-state.sqlite3")
            store = SQLiteStateStore(path)
            first = candidate(marker="1")
            store.compare_and_swap(S, None, first)
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "UPDATE policy_state_current SET payload='{}' WHERE subject=?",
                    (S.exact,),
                )
            with self.assertRaisesRegex(Refusal, "REFUSED_CORRUPT_POLICY_STATE"):
                store.load(S)

    def test_generation_rollback_is_refused_without_mutating_current(self):
        store = MemoryStateStore()
        first = candidate(generation=2, marker="1")
        store.compare_and_swap(S, None, first)
        rollback = candidate(generation=1, expected=first.token, marker="2")
        with self.assertRaisesRegex(Refusal, "REFUSED_POLICY_GENERATION_ROLLBACK"):
            store.compare_and_swap(S, first.token, rollback)
        self.assertEqual(store.load(S), first)
        self.assertEqual(len(store.audit(S)), 1)

    def test_stale_aba_token_cannot_overwrite_newer_state(self):
        store = MemoryStateStore()
        state_a1 = candidate(generation=1, marker="1")
        store.compare_and_swap(S, None, state_a1)
        state_b = candidate(generation=1, expected=state_a1.token, marker="2")
        store.compare_and_swap(S, state_a1.token, state_b)
        state_a2 = candidate(generation=1, expected=state_b.token, marker="1")
        store.compare_and_swap(S, state_b.token, state_a2)
        self.assertNotEqual(state_a1.token, state_a2.token)
        stale = candidate(generation=1, expected=state_a1.token, marker="3")
        with self.assertRaisesRegex(Refusal, "REFUSED_STALE_STATE_TOKEN"):
            store.compare_and_swap(S, state_a1.token, stale)
        self.assertEqual(store.load(S), state_a2)

    def test_parallel_compare_and_swap_has_exactly_one_winner(self):
        store = MemoryStateStore()
        first = candidate(marker="1")
        store.compare_and_swap(S, None, first)
        barrier = threading.Barrier(2)
        outcomes = []
        outcome_lock = threading.Lock()

        def worker(marker):
            proposed = candidate(generation=2, expected=first.token, marker=marker)
            barrier.wait()
            try:
                store.compare_and_swap(S, first.token, proposed)
                outcome = "COMMITTED"
            except Refusal as error:
                outcome = str(error)
            with outcome_lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=worker, args=(marker,)) for marker in ("2", "3")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(outcomes.count("COMMITTED"), 1)
        self.assertEqual(outcomes.count("REFUSED_STALE_STATE_TOKEN"), 1)
        self.assertEqual(len(store.audit(S)), 2)

    def test_state_cannot_launder_scoped_standing_to_alive(self):
        with self.assertRaisesRegex(Refusal, "REFUSED_CORRUPT_POLICY_STATE"):
            candidate(marker="1", standing="ALIVE")


if __name__ == "__main__":
    unittest.main()
