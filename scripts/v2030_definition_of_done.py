#!/usr/bin/env python3
"""Executable v2030.1.1 definition-of-done reference court.

This module composes existing Chatman Ecosystem constitutional laws into one
bounded end-to-end transaction:

INTENT -> OBSERVE -> ADMIT O* -> PRESERVE DfCM FRONTIER -> SELECT -> CONSTRUCT
-> ADMIT/VERIFY -> AUTHORIZE -> BRCE DO -> OBSERVE POSTCONDITION -> RECEIPT
-> REPLAY -> STANDING

It is deliberately a control-plane reference implementation. It does not grant
ambient production authority and it does not claim that an in-memory test proves
an external provider boundary. External runtimes can supply their own actuator,
observer, and durable receipt store while preserving the same admission law.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_GRAPH = ROOT / "catalog" / "capabilities-decision-graph.toml"
TPCS_CONFIG = ROOT / "catalog" / "tpcs.toml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

STAGES = (
    "intent",
    "observe",
    "admit_o_star",
    "preserve_dfcm_frontier",
    "select",
    "construct",
    "admit_verify",
    "authorize",
    "brce_do",
    "observe_postcondition",
    "receipt",
    "replay",
    "standing",
)

REQUIRED_CAPABILITIES = {
    "capability:observe-exact-github-subject": "OBSERVE",
    "capability:admit-public-custom-ontology": "SELECT",
    "capability:plan-decision-frontier": "SELECT",
    "capability:falsify-candidate-plan": "SELECT",
    "capability:admit-capability-plan": "SELECT",
    "capability:manufacture-with-ggen": "CONSTRUCT",
    "capability:enforce-authority-ceiling": "SELECT",
    "capability:broker-consequential-do": "DO",
    "capability:replay-manufacture": "OBSERVE",
    "capability:attest-affidavit-standing": "CONSTRUCT",
}


class Refusal(RuntimeError):
    """Typed fail-closed outcome."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_toml(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def validate_repository_contract() -> None:
    """Bind the reference court to the admitted capability/TPCS control plane."""
    capabilities = load_toml(CAPABILITY_GRAPH).get("capability", [])
    by_id = {item.get("id"): item for item in capabilities}
    for capability_id, capability_class in REQUIRED_CAPABILITIES.items():
        item = by_id.get(capability_id)
        if item is None:
            raise Refusal(f"REFUSED_MISSING_CAPABILITY:{capability_id}")
        if item.get("class") != capability_class:
            raise Refusal(f"REFUSED_CAPABILITY_CLASS_DRIFT:{capability_id}")

    tpcs = load_toml(TPCS_CONFIG)
    if tpcs.get("mode") != "pull":
        raise Refusal("REFUSED_TPCS_NOT_PULL")
    if not tpcs.get("zero_unreceipted_actuation"):
        raise Refusal("REFUSED_UNRECEIPTED_ACTUATION_POLICY")
    if tpcs.get("acceptance_mutation_authority"):
        raise Refusal("REFUSED_ACCEPTANCE_MUTATION_AUTHORITY")


@dataclass(frozen=True)
class Candidate:
    id: str
    consequence: str
    reversible: bool
    cost_units: int = 0
    admitted: bool = True
    constraints_satisfied: bool = True
    falsified: bool = False
    evidence: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.id.startswith("candidate:") or len(self.id) <= len("candidate:"):
            raise Refusal("REFUSED_INVALID_CANDIDATE_ID")
        if not self.consequence.strip():
            raise Refusal(f"REFUSED_EMPTY_CONSEQUENCE:{self.id}")
        if self.cost_units < 0:
            raise Refusal(f"REFUSED_NEGATIVE_COST:{self.id}")


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    subject: str
    consequence: str
    scope: str
    authority: str = "DO"
    receipt_required: bool = True

    def validate(self, subject: str, consequence: str) -> None:
        if self.authority != "DO":
            raise Refusal("REFUSED_AUTHORITY_CLASS_MISMATCH")
        if self.subject != subject:
            raise Refusal("REFUSED_AUTHORITY_SUBJECT_MISMATCH")
        if self.consequence != consequence:
            raise Refusal("REFUSED_AUTHORITY_CONSEQUENCE_MISMATCH")
        if not self.scope.strip():
            raise Refusal("REFUSED_AUTHORITY_SCOPE_MISSING")
        if not self.receipt_required:
            raise Refusal("REFUSED_AUTHORITY_WITHOUT_RECEIPT")

    @property
    def digest(self) -> str:
        return canonical_digest(asdict(self))


