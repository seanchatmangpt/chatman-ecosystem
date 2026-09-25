from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Iterable

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_RECEIPT_SCHEMA = "https://chatman.dev/hilt-court/receipt/v1"
_INADMISSIBLE_SCHEMA = "https://chatman.dev/hilt-court/inadmissible-case/v1"
_CLAIM_CEILING = "INSTITUTIONAL_ADMISSION_ONLY"


class Standing(str, Enum):
    ALIVE = "ALIVE"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"


class ActorKind(str, Enum):
    HUMAN = "HUMAN"
    NON_HUMAN = "NON_HUMAN"


class ArtifactState(str, Enum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"


class InteractionMode(str, Enum):
    REACTIVE = "REACTIVE"
    PROACTIVE = "PROACTIVE"


class AgencyLevel(IntEnum):
    OBSERVE = 0
    SELECT = 1
    CONSTRUCT = 2
    REQUEST_DO = 3
    PROACTIVE_SELECT = 4
    PROACTIVE_CONSTRUCT = 5
    BOUNDED_DELEGATED_DO = 6

    @property
    def label(self) -> str:
        return (
            "A0_OBSERVE",
            "A1_SELECT",
            "A2_CONSTRUCT",
            "A3_REQUEST_DO",
            "A4_PROACTIVE_SELECT",
            "A5_PROACTIVE_CONSTRUCT",
            "A6_BOUNDED_DELEGATED_DO",
        )[int(self)]


class Operation(str, Enum):
    READ = "READ"
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    DISCLOSE = "DISCLOSE"
    NOTIFY = "NOTIFY"
    RESPOND = "RESPOND"
    ASSIGN = "ASSIGN"
    SCHEDULE = "SCHEDULE"
    CLAIM_RESPONSIBILITY = "CLAIM_RESPONSIBILITY"
    EXECUTE = "EXECUTE"


CONSEQUENTIAL_OPERATIONS = frozenset(
    {
        Operation.DISCLOSE,
        Operation.NOTIFY,
        Operation.RESPOND,
        Operation.ASSIGN,
        Operation.SCHEDULE,
        Operation.CLAIM_RESPONSIBILITY,
        Operation.EXECUTE,
    }
)


@dataclass(frozen=True, slots=True)
class SubjectBinding:
    repository: str
    subject_sha: str

    def __post_init__(self) -> None:
        if "/" not in self.repository or self.repository.startswith("/"):
            raise ValueError("repository must be owner/name")
        if not _SHA40.fullmatch(self.subject_sha):
            raise ValueError("subject_sha must be exact 40-hex identity")

    @property
    def identity(self) -> str:
        return f"{self.repository}@{self.subject_sha}"


@dataclass(frozen=True, slots=True)
class ActorContract:
    actor_id: str
    actor_kind: ActorKind
    accountability_principal: str

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("actor_id must be non-empty")
        if not self.accountability_principal.strip():
            raise ValueError("accountability_principal must be non-empty")


@dataclass(frozen=True, slots=True)
class ArtifactStanding:
    artifact_id: str
    state: ArtifactState
    provenance: str

    def __post_init__(self) -> None:
        if not self.artifact_id.strip() or not self.provenance.strip():
            raise ValueError("artifact id/provenance must be non-empty")


@dataclass(frozen=True, slots=True)
class AgencyLease:
    capability: str
    context: str
    max_level: AgencyLevel
    evidence_id: str

    def __post_init__(self) -> None:
        if not self.capability.strip() or not self.context.strip():
            raise ValueError("agency lease capability/context must be non-empty")
        if not self.evidence_id.strip():
            raise ValueError("agency lease evidence_id must be non-empty")

    @property
    def key(self) -> tuple[str, str]:
        return (self.capability, self.context)


@dataclass(frozen=True, slots=True)
class ContextPermission:
    context: str
    operations: tuple[Operation, ...]
    read_artifacts: tuple[str, ...] = ()
    disclose_artifacts: tuple[str, ...] = ()
    surfaces: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.context.strip():
            raise ValueError("permission context must be non-empty")
        _require_unique("permission operations", self.operations)
        _require_unique("read_artifacts", self.read_artifacts)
        _require_unique("disclose_artifacts", self.disclose_artifacts)
        _require_unique("surfaces", self.surfaces)


@dataclass(frozen=True, slots=True)
class RelationContract:
    relation_id: str
    relation_kind: str
    allowed_operations: tuple[Operation, ...]

    def __post_init__(self) -> None:
        if not self.relation_id.strip() or not self.relation_kind.strip():
            raise ValueError("relation contract id/kind must be non-empty")
        _require_unique("relation allowed_operations", self.allowed_operations)


@dataclass(frozen=True, slots=True)
class HumanReservation:
    capability: str
    context: str
    operation: Operation
    reservation_id: str
    surface: str | None = None

    def __post_init__(self) -> None:
        if not self.capability.strip() or not self.context.strip():
            raise ValueError("human reservation capability/context must be non-empty")
        if not self.reservation_id.strip():
            raise ValueError("human reservation id must be non-empty")


@dataclass(frozen=True, slots=True)
class ActionCandidate:
    action_id: str
    actor_id: str
    capability: str
    context: str
    operation: Operation
    requested_agency: AgencyLevel
    interaction_mode: InteractionMode
    consequence_class: str
    artifact_id: str | None = None
    relation_id: str | None = None
    surface: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("action_id", self.action_id),
            ("actor_id", self.actor_id),
            ("capability", self.capability),
            ("context", self.context),
            ("consequence_class", self.consequence_class),
        ):
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class HiltCase:
    case_id: str
    semantic_subject_id: str
    subjects: tuple[SubjectBinding, ...]
    actor: ActorContract
    artifacts: tuple[ArtifactStanding, ...]
    agency_leases: tuple[AgencyLease, ...]
    permissions: tuple[ContextPermission, ...]
    relations: tuple[RelationContract, ...]
    human_reservations: tuple[HumanReservation, ...]
    action: ActionCandidate

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.semantic_subject_id.strip():
            raise ValueError("case_id and semantic_subject_id must be non-empty")
        if not self.subjects:
            raise ValueError("subjects must be non-empty")
        if self.action.actor_id != self.actor.actor_id:
            raise ValueError("action actor_id must match actor contract")
        _require_unique("subject identities", (x.identity for x in self.subjects))
        _require_unique("subject repositories", (x.repository for x in self.subjects))
        _require_unique("artifact ids", (x.artifact_id for x in self.artifacts))
        _require_unique("agency lease keys", (x.key for x in self.agency_leases))
        _require_unique("permission contexts", (x.context for x in self.permissions))
        _require_unique("relation ids", (x.relation_id for x in self.relations))
        _require_unique(
            "human reservation ids", (x.reservation_id for x in self.human_reservations)
        )


