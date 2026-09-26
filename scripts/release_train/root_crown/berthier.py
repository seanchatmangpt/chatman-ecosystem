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


def split_ref(ref: str) -> tuple[str, str]:
    """RFC-0005 §10: ``RFC-0005§7`` -> (``RFC-0005``, ``§7``); an unqualified ``§n`` binds RFC-0004."""
    head, sep, tail = ref.partition("§")
    if sep and head:
        return head, f"§{tail}"
    return PREMISE, ref


def premise_key(section: str, rfc: str = PREMISE) -> str:
    return f"premise:{rfc}#{section}"


def premise_ref_key(ref: str) -> str:
    rfc, section = split_ref(ref)
    return premise_key(section, rfc)


def premise_set_digest(texts: Mapping[str, str]) -> str:
    """RFC-0005 §10.3: the premise digest is over the mapping RFC id -> source digest."""
    return digest({rfc: sha256_bytes(text.encode("utf-8")) for rfc, text in sorted(texts.items())})


def req_key(rid: str) -> str:
    return f"req:{rid}"


def packet_key(owner: str) -> str:
    return f"packet:{owner}"


def artifact_key(locator: str) -> str:
    return f"artifact:{locator}"


def source_digests(rfc_text: str | Mapping[str, str], reqs: Iterable[Requirement]) -> dict[str, str]:
    """Digests of the strategic sources: premise sections and requirement rows.

    ``rfc_text`` is one premise (RFC-0004) or a premise set ``{rfc id: text}`` (RFC-0005 §10).
    A single premise yields exactly the keys and digests it yielded before premise sets.
    """
    texts = {PREMISE: rfc_text} if isinstance(rfc_text, str) else dict(rfc_text)
    out = {
        premise_key(k, rfc): sha256_bytes(v.encode("utf-8"))
        for rfc, text in sorted(texts.items())
        for k, v in premise_sections(text).items()
    }
    for req in reqs:
        out[req_key(req.id)] = digest(req.row())
    return out


def edge_specs(reqs: Iterable[Requirement]) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    for req in reqs:
        for ref in req.premise_refs:
            specs.append((premise_ref_key(ref), req_key(req.id)))
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
    return [premise_ref_key(ref) for ref in req.premise_refs]


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
