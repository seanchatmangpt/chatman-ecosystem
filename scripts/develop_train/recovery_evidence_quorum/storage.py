from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random


class Store(str, Enum):
    MEMORY = "MEMORY"
    JSONL = "JSONL"
    SQLITE = "SQLITE"


@dataclass(frozen=True, slots=True)
class PersistenceNeed:
    durable: bool = False
    transactional: bool = False


def store_candidates() -> tuple[Store, ...]:
    return tuple(Store)


def select_store(need: PersistenceNeed) -> Store:
    if need.transactional:
        return Store.SQLITE
    if need.durable:
        return Store.JSONL
    return Store.MEMORY


def deterministic_failure_schedule(seed: int, probability: float, count: int) -> tuple[bool, ...]:
    if not 0 <= probability <= 1 or count < 0:
        raise ValueError("invalid failure model")
    rng = random.Random(seed)
    return tuple(rng.random() < probability for _ in range(count))