@dataclass(frozen=True)
class DefinitionOfDoneRequest:
    subject: str
    intent: str
    observations: tuple[str, ...]
    candidates: tuple[Candidate, ...]
    selected_candidate: str
    authority: AuthorityGrant
    idempotency_key: str
    expected_precondition: str
    expected_postcondition: str
    verification_passed: bool
    verification_evidence: tuple[str, ...]


@dataclass
class ReceiptStore:
    """Minimal two-phase receipt-capability reference store.

    `reserve` executes before DO. An unavailable receipt path therefore refuses
    before actuation. `commit` seals the observed consequence after DO.
    """

    available: bool = True
    reservations: dict[str, str] = field(default_factory=dict)
    receipts: dict[str, dict] = field(default_factory=dict)

    def reserve(self, key: str, intent_digest: str) -> None:
        if not self.available:
            raise Refusal("REFUSED_RECEIPT_CAPABILITY_UNAVAILABLE")
        if not key.strip():
            raise Refusal("REFUSED_IDEMPOTENCY_KEY_MISSING")
        prior = self.reservations.get(key)
        if prior is not None and prior != intent_digest:
            raise Refusal("REFUSED_IDEMPOTENCY_CONFLICT")
        self.reservations[key] = intent_digest

    def commit(self, key: str, payload: dict) -> dict:
        expected_intent = self.reservations.get(key)
        if expected_intent is None:
            raise Refusal("REFUSED_RECEIPT_WITHOUT_RESERVATION")
        if payload.get("intent_digest") != expected_intent:
            raise Refusal("REFUSED_RECEIPT_INTENT_DRIFT")
        unsigned = dict(payload)
        unsigned.pop("digest", None)
        receipt = {**unsigned, "digest": canonical_digest(unsigned)}
        prior = self.receipts.get(key)
        if prior is not None and prior != receipt:
            raise Refusal("REFUSED_RECEIPT_REWRITE")
        self.receipts[key] = receipt
        return receipt

    def verify(self, receipt: dict) -> None:
        unsigned = dict(receipt)
        digest = unsigned.pop("digest", None)
        if digest != canonical_digest(unsigned):
            raise Refusal("REFUSED_RECEIPT_TAMPERED")
        key = receipt.get("idempotency_key")
        if not isinstance(key, str) or self.receipts.get(key) != receipt:
            raise Refusal("REFUSED_RECEIPT_NOT_PERSISTED")


@dataclass
class MemoryWorld:
    """Bounded executable subject used by the reference self-test only."""

    state: str
    actuation_count: int = 0

    def observe(self) -> str:
        return self.state

    def actuate(self, consequence: str) -> str:
        self.actuation_count += 1
        self.state = consequence
        return self.state


def admit_observation(request: DefinitionOfDoneRequest) -> dict:
    if not SHA40.fullmatch(request.subject):
        raise Refusal("REFUSED_INVALID_SUBJECT")
    if not request.intent.strip():
        raise Refusal("REFUSED_EMPTY_INTENT")
    facts = sorted({item.strip() for item in request.observations if item.strip()})
    if not facts:
        raise Refusal("REFUSED_EMPTY_OBSERVATION")
    admitted = {"subject": request.subject, "facts": facts}
    return {**admitted, "digest": canonical_digest(admitted)}


def preserve_dfcm_frontier(candidates: tuple[Candidate, ...]) -> tuple[list[Candidate], dict[str, str]]:
    """Preserve every reversible lawful candidate; exclusions remain topology."""
    seen: set[str] = set()
    frontier: list[Candidate] = []
    excluded: dict[str, str] = {}
    for candidate in candidates:
        candidate.validate()
        if candidate.id in seen:
            raise Refusal(f"REFUSED_DUPLICATE_CANDIDATE:{candidate.id}")
        seen.add(candidate.id)
        if not candidate.reversible:
            excluded[candidate.id] = "EXCLUDED_IRREVERSIBLE"
        elif not candidate.admitted:
            excluded[candidate.id] = "EXCLUDED_NOT_ADMITTED"
        elif not candidate.constraints_satisfied:
            excluded[candidate.id] = "EXCLUDED_CONSTRAINT"
        elif candidate.falsified:
            excluded[candidate.id] = "EXCLUDED_FALSIFIED"
        else:
            frontier.append(candidate)
    frontier.sort(key=lambda item: (item.cost_units, item.id))
    if not frontier:
        raise Refusal("REFUSED_NO_LAWFUL_FRONTIER")
    return frontier, excluded