@dataclass(frozen=True, slots=True)
class HiltReceipt:
    schema: str
    case_id: str
    semantic_subject_id: str
    subject_bindings: tuple[str, ...]
    action_id: str
    actor_id: str
    standing: Standing
    claim_ceiling: str
    authority: str
    accountability_principal: str
    admitted_agency: str | None
    operation: str
    downstream: str
    responsibility_claim: bool
    refusals: tuple[str, ...]
    receipt_digest: str

    def canonical_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_digest", None)
        payload["standing"] = self.standing.value
        return payload


def _require_unique(name: str, values: Iterable[object]) -> None:
    items = tuple(values)
    if len(items) != len(set(items)):
        raise ValueError(f"{name} must be unique")


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _operation_minimum(action: ActionCandidate) -> AgencyLevel:
    if action.operation is Operation.READ:
        return AgencyLevel.OBSERVE
    if action.operation is Operation.SELECT:
        return (
            AgencyLevel.PROACTIVE_SELECT
            if action.interaction_mode is InteractionMode.PROACTIVE
            else AgencyLevel.SELECT
        )
    if action.operation is Operation.CONSTRUCT:
        return (
            AgencyLevel.PROACTIVE_CONSTRUCT
            if action.interaction_mode is InteractionMode.PROACTIVE
            else AgencyLevel.CONSTRUCT
        )
    if action.operation in CONSEQUENTIAL_OPERATIONS:
        return (
            AgencyLevel.BOUNDED_DELEGATED_DO
            if action.interaction_mode is InteractionMode.PROACTIVE
            else AgencyLevel.REQUEST_DO
        )
    raise AssertionError(f"unhandled operation {action.operation}")


