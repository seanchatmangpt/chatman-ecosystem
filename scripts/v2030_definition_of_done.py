#!/usr/bin/env python3
"""v2030.1.1 end-to-end consequence court over the canonical DFCM finisher.

PR #40 owns release-graph Definition of Done, DFCM repair selection, exact BRCE
admission, receipt chaining, and deterministic replay. This module does not
replace that engine. It extends it across the remaining v2030 product boundary:

INTENT -> OBSERVE -> ADMIT O* -> PRESERVE ACTION FRONTIER -> SELECT -> CONSTRUCT
-> ADMIT/VERIFY -> [external exact authority] -> BRCE DO -> OBSERVE POSTCONDITION
-> RECEIPT -> REPLAY -> STANDING

`prepare()` is SELECT/CONSTRUCT only and cannot actuate. The caller must supply
an independently created exact grant for the prepared intent digest before
`execute()` can cross the BRCE boundary. Receipt capability is reserved before
actuation, and replay never calls the actuator.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
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


def _load_dfcm_module():
    path = Path(__file__).with_name("dfcm_autonomic_finish.py")
    spec = importlib.util.spec_from_file_location("chatman_dfcm_autonomic_finish", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load canonical DFCM finisher")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dfcm = _load_dfcm_module()


class Refusal(RuntimeError):
    """Typed fail-closed outcome for the v2030 consequence boundary."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def digest(value: object) -> str:
    """Use the canonical DFCM finisher's deterministic digest."""
    return dfcm.digest(value)