def select_candidate(frontier: list[Candidate], selected_id: str) -> Candidate:
    for candidate in frontier:
        if candidate.id == selected_id:
            return candidate
    raise Refusal("REFUSED_SELECTION_OUTSIDE_FRONTIER")


def construct_intent(subject: str, o_star: dict, candidate: Candidate) -> dict:
    payload = {
        "kind": "bounded-consequence-intent",
        "subject": subject,
        "o_star": o_star["digest"],
        "candidate": candidate.id,
        "consequence": candidate.consequence,
        "evidence": list(candidate.evidence),
    }
    return {**payload, "digest": canonical_digest(payload)}


def admit_verification(request: DefinitionOfDoneRequest, artifact: dict) -> dict:
    if not request.verification_passed:
        raise Refusal("REFUSED_VERIFICATION_FAILED")
    evidence = sorted({item.strip() for item in request.verification_evidence if item.strip()})
    if not evidence:
        raise Refusal("REFUSED_VERIFICATION_EVIDENCE_MISSING")
    payload = {"artifact": artifact["digest"], "evidence": evidence, "passed": True}
    return {**payload, "digest": canonical_digest(payload)}


def intent_digest(
    request: DefinitionOfDoneRequest,
    o_star: dict,
    frontier: list[Candidate],
    artifact: dict,
    verification: dict,
    selected: Candidate,
) -> str:
    return canonical_digest(
        {
            "subject": request.subject,
            "intent": request.intent,
            "o_star": o_star["digest"],
            "frontier": [item.id for item in frontier],
            "selected": selected.id,
            "artifact": artifact["digest"],
            "verification": verification["digest"],
            "authority": request.authority.digest,
            "expected_precondition": request.expected_precondition,
            "expected_postcondition": request.expected_postcondition,
        }
    )


def brce_do(
    request: DefinitionOfDoneRequest,
    selected: Candidate,
    o_star: dict,
    frontier: list[Candidate],
    excluded: dict[str, str],
    artifact: dict,
    verification: dict,
    store: ReceiptStore,
    actuator: Callable[[str], str],
    observer: Callable[[], str],
) -> dict:
    """Exclusive consequential path with pre-reserved receipt capability."""
    request.authority.validate(request.subject, selected.consequence)
    digest = intent_digest(request, o_star, frontier, artifact, verification, selected)
    store.reserve(request.idempotency_key, digest)

    prior = store.receipts.get(request.idempotency_key)
    if prior is not None:
        store.verify(prior)
        if prior.get("intent_digest") != digest:
            raise Refusal("REFUSED_REPLAY_IDENTITY_DRIFT")
        return prior

    before = observer()
    if before != request.expected_precondition:
        raise Refusal("REFUSED_PRECONDITION_MISMATCH")

    execution_error: str | None = None
    try:
        actuator(selected.consequence)
    except Exception as exc:  # external adapters are allowed to fail; failure must still be receipted
        execution_error = f"{type(exc).__name__}:{exc}"

    after = observer()
    postcondition_ok = execution_error is None and after == request.expected_postcondition
    outcome = "succeeded" if postcondition_ok else "blocked"
    payload = {
        "version": "v2030.1.1",
        "subject": request.subject,
        "idempotency_key": request.idempotency_key,
        "intent_digest": digest,
        "o_star": o_star["digest"],
        "frontier": [item.id for item in frontier],
        "excluded": excluded,
        "selected_candidate": selected.id,
        "artifact": artifact["digest"],
        "verification": verification["digest"],
        "authority": request.authority.digest,
        "precondition": before,
        "requested_consequence": selected.consequence,
        "observed_postcondition": after,
        "expected_postcondition": request.expected_postcondition,
        "postcondition_verified": postcondition_ok,
        "execution_error": execution_error,
        "outcome": outcome,
        "replay_class": "deterministic_receipt_verification_no_reactuation",
    }
    return store.commit(request.idempotency_key, payload)