def evaluate(case: HiltCase) -> HiltReceipt:
    action = case.action
    refusals: list[str] = []
    artifacts = {x.artifact_id: x for x in case.artifacts}
    leases = {x.key: x for x in case.agency_leases}
    permissions = {x.context: x for x in case.permissions}
    relations = {x.relation_id: x for x in case.relations}

    permission = permissions.get(action.context)
    if permission is None:
        refusals.append(f"BLOCKED:CONTEXT_PERMISSION_MISSING:{action.context}")
    elif action.operation not in permission.operations:
        refusals.append(
            f"REFUSED:OPERATION_NOT_PERMITTED:{action.context}:{action.operation.value}"
        )

    lease = leases.get((action.capability, action.context))
    admitted_agency: AgencyLevel | None = None
    if lease is None:
        refusals.append(
            f"BLOCKED:AGENCY_LEASE_MISSING:{action.capability}:{action.context}"
        )
    elif action.requested_agency > lease.max_level:
        refusals.append(
            "REFUSED:AGENCY_EXCEEDS_LEASE:"
            f"{action.capability}:{action.context}:"
            f"requested={action.requested_agency.label}:max={lease.max_level.label}"
        )
    else:
        admitted_agency = action.requested_agency

    minimum = _operation_minimum(action)
    if action.requested_agency < minimum:
        refusals.append(
            "REFUSED:AGENCY_BELOW_OPERATION_MINIMUM:"
            f"{action.operation.value}:"
            f"requested={action.requested_agency.label}:required={minimum.label}"
        )

    if action.artifact_id is not None:
        artifact = artifacts.get(action.artifact_id)
        if artifact is None:
            refusals.append(f"BLOCKED:ARTIFACT_STANDING_MISSING:{action.artifact_id}")
        elif artifact.state is ArtifactState.SUPERSEDED:
            refusals.append(f"REFUSED:SUPERSEDED_ARTIFACT:{action.artifact_id}")
        elif artifact.state is ArtifactState.UNKNOWN:
            refusals.append(f"BLOCKED:ARTIFACT_STANDING_UNKNOWN:{action.artifact_id}")

        if permission is not None and action.operation is Operation.READ:
            if action.artifact_id not in permission.read_artifacts:
                refusals.append(f"REFUSED:READ_NOT_PERMITTED:{action.artifact_id}")
        if permission is not None and action.operation is Operation.DISCLOSE:
            if action.artifact_id not in permission.disclose_artifacts:
                refusals.append(
                    f"REFUSED:DISCLOSE_NOT_PERMITTED:{action.artifact_id}"
                )

    if action.surface is not None and permission is not None:
        if action.surface not in permission.surfaces:
            refusals.append(f"REFUSED:SURFACE_NOT_PERMITTED:{action.surface}")

    relation_bound = {
        Operation.NOTIFY,
        Operation.RESPOND,
        Operation.ASSIGN,
        Operation.CLAIM_RESPONSIBILITY,
    }
    if action.operation in relation_bound:
        if action.relation_id is None:
            refusals.append(f"BLOCKED:RELATION_REQUIRED:{action.operation.value}")
        else:
            relation = relations.get(action.relation_id)
            if relation is None:
                refusals.append(
                    f"BLOCKED:RELATION_CONTRACT_MISSING:{action.relation_id}"
                )
            elif action.operation not in relation.allowed_operations:
                refusals.append(
                    "REFUSED:RELATION_OPERATION_NOT_GRANTED:"
                    f"{action.relation_id}:{action.operation.value}"
                )

    for reservation in case.human_reservations:
        if (
            reservation.capability == action.capability
            and reservation.context == action.context
            and reservation.operation is action.operation
            and (reservation.surface is None or reservation.surface == action.surface)
        ):
            refusals.append(f"REFUSED:HUMAN_RESERVED:{reservation.reservation_id}")

    if any(x.startswith("REFUSED:") for x in refusals):
        standing = Standing.REFUSED
    elif any(x.startswith("BLOCKED:") for x in refusals):
        standing = Standing.BLOCKED
    else:
        standing = Standing.ALIVE

    responsibility_claim = (
        standing is Standing.ALIVE
        and action.operation is Operation.CLAIM_RESPONSIBILITY
    )
    downstream = (
        "BRCE_REQUIRED"
        if standing is Standing.ALIVE and action.operation in CONSEQUENTIAL_OPERATIONS
        else "NONE"
    )

    receipt = HiltReceipt(
        schema=_RECEIPT_SCHEMA,
        case_id=case.case_id,
        semantic_subject_id=case.semantic_subject_id,
        subject_bindings=tuple(sorted(x.identity for x in case.subjects)),
        action_id=action.action_id,
        actor_id=action.actor_id,
        standing=standing,
        claim_ceiling=_CLAIM_CEILING,
        authority="NONE",
        accountability_principal=case.actor.accountability_principal,
        admitted_agency=admitted_agency.label if admitted_agency is not None else None,
        operation=action.operation.value,
        downstream=downstream,
        responsibility_claim=responsibility_claim,
        refusals=tuple(sorted(set(refusals))),
        receipt_digest="sha256:" + "0" * 64,
    )
    return replace(
        receipt, receipt_digest=_canonical_digest(receipt.canonical_payload())
    )