def load_toml(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def validate_repository_contract() -> None:
    """Bind this extension to current capability/TPCS and PR #40 ownership."""
    for name in ("definition_of_done", "frontier", "admit_do", "receipt", "replay_receipts"):
        if not callable(getattr(dfcm, name, None)):
            raise Refusal(f"REFUSED_DFCM_OWNER_MISSING:{name}")

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
class DefinitionOfDoneRequest:
    subject: str
    intent: str
    observations: tuple[str, ...]
    candidates: tuple[Candidate, ...]
    selected_candidate: str
    idempotency_key: str
    expected_precondition: str
    expected_postcondition: str
    verification_passed: bool
    verification_evidence: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityGrant:
    """Exact external grant. The runner never manufactures this object."""

    authority_id: str
    subject_sha: str
    intent_digest: str
    consequence: str
    scope: str = "BRCE:VERIFY_REPAIR_ONLY"
    expires_at: str = "bounded-reference-window"

    def as_broker_grant(self) -> dict[str, str]:
        return {
            "authority_id": self.authority_id,
            "subject_sha": self.subject_sha,
            "intent_digest": self.intent_digest,
            "scope": self.scope,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True)
class PreparedExecution:
    request: DefinitionOfDoneRequest
    o_star: dict
    frontier: tuple[Candidate, ...]
    excluded: dict[str, str]
    selected: Candidate
    artifact: dict
    verification: dict
    intent: dict


@dataclass
class ReceiptStore:
    """Two-phase receipt capability.

    Reservation occurs before DO. If reservation is impossible, the actuator is
    never called. Final receipt sealing delegates to PR #40's canonical receipt
    implementation and replay court.
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

    def commit(self, key: str, event: dict) -> dict:
        expected_intent = self.reservations.get(key)
        if expected_intent is None:
            raise Refusal("REFUSED_RECEIPT_WITHOUT_RESERVATION")
        if event.get("intent_digest") != expected_intent:
            raise Refusal("REFUSED_RECEIPT_INTENT_DRIFT")
        envelope = dfcm.receipt(event)
        stored = {
            "idempotency_key": key,
            "intent_digest": expected_intent,
            "envelope": envelope,
        }
        prior = self.receipts.get(key)
        if prior is not None and prior != stored:
            raise Refusal("REFUSED_RECEIPT_REWRITE")
        self.receipts[key] = stored
        return stored

    def verify(self, stored: dict) -> str:
        key = stored.get("idempotency_key")
        if not isinstance(key, str) or self.receipts.get(key) != stored:
            raise Refusal("REFUSED_RECEIPT_NOT_PERSISTED")
        if stored.get("intent_digest") != self.reservations.get(key):
            raise Refusal("REFUSED_RECEIPT_RESERVATION_DRIFT")
        try:
            return dfcm.replay_receipts([stored["envelope"]])
        except (KeyError, dfcm.Refusal) as exc:
            raise Refusal("REFUSED_RECEIPT_TAMPERED") from exc


@dataclass
class MemoryWorld:
    """Bounded subject used only by the exact executable reference fixture."""

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
    return {**admitted, "digest": digest(admitted)}


def preserve_action_frontier(candidates: tuple[Candidate, ...]) -> tuple[list[Candidate], dict[str, str]]:
    """Preserve every reversible lawful action edge; exclusions remain topology."""
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
    return {**payload, "digest": digest(payload)}


def admit_verification(request: DefinitionOfDoneRequest, artifact: dict) -> dict:
    if not request.verification_passed:
        raise Refusal("REFUSED_VERIFICATION_FAILED")
    evidence = sorted({item.strip() for item in request.verification_evidence if item.strip()})
    if not evidence:
        raise Refusal("REFUSED_VERIFICATION_EVIDENCE_MISSING")
    payload = {"artifact": artifact["digest"], "evidence": evidence, "passed": True}
    return {**payload, "digest": digest(payload)}


def prepare(request: DefinitionOfDoneRequest) -> PreparedExecution:
    """SELECT/CONSTRUCT-only half. No authority object is accepted or created."""
    validate_repository_contract()
    o_star = admit_observation(request)
    frontier, excluded = preserve_action_frontier(request.candidates)
    selected = select_candidate(frontier, request.selected_candidate)
    artifact = construct_intent(request.subject, o_star, selected)
    verification = admit_verification(request, artifact)
    intent = {
        "schema": "urn:chatman:v2030:consequence-intent:v1",
        "subject": {
            "component": selected.id,
            "repository": "seanchatmangpt/chatman-ecosystem",
            "ref": "exact-subject",
            "sha": request.subject,
        },
        "consequence": selected.consequence,
        "o_star": o_star["digest"],
        "frontier": [item.id for item in frontier],
        "excluded": excluded,
        "artifact": artifact["digest"],
        "verification": verification["digest"],
        "expected_precondition": request.expected_precondition,
        "expected_postcondition": request.expected_postcondition,
    }
    intent["intent_digest"] = digest(intent)
    return PreparedExecution(
        request=request,
        o_star=o_star,
        frontier=tuple(frontier),
        excluded=excluded,
        selected=selected,
        artifact=artifact,
        verification=verification,
        intent=intent,
    )


def execute(
    prepared: PreparedExecution,
    grant: AuthorityGrant,
    store: ReceiptStore,
    actuator: Callable[[str], str],
    observer: Callable[[], str],
) -> dict:
    """Cross the canonical BRCE admission, actuate once, observe, receipt, replay."""
    request = prepared.request
    selected = prepared.selected
    if grant.consequence != selected.consequence:
        raise Refusal("REFUSED_AUTHORITY_CONSEQUENCE_MISMATCH")
    try:
        broker_admission = dfcm.admit_do(prepared.intent, grant.as_broker_grant())
    except dfcm.Refusal as exc:
        raise Refusal(f"REFUSED_DFCM_{exc.code}") from exc

    store.reserve(request.idempotency_key, prepared.intent["intent_digest"])
    prior = store.receipts.get(request.idempotency_key)
    if prior is not None:
        replay_status = store.verify(prior)
        return _result(prepared, prior, replay_status)

    before = observer()
    if before != request.expected_precondition:
        raise Refusal("REFUSED_PRECONDITION_MISMATCH")

    execution_error: str | None = None
    try:
        actuator(selected.consequence)
    except Exception as exc:  # external failure is evidence and must still be receipted
        execution_error = f"{type(exc).__name__}:{exc}"

    after = observer()
    postcondition_ok = execution_error is None and after == request.expected_postcondition
    event = {
        "version": "v2030.1.1",
        "phase": "BRCE_CONSEQUENCE",
        "subject": request.subject,
        "intent_digest": prepared.intent["intent_digest"],
        "o_star": prepared.o_star["digest"],
        "frontier": [item.id for item in prepared.frontier],
        "excluded": prepared.excluded,
        "selected_candidate": selected.id,
        "artifact": prepared.artifact["digest"],
        "verification": prepared.verification["digest"],
        "broker_admission": broker_admission,
        "precondition": before,
        "requested_consequence": selected.consequence,
        "observed_postcondition": after,
        "expected_postcondition": request.expected_postcondition,
        "postcondition_verified": postcondition_ok,
        "execution_error": execution_error,
        "outcome": "succeeded" if postcondition_ok else "blocked",
        "replay_class": "canonical_dfcm_receipt_no_reactuation",
    }
    stored = store.commit(request.idempotency_key, event)
    replay_status = store.verify(stored)
    return _result(prepared, stored, replay_status)


def _result(prepared: PreparedExecution, stored: dict, replay_status: str) -> dict:
    event = stored["envelope"]["event"]
    standing = "ALIVE" if event["outcome"] == "succeeded" and replay_status.startswith("ALIVE:REPLAY:") else "BLOCKED"
    return {
        "version": "v2030.1.1",
        "subject": prepared.request.subject,
        "stages": list(STAGES),
        "o_star": prepared.o_star["digest"],
        "frontier": [item.id for item in prepared.frontier],
        "excluded": prepared.excluded,
        "selected": prepared.selected.id,
        "artifact": prepared.artifact["digest"],
        "verification": prepared.verification["digest"],
        "authority_id": event["broker_admission"]["authority_id"],
        "intent_digest": prepared.intent["intent_digest"],
        "receipt": stored["envelope"]["receipt_digest"],
        "replay": replay_status,
        "standing": standing,
    }


def reference_request(subject: str = "a" * 40) -> DefinitionOfDoneRequest:
    return DefinitionOfDoneRequest(
        subject=subject,
        intent="apply one bounded verified consequence",
        observations=("world.state=planned", "receipt.capability=available"),
        candidates=(
            Candidate("candidate:portable-a", "deployed", True, cost_units=30, evidence=("fixture:a",)),
            Candidate("candidate:portable-b", "deployed", True, cost_units=20, evidence=("fixture:b",)),
            Candidate("candidate:blocked-edge", "deployed", True, cost_units=10, constraints_satisfied=False),
            Candidate("candidate:irreversible-edge", "deployed", False, cost_units=1),
        ),
        selected_candidate="candidate:portable-b",
        idempotency_key="v2030-reference-1",
        expected_precondition="planned",
        expected_postcondition="deployed",
        verification_passed=True,
        verification_evidence=("reference-verifier:passed",),
    )


def reference_grant(prepared: PreparedExecution) -> AuthorityGrant:
    """External-authority fixture used only by tests/self-test, never by execute()."""
    return AuthorityGrant(
        authority_id="authority:reference-do",
        subject_sha=prepared.request.subject,
        intent_digest=prepared.intent["intent_digest"],
        consequence=prepared.selected.consequence,
    )


def self_test() -> dict:
    request = reference_request()
    prepared = prepare(request)
    grant = reference_grant(prepared)
    world = MemoryWorld("planned")
    store = ReceiptStore()
    result = execute(prepared, grant, store, world.actuate, world.observe)
    if result["standing"] != "ALIVE":
        raise AssertionError(result)
    if result["frontier"] != ["candidate:portable-b", "candidate:portable-a"]:
        raise AssertionError("action frontier was not preserved")
    if result["excluded"].get("candidate:blocked-edge") != "EXCLUDED_CONSTRAINT":
        raise AssertionError("constraint exclusion missing")
    if world.actuation_count != 1:
        raise AssertionError("expected exactly one actuation")

    replayed = execute(prepared, grant, store, world.actuate, world.observe)
    if replayed["receipt"] != result["receipt"] or world.actuation_count != 1:
        raise AssertionError("idempotent replay re-actuated or changed receipt")

    blocked_request = reference_request("b" * 40)
    blocked_prepared = prepare(blocked_request)
    blocked_grant = reference_grant(blocked_prepared)
    blocked_world = MemoryWorld("planned")
    try:
        execute(
            blocked_prepared,
            blocked_grant,
            ReceiptStore(available=False),
            blocked_world.actuate,
            blocked_world.observe,
        )
    except Refusal as exc:
        if exc.code != "REFUSED_RECEIPT_CAPABILITY_UNAVAILABLE":
            raise
    else:
        raise AssertionError("missing receipt capability was not refused")
    if blocked_world.actuation_count != 0:
        raise AssertionError("actuation occurred without receipt capability")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Chatman Ecosystem v2030.1.1 executable consequence court")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("--self-test is required; external DO adapters belong to an owning runtime")
    result = self_test()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("V2030_DEFINITION_OF_DONE_ALIVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
