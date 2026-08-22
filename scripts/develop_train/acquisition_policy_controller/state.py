from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Iterable

from .realization import STRATEGIES
from .receipt import replay
from .subject import Refusal, Subject

SCHEMA = "chatman.develop-acquisition-policy-state/1"
_HEX = frozenset("0123456789abcdef")
_ALLOWED_STANDING = frozenset(
    {"UNKNOWN", "PARTIAL_ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}
)


def _digest(body: dict) -> str:
    encoded = json.dumps(
        {"schema": SCHEMA, **body}, sort_keys=True, separators=(",", ":")
    ).encode()
    return sha256(encoded).hexdigest()


def _valid_digest(value: str) -> bool:
    return len(value) == 64 and all(ch in _HEX for ch in value)


def _valid_subject(value: str) -> bool:
    try:
        repo, sha = value.rsplit("@", 1)
        return Subject(repo, sha).exact == value
    except (ValueError, Refusal):
        return False


@dataclass(frozen=True, slots=True)
class StateToken:
    revision: int
    digest: str

    def __post_init__(self) -> None:
        if self.revision < 1 or not _valid_digest(self.digest):
            raise Refusal("REFUSED_INVALID_STATE_TOKEN")


@dataclass(frozen=True, slots=True)
class PolicyState:
    subject: str
    revision: int
    policy_generation: int
    policy_digest: str
    frontier_digest: str
    selected_strategy: str | None
    standing: str
    drifted: bool
    blockers: tuple[str, ...]
    receipt_digest: str
    previous_digest: str | None = None
    digest: str = ""

    def body(self) -> dict:
        body = asdict(self)
        body.pop("digest")
        body["blockers"] = list(self.blockers)
        return body

    @property
    def token(self) -> StateToken:
        return StateToken(self.revision, self.digest)

    def verify(self) -> "PolicyState":
        if (
            not _valid_subject(self.subject)
            or self.revision < 1
            or self.policy_generation < 0
            or self.standing not in _ALLOWED_STANDING
            or self.selected_strategy not in (*STRATEGIES, None)
            or not _valid_digest(self.policy_digest)
            or not _valid_digest(self.frontier_digest)
            or not _valid_digest(self.receipt_digest)
            or (self.previous_digest is not None and not _valid_digest(self.previous_digest))
            or tuple(sorted(set(self.blockers))) != self.blockers
            or any(not isinstance(blocker, str) or not blocker for blocker in self.blockers)
            or not _valid_digest(self.digest)
            or _digest(self.body()) != self.digest
        ):
            raise Refusal("REFUSED_CORRUPT_POLICY_STATE")
        return self

    @classmethod
    def from_qualification(
        cls,
        subject: Subject,
        policy,
        frontier,
        qualification,
        expected: StateToken | None,
    ) -> "PolicyState":
        receipt = qualification.receipt
        expected_parent = expected.digest if expected else None
        if not replay(receipt):
            raise Refusal("REFUSED_INVALID_QUALIFICATION_RECEIPT")
        if (
            receipt.subject != subject.exact
            or receipt.policy_generation != policy.generation
            or receipt.policy_digest != policy.digest
            or receipt.frontier_digest != frontier.digest
            or receipt.selected_strategy != qualification.selected_strategy
            or receipt.standing != qualification.standing
            or receipt.parent != expected_parent
            or receipt.actuation_performed
            or receipt.authority != "SELECT"
        ):
            raise Refusal("REFUSED_QUALIFICATION_STATE_MISMATCH")
        revision = 1 if expected is None else expected.revision + 1
        state = cls(
            subject=subject.exact,
            revision=revision,
            policy_generation=policy.generation,
            policy_digest=policy.digest,
            frontier_digest=frontier.digest,
            selected_strategy=qualification.selected_strategy,
            standing=qualification.standing,
            drifted=bool(qualification.drifted),
            blockers=tuple(sorted(set(qualification.blockers))),
            receipt_digest=receipt.digest,
            previous_digest=expected_parent,
        )
        return replace(state, digest=_digest(state.body())).verify()


def verify_chain(states: Iterable[PolicyState]) -> tuple[PolicyState, ...]:
    ordered = tuple(states)
    previous: PolicyState | None = None
    for state in ordered:
        state.verify()
        if previous is None:
            if state.revision != 1 or state.previous_digest is not None:
                raise Refusal("REFUSED_BROKEN_STATE_CHAIN")
        elif (
            state.subject != previous.subject
            or state.revision != previous.revision + 1
            or state.previous_digest != previous.digest
            or state.policy_generation < previous.policy_generation
        ):
            raise Refusal("REFUSED_BROKEN_STATE_CHAIN")
        previous = state
    return ordered


class MemoryStateStore:
    """Process-local exact-subject CAS store with immutable audit history."""

    def __init__(self) -> None:
        self._current: dict[str, PolicyState] = {}
        self._history: dict[str, list[PolicyState]] = {}
        self._lock = RLock()

    def load(self, subject: Subject) -> PolicyState | None:
        with self._lock:
            state = self._current.get(subject.exact)
            return state.verify() if state else None

    def compare_and_swap(
        self, subject: Subject, expected: StateToken | None, candidate: PolicyState
    ) -> PolicyState:
        candidate.verify()
        if candidate.subject != subject.exact:
            raise Refusal("REFUSED_FOREIGN_POLICY_STATE")
        with self._lock:
            current = self._current.get(subject.exact)
            actual = current.token if current else None
            if current is not None and current.digest == candidate.digest:
                return current
            if actual != expected:
                raise Refusal("REFUSED_STALE_STATE_TOKEN")
            _admit_successor(expected, candidate, current)
            self._history.setdefault(subject.exact, []).append(candidate)
            self._current[subject.exact] = candidate
            return candidate

    def audit(self, subject: Subject) -> tuple[PolicyState, ...]:
        with self._lock:
            return verify_chain(tuple(self._history.get(subject.exact, ())))


class SQLiteStateStore:
    """Durable transactional CAS store with restart-safe immutable history."""

    def __init__(self, path: str | Path, *, timeout: float = 5.0) -> None:
        self.path = str(path)
        self.timeout = timeout
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS policy_state_current (
                    subject TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL,
                    digest TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS policy_state_history (
                    subject TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    digest TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    PRIMARY KEY(subject, revision)
                );
                """
            )

    @staticmethod
    def _encode(state: PolicyState) -> str:
        state.verify()
        return json.dumps(asdict(state), sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode(payload: str) -> PolicyState:
        try:
            raw = json.loads(payload)
            raw["blockers"] = tuple(raw.get("blockers", ()))
            return PolicyState(**raw).verify()
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            if isinstance(error, Refusal):
                raise
            raise Refusal("REFUSED_CORRUPT_POLICY_STATE") from error

    def load(self, subject: Subject) -> PolicyState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM policy_state_current WHERE subject=?",
                (subject.exact,),
            ).fetchone()
        return self._decode(row[0]) if row else None

    def compare_and_swap(
        self, subject: Subject, expected: StateToken | None, candidate: PolicyState
    ) -> PolicyState:
        candidate.verify()
        if candidate.subject != subject.exact:
            raise Refusal("REFUSED_FOREIGN_POLICY_STATE")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload FROM policy_state_current WHERE subject=?",
                (subject.exact,),
            ).fetchone()
            current = self._decode(row[0]) if row else None
            actual = current.token if current else None
            if current is not None and current.digest == candidate.digest:
                connection.rollback()
                return current
            if actual != expected:
                raise Refusal("REFUSED_STALE_STATE_TOKEN")
            _admit_successor(expected, candidate, current)
            payload = self._encode(candidate)
            connection.execute(
                "INSERT INTO policy_state_history(subject,revision,digest,payload) "
                "VALUES(?,?,?,?)",
                (subject.exact, candidate.revision, candidate.digest, payload),
            )
            connection.execute(
                "INSERT INTO policy_state_current(subject,revision,digest,payload) "
                "VALUES(?,?,?,?) ON CONFLICT(subject) DO UPDATE SET "
                "revision=excluded.revision,digest=excluded.digest,payload=excluded.payload",
                (subject.exact, candidate.revision, candidate.digest, payload),
            )
            connection.commit()
            return candidate
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def audit(self, subject: Subject) -> tuple[PolicyState, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM policy_state_history WHERE subject=? ORDER BY revision",
                (subject.exact,),
            ).fetchall()
        return verify_chain(tuple(self._decode(row[0]) for row in rows))


def _admit_successor(
    expected: StateToken | None,
    candidate: PolicyState,
    current: PolicyState | None,
) -> None:
    expected_revision = 1 if expected is None else expected.revision + 1
    expected_parent = None if expected is None else expected.digest
    if (
        candidate.revision != expected_revision
        or candidate.previous_digest != expected_parent
    ):
        raise Refusal("REFUSED_NON_SUCCESSOR_POLICY_STATE")
    if current is not None and candidate.policy_generation < current.policy_generation:
        raise Refusal("REFUSED_POLICY_GENERATION_ROLLBACK")