def replay(receipt: dict, store: ReceiptStore) -> str:
    """Verify persisted consequence evidence without calling an actuator."""
    store.verify(receipt)
    if receipt.get("replay_class") != "deterministic_receipt_verification_no_reactuation":
        raise Refusal("REFUSED_REPLAY_CLASS_UNSUPPORTED")
    return "REPLAY_MATCH"


def run(
    request: DefinitionOfDoneRequest,
    store: ReceiptStore,
    actuator: Callable[[str], str],
    observer: Callable[[], str],
) -> dict:
    """Execute the complete bounded v2030.1.1 DoD loop."""
    validate_repository_contract()
    o_star = admit_observation(request)
    frontier, excluded = preserve_dfcm_frontier(request.candidates)
    selected = select_candidate(frontier, request.selected_candidate)
    artifact = construct_intent(request.subject, o_star, selected)
    verification = admit_verification(request, artifact)
    receipt = brce_do(
        request,
        selected,
        o_star,
        frontier,
        excluded,
        artifact,
        verification,
        store,
        actuator,
        observer,
    )
    replay_status = replay(receipt, store)
    standing = "ALIVE" if receipt["outcome"] == "succeeded" and replay_status == "REPLAY_MATCH" else "BLOCKED"
    return {
        "version": "v2030.1.1",
        "subject": request.subject,
        "stages": list(STAGES),
        "o_star": o_star["digest"],
        "frontier": [item.id for item in frontier],
        "excluded": excluded,
        "selected": selected.id,
        "artifact": artifact["digest"],
        "verification": verification["digest"],
        "authority": request.authority.digest,
        "receipt": receipt["digest"],
        "replay": replay_status,
        "standing": standing,
    }


def reference_request(subject: str = "a" * 40) -> DefinitionOfDoneRequest:
    candidates = (
        Candidate("candidate:portable-a", "deployed", True, cost_units=30, evidence=("fixture:a",)),
        Candidate("candidate:portable-b", "deployed", True, cost_units=20, evidence=("fixture:b",)),
        Candidate("candidate:blocked-edge", "deployed", True, cost_units=10, constraints_satisfied=False),
        Candidate("candidate:irreversible-edge", "deployed", False, cost_units=1),
    )
    return DefinitionOfDoneRequest(
        subject=subject,
        intent="apply one bounded verified consequence",
        observations=("world.state=planned", "receipt.capability=available"),
        candidates=candidates,
        selected_candidate="candidate:portable-b",
        authority=AuthorityGrant(
            grant_id="authority:reference-do",
            subject=subject,
            consequence="deployed",
            scope="memory-world/reference",
        ),
        idempotency_key="v2030-reference-1",
        expected_precondition="planned",
        expected_postcondition="deployed",
        verification_passed=True,
        verification_evidence=("reference-verifier:passed",),
    )


def self_test() -> dict:
    world = MemoryWorld("planned")
    store = ReceiptStore()
    request = reference_request()
    result = run(request, store, world.actuate, world.observe)
    if result["standing"] != "ALIVE":
        raise AssertionError(result)
    if result["frontier"] != ["candidate:portable-b", "candidate:portable-a"]:
        raise AssertionError("DfCM frontier was not preserved")
    if result["excluded"].get("candidate:blocked-edge") != "EXCLUDED_CONSTRAINT":
        raise AssertionError("constraint exclusion missing")
    if world.actuation_count != 1:
        raise AssertionError("expected exactly one actuation")

    replayed = run(request, store, world.actuate, world.observe)
    if replayed["receipt"] != result["receipt"] or world.actuation_count != 1:
        raise AssertionError("idempotent replay re-actuated or changed receipt")

    blocked_world = MemoryWorld("planned")
    try:
        run(reference_request("b" * 40), ReceiptStore(available=False), blocked_world.actuate, blocked_world.observe)
    except Refusal as exc:
        if exc.code != "REFUSED_RECEIPT_CAPABILITY_UNAVAILABLE":
            raise
    else:
        raise AssertionError("missing receipt capability was not refused")
    if blocked_world.actuation_count != 0:
        raise AssertionError("actuation occurred without receipt capability")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Chatman Ecosystem v2030.1.1 executable definition-of-done court")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("--self-test is required; external DO adapters must be integrated by an owning runtime")
    result = self_test()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("V2030_DEFINITION_OF_DONE_ALIVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
