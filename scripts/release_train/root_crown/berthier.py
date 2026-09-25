"""Berthier recompile court (RFC-0004 §8, §9).

Graph: ``premise:RFC-0004#§n`` -> ``req:<id>`` -> {``proj:<path>``, ``packet:<owner>``,
``artifact:<locator>``}. Every edge records ``compiled_from`` (the producer digest at
projection time). The dependent-set engine is reused unchanged from
``invalidation_promotion``: ``DependencyGraph`` (cycle refusal) and ``build_cascade``
(SCHEMA_CHANGE -> SCHEMA_DRIFT impacts); renewal reuses ``renew_binding`` so a
regenerated edge must carry a real delta (``NO_RENEWAL_DELTA``).

The court never writes. Packets are Berthier work identity (SELECT/DECOMPOSE/ROUTE),
never actuation: every packet authority ceiling is CONSTRUCT.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
from typing import Any, Iterable, Mapping

from scripts.release_train.invalidation_promotion.authority import require_authority
from scripts.release_train.invalidation_promotion.cascade import build_cascade
from scripts.release_train.invalidation_promotion.graph import DependencyGraph
from scripts.release_train.invalidation_promotion.renewal import renew_binding
from scripts.release_train.invalidation_promotion.subject import Refusal

from .model import Requirement, digest, sha256_bytes
from .requirements import premise_sections

PREMISE = "RFC-0004"
SCHEMA = "root-crown/berthier-edge/v1"
PROJECTED_OUTPUTS = ("out/packets.json", "out/requirements.ttl")
UNOBSERVED = "UNOBSERVED"
PACKET_AUTHORITY = "CONSTRUCT"
CAMPAIGN_SCHEMA = "https://chatman.dev/root-crown/berthier-campaign/v1"
CAMPAIGN_ALLOWED_ACTIONS = frozenset({"OBSERVE", "SELECT", "DECOMPOSE", "ROUTE", "CONSTRUCT", "VERIFY"})


@dataclass(frozen=True, slots=True)
class Node:
    key: str

    @property
    def repo(self) -> str:
        # renew_binding refuses a producer from a different namespace (FOREIGN_PRODUCER_RENEWAL).
        return self.key.split(":", 1)[0]


@dataclass(frozen=True, slots=True)
class Edge:
    producer: Node
    consumer: Node
    receipt: str  # compiled_from: producer digest at projection time
    schema: str
    consumer_digest: str

    @property
    def compiled_from(self) -> str:
        return self.receipt

    def as_dict(self) -> dict[str, str]:
        return {
            "producer": self.producer.key,
            "consumer": self.consumer.key,
            "compiled_from": self.receipt,
            "consumer_digest": self.consumer_digest,
        }


@dataclass(frozen=True, slots=True)
class Event:
    producer: Node
    kind: str


@dataclass(frozen=True, slots=True)
class BerthierVerdict:
    standing: str
    refusals: tuple[str, ...]
    stale: tuple[str, ...]
    impact: tuple[str, ...]
    required_owners: tuple[str, ...]


def premise_key(section: str) -> str:
    return f"premise:{PREMISE}#{section}"


def req_key(rid: str) -> str:
    return f"req:{rid}"


def packet_key(owner: str) -> str:
    return f"packet:{owner}"


def artifact_key(locator: str) -> str:
    return f"artifact:{locator}"


def source_digests(rfc_text: str, reqs: Iterable[Requirement]) -> dict[str, str]:
    """Digests of the strategic sources: premise sections and requirement rows."""
    out = {premise_key(k): sha256_bytes(v.encode("utf-8")) for k, v in premise_sections(rfc_text).items()}
    for req in reqs:
        out[req_key(req.id)] = digest(req.row())
    return out


def edge_specs(reqs: Iterable[Requirement]) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    for req in reqs:
        for ref in req.premise_refs:
            specs.append((premise_key(ref), req_key(req.id)))
        for out in PROJECTED_OUTPUTS:
            specs.append((req_key(req.id), f"proj:{out}"))
        specs.append((req_key(req.id), packet_key(req.owner_repo)))
        specs.append((req_key(req.id), artifact_key(req.evidence_locator)))
    return sorted(set(specs))


def build_edges(
    reqs: Iterable[Requirement],
    digests: dict[str, str],
    consumer_digests: dict[str, str],
) -> tuple[Edge, ...]:
    edges = []
    for producer, consumer in edge_specs(reqs):
        edges.append(
            Edge(
                Node(producer),
                Node(consumer),
                digests.get(producer, UNOBSERVED),
                SCHEMA,
                consumer_digests.get(consumer, UNOBSERVED),
            )
        )
    DependencyGraph(edges)  # REFUSED[DEPENDENCY_CYCLE] if the graph is not a DAG
    return tuple(edges)


def renew_projection(edge: Edge, new_producer_digest: str, new_consumer_digest: str) -> Edge:
    """Regenerate one edge; refuses REFUSED[NO_RENEWAL_DELTA] when nothing changed."""
    renewed = renew_binding(edge, producer=edge.producer, receipt=new_producer_digest)
    return replace(renewed, consumer_digest=new_consumer_digest)


def edges_from_json(rows: Iterable[dict[str, Any]]) -> tuple[Edge, ...]:
    return tuple(
        Edge(Node(r["producer"]), Node(r["consumer"]), r["compiled_from"], SCHEMA, r.get("consumer_digest", UNOBSERVED))
        for r in rows
    )


def delta(baseline: dict[str, str], current: dict[str, str]) -> tuple[str, ...]:
    """Source nodes whose digest differs from the baseline compile (the strategic delta)."""
    return tuple(sorted(k for k, v in current.items() if baseline.get(k) != v))


def impact_of(edges: tuple[Edge, ...], changed: Iterable[str]) -> tuple[str, ...]:
    impacted: set[str] = set()
    for key in changed:
        impacted.add(key)
        for impact in build_cascade(edges, Event(Node(key), "SCHEMA_CHANGE")):
            impacted.add(impact.subject)
    return tuple(sorted(impacted))


def owners_of(impact: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(k[len("packet:") :] for k in impact if k.startswith("packet:")))


def packets(
    reqs: tuple[Requirement, ...],
    impact: tuple[str, ...],
    changed: tuple[str, ...],
    pins: dict[str, Any],
) -> list[dict[str, Any]]:
    """RFC-0004 §8 packets (plus the Berthier-RFC fields), one per impacted owner repository."""
    by_repo = {e["repository"]: e for e in pins.get("repos", {}).values()}
    impacted_reqs = {k[len("req:") :] for k in impact if k.startswith("req:")}
    out = []
    for owner in owners_of(impact):
        mine = [r for r in reqs if r.owner_repo == owner and r.id in impacted_reqs]
        pin = by_repo.get(owner, {})
        out.append(
            {
                "subject": {"repository": owner, "ref": pin.get("ref"), "sha": pin.get("sha")},
                "action": "CONSTRUCT evidence satisfying the listed requirements; no actuation",
                "acceptance": [f"{r.id}: {r.acceptance}" for r in mine],
                "falsifier": [r.id for r in mine if r.kind == "FALSIFIER"]
                or ["root crown refuses the requirement state"],
                "dependencies": sorted({d for r in mine for d in r.depends_on}),
                "authority": PACKET_AUTHORITY,
                "authority_ceiling": PACKET_AUTHORITY,
                "verification": sorted({f"{r.evidence_kind}@{r.evidence_locator}" for r in mine}),
                "receipt_requirement": "root-crown receipt with every listed requirement PASS on a merged SHA",
                "strategic_delta": sorted(
                    k for k in changed if any(k == req_key(r.id) or k in _premise_nodes(r) for r in mine)
                ),
                "exact_subject": f"{owner}@{pin.get('sha')}",
                "changed_edge": sorted(
                    f"{p}->{req_key(r.id)}" for r in mine for p in _premise_nodes(r) if p in changed
                ),
                "preserved_invariants": ["authority ceiling CONSTRUCT", "SELECT != DECOMPOSE != DO"],
                "required_capability": sorted(r.id for r in mine),
                "successor": None,
                "mode": "normal",
            }
        )
    return out


def _premise_nodes(req: Requirement) -> list[str]:
    return [premise_key(ref) for ref in req.premise_refs]


def judge(
    edges: tuple[Edge, ...],
    current: dict[str, str],
    declared_packets: list[dict[str, Any]],
    baseline: dict[str, str],
    observed_artifacts: dict[str, str] | None = None,
    live_runtime_failures: Iterable[str] = (),
) -> BerthierVerdict:
    """Judge the committed Berthier graph against current source digests and observations.

    ``current`` holds digests for every node the court can recompute (sources and
    projections). ``baseline`` is the source digest set of the previous compile; the
    committed packets must cover exactly the owners impacted by baseline -> compiled.
    """
    refusals: list[str] = []
    try:
        DependencyGraph(edges)
    except Refusal as exc:
        return BerthierVerdict("REFUSED", (f"REFUSED:DEPENDENCY_CYCLE:{exc}",), (), (), ())

    stale_roots = []
    for edge in edges:
        producer = edge.producer.key
        if producer.startswith("premise:") and producer not in current:
            refusals.append(f"REFUSED:PREMISE_UNBOUND:{producer}")
            continue
        if producer in current and current[producer] != edge.compiled_from:
            stale_roots.append(producer)
    stale = impact_of(edges, sorted(set(stale_roots))) if stale_roots else ()
    stale_consumers = tuple(k for k in stale if k not in set(stale_roots))
    for key in stale_consumers:
        refusals.append(f"REFUSED:STALE_PROJECTION:{key}")
    for edge in edges:
        consumer = edge.consumer.key
        if consumer.startswith("proj:") and consumer in current and edge.consumer_digest != current[consumer]:
            if consumer not in stale_consumers:
                refusals.append(f"REFUSED:STALE_PROJECTION:{consumer}")
        if consumer.startswith("artifact:") and observed_artifacts is not None:
            seen = observed_artifacts.get(consumer)
            if edge.consumer_digest != UNOBSERVED and seen is not None and seen != edge.consumer_digest:
                refusals.append(f"REFUSED:ARTIFACT_DIGEST_MISMATCH:{consumer}")

    compiled = {e.producer.key: e.compiled_from for e in edges if e.producer.key.startswith(("premise:", "req:"))}
    changed = delta(baseline, compiled)
    impact = impact_of(edges, changed)
    required = set(owners_of(impact))
    declared = {p.get("subject", {}).get("repository") for p in declared_packets}
    for owner in sorted(required - declared):
        refusals.append(f"REFUSED:OMITTED_SUBJECT:{owner}")
    for owner in sorted(d for d in declared - required if d is not None):
        refusals.append(f"REFUSED:UNEVIDENCED_WORK:{owner}")
    failures = set(live_runtime_failures)
    for packet in declared_packets:
        owner = packet.get("subject", {}).get("repository")
        try:
            require_authority(packet.get("authority_ceiling", "UNKNOWN"))
        except Refusal as exc:
            refusals.append(f"REFUSED:AUTHORITY_INCREASE:{owner}:{exc}")
        if packet.get("mode") == "break_glass" and owner not in failures:
            refusals.append(f"REFUSED:BREAK_GLASS_AS_NORMAL:{owner}")
    refusals = sorted(set(refusals))
    return BerthierVerdict(
        "REFUSED" if refusals else "ALIVE",
        tuple(refusals),
        stale_consumers,
        impact,
        tuple(sorted(required)),
    )


def graph_document(edges: tuple[Edge, ...], baseline: dict[str, str], compiled: dict[str, str]) -> dict[str, Any]:
    return {
        "schema": "https://chatman.dev/root-crown/berthier/v1",
        "premise": PREMISE,
        "baseline": dict(sorted(baseline.items())),
        "compiled": dict(sorted(compiled.items())),
        "edges": [e.as_dict() for e in edges],
    }


# --- RFC-native campaign compiler ----------------------------------------------------
#
# GRASP-style "generate / branch / judge" is represented here as typed strategic
# compilation, not as an LLM-agent topology:
#
#   Doctrine (global structural law)
#       -> StrategyPartition[] (isolated local premise snapshots)
#       -> CampaignCandidate[] (bounded SPG-like candidate IR)
#       -> CampaignVerdict[] (machine court)
#       -> SELECT among ALIVE candidates only.
#
# Berthier remains non-actuating. Candidate actions are limited to the planning /
# construction vocabulary below; DO and other consequential verbs are refused.
# The BRCE boundary remains the only downstream route to consequential actuation.


@dataclass(frozen=True, slots=True)
class Doctrine:
    subject: str
    premise_digests: tuple[tuple[str, str], ...]
    invariants: tuple[str, ...]
    required_capabilities: tuple[str, ...] = ()
    authority_ceiling: str = PACKET_AUTHORITY

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "premise_digests": dict(sorted(self.premise_digests)),
            "invariants": list(sorted(self.invariants)),
            "required_capabilities": list(sorted(self.required_capabilities)),
            "authority_ceiling": self.authority_ceiling,
        }

    @property
    def compiled_digest(self) -> str:
        return digest(self.as_dict())


@dataclass(frozen=True, slots=True)
class StrategyPartition:
    strategy_id: str
    strategy: str
    doctrine_digest: str
    local_premise_digests: tuple[tuple[str, str], ...]
    local_constraints: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy": self.strategy,
            "doctrine_digest": self.doctrine_digest,
            "local_premise_digests": dict(sorted(self.local_premise_digests)),
            "local_constraints": list(sorted(self.local_constraints)),
        }

    @property
    def partition_digest(self) -> str:
        return digest(self.as_dict())


@dataclass(frozen=True, slots=True)
class CampaignCandidate:
    candidate_id: str
    subject: str
    strategy_id: str
    doctrine_digest: str
    partition_digest: str
    invariants: tuple[str, ...]
    capabilities: tuple[str, ...]
    actions: tuple[str, ...]
    falsifier: str
    objectives: tuple[tuple[str, float], ...]
    authority_ceiling: str = PACKET_AUTHORITY
    observed_partition_digests: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "subject": self.subject,
            "strategy_id": self.strategy_id,
            "doctrine_digest": self.doctrine_digest,
            "partition_digest": self.partition_digest,
            "invariants": list(sorted(self.invariants)),
            "capabilities": list(sorted(self.capabilities)),
            "actions": list(self.actions),
            "falsifier": self.falsifier,
            "objectives": dict(sorted(self.objectives)),
            "authority_ceiling": self.authority_ceiling,
            "observed_partition_digests": list(sorted(self.observed_partition_digests)),
        }

    @property
    def candidate_digest(self) -> str:
        return digest(self.as_dict())

    def objective(self, name: str) -> float | None:
        return dict(self.objectives).get(name)


@dataclass(frozen=True, slots=True)
class CampaignVerdict:
    standing: str
    candidate_id: str
    refusals: tuple[str, ...]
    objectives: tuple[tuple[str, float], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "standing": self.standing,
            "candidate_id": self.candidate_id,
            "refusals": list(self.refusals),
            "objectives": dict(sorted(self.objectives)),
        }


@dataclass(frozen=True, slots=True)
class CampaignSelection:
    candidate_id: str
    candidate_digest: str
    objective: str
    value: float
    maximize: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_digest": self.candidate_digest,
            "objective": self.objective,
            "value": self.value,
            "maximize": self.maximize,
        }


def _campaign_refusal(code: str, detail: str) -> str:
    return f"REFUSED:{code}:{detail}"


def compile_doctrine(
    subject: str,
    premise_digests: Mapping[str, str],
    invariants: Iterable[str],
    required_capabilities: Iterable[str] = (),
    authority_ceiling: str = PACKET_AUTHORITY,
) -> Doctrine:
    """Compile immutable global campaign law.

    Global premises belong here. Instance/strategy-local observations belong in
    StrategyPartition so a local change invalidates only the branches that read it.
    """
    subject = subject.strip()
    premise_rows = tuple(sorted((str(k), str(v)) for k, v in premise_digests.items()))
    invariant_rows = tuple(sorted({str(v).strip() for v in invariants if str(v).strip()}))
    capabilities = tuple(sorted({str(v).strip() for v in required_capabilities if str(v).strip()}))
    if not subject or not premise_rows or not invariant_rows:
        raise Refusal("REFUSED[STRATEGY_UNBOUNDED]")
    try:
        require_authority(authority_ceiling)
    except Refusal as exc:
        raise Refusal("REFUSED[AUTHORITY_INCREASE]") from exc
    if authority_ceiling != PACKET_AUTHORITY:
        raise Refusal("REFUSED[AUTHORITY_INCREASE]")
    return Doctrine(subject, premise_rows, invariant_rows, capabilities, authority_ceiling)


def partition_strategy(
    doctrine: Doctrine,
    strategy_id: str,
    strategy: str,
    local_premise_digests: Mapping[str, str],
    local_constraints: Iterable[str] = (),
) -> StrategyPartition:
    """Create a sealed strategy partition.

    The partition carries only its own local premise snapshot plus the immutable
    doctrine digest. It has no field through which another strategy's generated
    state can be inherited.
    """
    strategy_id = strategy_id.strip()
    strategy = strategy.strip()
    local = tuple(sorted((str(k), str(v)) for k, v in local_premise_digests.items()))
    constraints = tuple(sorted({str(v).strip() for v in local_constraints if str(v).strip()}))
    if not strategy_id or not strategy or not local:
        raise Refusal("REFUSED[STRATEGY_UNBOUNDED]")
    return StrategyPartition(strategy_id, strategy, doctrine.compiled_digest, local, constraints)


def candidate_from_partition(
    doctrine: Doctrine,
    partition: StrategyPartition,
    candidate_id: str,
    falsifier: str,
    objectives: Mapping[str, float],
    *,
    invariants: Iterable[str] | None = None,
    capabilities: Iterable[str] | None = None,
    actions: Iterable[str] = ("SELECT", "DECOMPOSE", "ROUTE", "CONSTRUCT"),
    authority_ceiling: str = PACKET_AUTHORITY,
    observed_partition_digests: Iterable[str] | None = None,
) -> CampaignCandidate:
    """Manufacture a bounded candidate IR from one sealed partition."""
    inv = doctrine.invariants if invariants is None else tuple(sorted({str(v) for v in invariants}))
    caps = (
        doctrine.required_capabilities
        if capabilities is None
        else tuple(sorted({str(v) for v in capabilities}))
    )
    obs = (
        (partition.partition_digest,)
        if observed_partition_digests is None
        else tuple(sorted({str(v) for v in observed_partition_digests}))
    )
    return CampaignCandidate(
        candidate_id=candidate_id.strip(),
        subject=doctrine.subject,
        strategy_id=partition.strategy_id,
        doctrine_digest=doctrine.compiled_digest,
        partition_digest=partition.partition_digest,
        invariants=tuple(inv),
        capabilities=tuple(caps),
        actions=tuple(str(v) for v in actions),
        falsifier=falsifier.strip(),
        objectives=tuple(sorted((str(k), float(v)) for k, v in objectives.items())),
        authority_ceiling=authority_ceiling,
        observed_partition_digests=obs,
    )


def judge_campaign_candidate(
    doctrine: Doctrine,
    partition: StrategyPartition,
    candidate: CampaignCandidate,
    current_local_premises: Mapping[str, str] | None = None,
) -> CampaignVerdict:
    """Fail-closed candidate court.

    This is the RFC-native replacement for an LLM "VerPlan" discriminator:
    doctrine preservation, provenance isolation, boundedness and authority are
    typed predicates. Quantitative objective values are used only after admission.
    """
    refusals: list[str] = []

    if partition.doctrine_digest != doctrine.compiled_digest:
        refusals.append(_campaign_refusal("CONSTRAINT_WEAKENING", "partition-doctrine-digest"))
    if candidate.doctrine_digest != doctrine.compiled_digest:
        refusals.append(_campaign_refusal("CONSTRAINT_WEAKENING", "candidate-doctrine-digest"))
    if not set(doctrine.invariants).issubset(set(candidate.invariants)):
        refusals.append(_campaign_refusal("CONSTRAINT_WEAKENING", "invariant-removed"))

    if candidate.strategy_id != partition.strategy_id:
        refusals.append(_campaign_refusal("CROSS_PARTITION_CONTAMINATION", "strategy-id"))
    if candidate.partition_digest != partition.partition_digest:
        refusals.append(_campaign_refusal("CROSS_PARTITION_CONTAMINATION", "partition-digest"))
    if set(candidate.observed_partition_digests) != {partition.partition_digest}:
        refusals.append(_campaign_refusal("CROSS_PARTITION_CONTAMINATION", "observed-partitions"))

    if current_local_premises is not None:
        for key, compiled_value in partition.local_premise_digests:
            if key not in current_local_premises:
                refusals.append(_campaign_refusal("PREMISE_UNBOUND", f"{partition.strategy_id}:{key}"))
            elif str(current_local_premises[key]) != compiled_value:
                refusals.append(_campaign_refusal("STALE_PROJECTION", f"{partition.strategy_id}:{key}"))

    if candidate.subject != doctrine.subject:
        refusals.append(_campaign_refusal("STRATEGY_UNBOUNDED", "subject"))
    if not candidate.candidate_id or not candidate.falsifier or not candidate.actions or not candidate.objectives:
        refusals.append(_campaign_refusal("STRATEGY_UNBOUNDED", "missing-bound"))
    if not set(doctrine.required_capabilities).issubset(set(candidate.capabilities)):
        refusals.append(_campaign_refusal("STRATEGY_UNBOUNDED", "capability-gap"))
    illegal_actions = sorted(set(candidate.actions) - CAMPAIGN_ALLOWED_ACTIONS)
    if illegal_actions:
        refusals.append(_campaign_refusal("STRATEGY_UNBOUNDED", "actions=" + ",".join(illegal_actions)))
    if any(not name or not math.isfinite(value) for name, value in candidate.objectives):
        refusals.append(_campaign_refusal("STRATEGY_UNBOUNDED", "objective"))

    try:
        require_authority(candidate.authority_ceiling)
    except Refusal:
        refusals.append(_campaign_refusal("AUTHORITY_INCREASE", candidate.authority_ceiling))
    if candidate.authority_ceiling != doctrine.authority_ceiling:
        refusals.append(_campaign_refusal("AUTHORITY_INCREASE", candidate.authority_ceiling))

    refusals = sorted(set(refusals))
    return CampaignVerdict(
        "REFUSED" if refusals else "ALIVE",
        candidate.candidate_id,
        tuple(refusals),
        candidate.objectives,
    )


def select_campaign(
    candidates: Iterable[CampaignCandidate],
    verdicts: Iterable[CampaignVerdict],
    objective: str,
    *,
    maximize: bool = False,
) -> CampaignSelection | None:
    """SELECT only from admitted candidates; selection never implies DO."""
    by_id = {v.candidate_id: v for v in verdicts}
    eligible: list[tuple[float, CampaignCandidate]] = []
    for candidate in candidates:
        verdict = by_id.get(candidate.candidate_id)
        value = candidate.objective(objective)
        if verdict is not None and verdict.standing == "ALIVE" and value is not None and math.isfinite(value):
            eligible.append((value, candidate))
    if not eligible:
        return None
    eligible.sort(key=lambda row: ((-row[0] if maximize else row[0]), row[1].candidate_id))
    value, candidate = eligible[0]
    return CampaignSelection(candidate.candidate_id, candidate.candidate_digest, objective, value, maximize)


def campaign_dependents(
    partitions: Iterable[StrategyPartition],
    changed_local_premises: Iterable[str],
) -> tuple[str, ...]:
    """Direct branch invalidation set for local premise changes."""
    changed = set(changed_local_premises)
    return tuple(
        sorted(
            p.strategy_id
            for p in partitions
            if changed.intersection(key for key, _ in p.local_premise_digests)
        )
    )


def _campaign_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def campaign_artifacts(
    doctrine: Doctrine,
    partitions: Iterable[StrategyPartition],
    candidates: Iterable[CampaignCandidate],
    verdicts: Iterable[CampaignVerdict],
    selection: CampaignSelection | None,
) -> dict[str, bytes]:
    """Deterministic machine artifacts for review, replay and byte-identity tests."""
    partitions = tuple(sorted(partitions, key=lambda p: p.strategy_id))
    candidates = tuple(sorted(candidates, key=lambda c: c.candidate_id))
    verdicts = tuple(sorted(verdicts, key=lambda v: v.candidate_id))
    by_strategy = {c.strategy_id: c for c in candidates}
    by_candidate = {v.candidate_id: v for v in verdicts}

    out: dict[str, bytes] = {
        "out/doctrine.json": _campaign_json_bytes(
            {"schema": CAMPAIGN_SCHEMA, "doctrine": doctrine.as_dict(), "digest": doctrine.compiled_digest}
        )
    }
    for partition in partitions:
        candidate = by_strategy.get(partition.strategy_id)
        out[f"out/strategies/{partition.strategy_id}.json"] = _campaign_json_bytes(
            {
                "schema": CAMPAIGN_SCHEMA,
                "partition": partition.as_dict(),
                "partition_digest": partition.partition_digest,
                "candidate": candidate.as_dict() if candidate else None,
            }
        )
        if candidate is not None:
            verdict = by_candidate.get(candidate.candidate_id)
            out[f"out/courts/{partition.strategy_id}.json"] = _campaign_json_bytes(
                {
                    "schema": CAMPAIGN_SCHEMA,
                    "candidate_digest": candidate.candidate_digest,
                    "verdict": verdict.as_dict() if verdict else None,
                }
            )
    out["out/campaign.json"] = _campaign_json_bytes(
        {
            "schema": CAMPAIGN_SCHEMA,
            "subject": doctrine.subject,
            "doctrine_digest": doctrine.compiled_digest,
            "strategies": [p.strategy_id for p in partitions],
            "selection": selection.as_dict() if selection else None,
            "authority_ceiling": doctrine.authority_ceiling,
            "actuation": "NONE",
            "successor_boundary": "SA2A/XaaS -> BRCE -> DO",
        }
    )
    return dict(sorted(out.items()))