def _agency(value: str | int) -> AgencyLevel:
    if isinstance(value, int):
        return AgencyLevel(value)
    labels = {item.label: item for item in AgencyLevel}
    try:
        return labels[value]
    except KeyError as exc:
        raise ValueError(f"unknown agency level {value}") from exc


def load_case(path: str | Path) -> HiltCase:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return HiltCase(
        case_id=raw["case_id"],
        semantic_subject_id=raw["semantic_subject_id"],
        subjects=tuple(
            SubjectBinding(x["repository"], x["subject_sha"]) for x in raw["subjects"]
        ),
        actor=ActorContract(
            actor_id=raw["actor"]["actor_id"],
            actor_kind=ActorKind(raw["actor"]["actor_kind"]),
            accountability_principal=raw["actor"]["accountability_principal"],
        ),
        artifacts=tuple(
            ArtifactStanding(
                artifact_id=x["artifact_id"],
                state=ArtifactState(x["state"]),
                provenance=x["provenance"],
            )
            for x in raw.get("artifacts", [])
        ),
        agency_leases=tuple(
            AgencyLease(
                capability=x["capability"],
                context=x["context"],
                max_level=_agency(x["max_level"]),
                evidence_id=x["evidence_id"],
            )
            for x in raw.get("agency_leases", [])
        ),
        permissions=tuple(
            ContextPermission(
                context=x["context"],
                operations=tuple(Operation(v) for v in x["operations"]),
                read_artifacts=tuple(x.get("read_artifacts", [])),
                disclose_artifacts=tuple(x.get("disclose_artifacts", [])),
                surfaces=tuple(x.get("surfaces", [])),
            )
            for x in raw.get("permissions", [])
        ),
        relations=tuple(
            RelationContract(
                relation_id=x["relation_id"],
                relation_kind=x["relation_kind"],
                allowed_operations=tuple(
                    Operation(v) for v in x["allowed_operations"]
                ),
            )
            for x in raw.get("relations", [])
        ),
        human_reservations=tuple(
            HumanReservation(
                capability=x["capability"],
                context=x["context"],
                operation=Operation(x["operation"]),
                reservation_id=x["reservation_id"],
                surface=x.get("surface"),
            )
            for x in raw.get("human_reservations", [])
        ),
        action=ActionCandidate(
            action_id=raw["action"]["action_id"],
            actor_id=raw["action"]["actor_id"],
            capability=raw["action"]["capability"],
            context=raw["action"]["context"],
            operation=Operation(raw["action"]["operation"]),
            requested_agency=_agency(raw["action"]["requested_agency"]),
            interaction_mode=InteractionMode(raw["action"]["interaction_mode"]),
            consequence_class=raw["action"]["consequence_class"],
            artifact_id=raw["action"].get("artifact_id"),
            relation_id=raw["action"].get("relation_id"),
            surface=raw["action"].get("surface"),
        ),
    )


def receipt_dict(case: HiltCase) -> dict[str, Any]:
    receipt = evaluate(case)
    data = asdict(receipt)
    data["standing"] = receipt.standing.value
    return data


def run(path: str) -> tuple[dict[str, Any], int]:
    try:
        case = load_case(path)
    except (ValueError, KeyError, TypeError) as exc:
        message = str(exc).replace("\n", " ").strip() or type(exc).__name__
        if isinstance(exc, KeyError):
            message = f"missing field {message}"
        return (
            {
                "schema": _INADMISSIBLE_SCHEMA,
                "standing": "REFUSED",
                "authority": "NONE",
                "refusals": [f"REFUSED:INADMISSIBLE_CASE:{message}"],
            },
            2,
        )
    data = receipt_dict(case)
    return data, 0 if data["standing"] == "ALIVE" else 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a HILT institutional-semantics admission case"
    )
    parser.add_argument("case")
    args = parser.parse_args()
    data, code = run(args.case)
    print(json.dumps(data, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
