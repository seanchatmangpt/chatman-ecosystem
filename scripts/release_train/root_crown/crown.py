"""Root crown: RELEASE_26.9.25 = C ∧ A ∧ R ∧ X ∧ F ∧ M (RFC-0004 §3, §44, §55).

Term aggregation reuses ``current_frontier.obligation`` (``Obligation`` +
``require_complete``). The receipt is hash-chained (``previous_receipt_digest``) and
carries ``next_observations`` so R_t feeds O*_{t+1}: every head that moved since R_t is
a NEW_HEAD event whose cascade (``invalidation_promotion.build_cascade``) drops each
affected PASS to UNKNOWN unless its evidence is bound to the new head.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.release_train.current_frontier.obligation import Obligation, Refusal as FrontierRefusal, require_complete

from . import berthier, projector
from .evidence import DEFERRED, EVALUATORS, Context, Evaluator
from .model import (
    FAILURE_CLASS,
    SCHEMA_RECEIPT,
    TERMS,
    UNKNOWN,
    REFUSED,
    ReqState,
    Requirement,
    code_of,
    digest,
    sha256_bytes,
)
from .requirements import validate_requirements


@dataclass(frozen=True)
class Verdict:
    standing: str
    terms: dict[str, str]
    refusals: tuple[str, ...]
    remaining: tuple[dict[str, Any], ...]
    receipt: dict[str, Any]


def receipt_digest_of(receipt: dict[str, Any]) -> str:
    return digest({k: v for k, v in receipt.items() if k != "receipt_digest"})


def verify_receipt(receipt: dict[str, Any]) -> bool:
    return isinstance(receipt, dict) and receipt.get("receipt_digest") == receipt_digest_of(receipt)


def _new_head_impacts(
    reqs: tuple[Requirement, ...], previous: dict[str, Any] | None, heads: dict[str, str]
) -> dict[str, list[str]]:
    """req id -> repositories whose head moved since R_t and that the requirement depends on."""
    if not previous:
        return {}
    prior_heads = previous.get("heads", {})
    moved = sorted(r for r, sha in heads.items() if r in prior_heads and prior_heads[r] != sha)
    if not moved:
        return {}
    edges = []
    for req in reqs:
        for repo in {req.owner_repo, req.locator_repo} - {None}:
            edges.append(
                berthier.Edge(
                    berthier.Node(f"repo:{repo}"),
                    berthier.Node(f"req:{req.id}"),
                    "0" * 64,
                    "root-crown/new-head/v1",
                    "",
                )
            )
        for dep in req.depends_on:
            edges.append(
                berthier.Edge(
                    berthier.Node(f"req:{dep}"), berthier.Node(f"req:{req.id}"), "0" * 64, "root-crown/new-head/v1", ""
                )
            )
    impacted: dict[str, list[str]] = {}
    for repo in moved:
        for key in berthier.impact_of(tuple(edges), [f"repo:{repo}"]):
            if key.startswith("req:"):
                impacted.setdefault(key[4:], []).append(repo)
    return impacted


def evaluate(
    release_dir: Path,
    observations: dict[str, Any],
    previous: dict[str, Any] | None,
    crown_sha: str,
    *,
    root: Path = Path("."),
    evaluators: dict[str, Evaluator] | None = None,
) -> Verdict:
    registry = EVALUATORS if evaluators is None else evaluators
    inputs = projector.load_inputs(release_dir)
    reqs = inputs.requirements
    refusals: list[str] = []
    refusals += validate_requirements(inputs.requirements_doc, inputs.pins, inputs.rfc_text, registry.keys())
    refusals += projector.check(release_dir)

    previous_digest = None
    if previous is not None:
        if not verify_receipt(previous) or previous.get("release") != release_dir.name:
            refusals.append("REFUSED:RECEIPT_CHAIN_BROKEN:previous receipt digest does not recompute")
        previous_digest = previous.get("receipt_digest")

    root_repo = inputs.pins["root_repository"]
    root_obs = observations.get("repos", {}).get(root_repo, {})
    if root_obs.get("head_sha") and root_obs["head_sha"] != crown_sha:
        refusals.append(f"REFUSED:CROWN_SHA_SPLIT:observed={root_obs['head_sha']}:crown={crown_sha}")

    ctx = Context(root=root, release_dir=release_dir, observations=observations, crown_sha=crown_sha, inputs=inputs)
    # Heads include admitted operator-local private observations (NEW_HEAD cascade covers them too).
    heads = {repo: obs["head_sha"] for repo, obs in sorted(ctx.repos.items()) if obs.get("head_sha")}
    states: dict[str, ReqState] = {}
    ordered = [r for r in reqs if r.evidence_kind not in DEFERRED] + [r for r in reqs if r.evidence_kind in DEFERRED]
    impacts = _new_head_impacts(reqs, previous, heads)
    for req in ordered:
        fn = registry.get(req.evidence_kind)
        if fn is None:
            state = REFUSED("UNKNOWN_EVIDENCE_KIND", req.evidence_kind)
        else:
            ctx.extra["states"] = states
            state = fn(req, ctx)
        if state.state in {"BLOCKED", "UNKNOWN"} and (not state.code or state.code not in FAILURE_CLASS):
            state = REFUSED("BLOCKED_WITHOUT_TYPE", f"{req.id}:{state.code}")
        if state.state == "PASS" and req.id in impacts:
            moved = impacts[req.id]
            new_heads = {heads.get(r) for r in moved}
            if state.subject_sha not in new_heads and not (state.subject_sha == crown_sha):
                state = UNKNOWN(
                    "NEW_HEAD_UNEVIDENCED",
                    f"heads moved: {','.join(moved)}; evidence bound to {state.subject_sha}",
                    state.subject_sha,
                )
        states[req.id] = state

    term_states: dict[str, dict[str, Any]] = {}
    for term in TERMS:
        members = [r for r in reqs if r.term == term]
        obligations = tuple(Obligation(r.id, "REPOSITORY", r.required) for r in members)
        coverage = {r.id: states[r.id].state for r in members}
        try:
            require_complete(coverage, obligations)
            term_state, detail = "PASS", ""
        except FrontierRefusal as exc:
            term_state = "REFUSED" if any(coverage[r.id] == "REFUSED" for r in members if r.required) else "BLOCKED"
            detail = str(exc)
        term_states[term] = {"state": term_state, "requirements": sorted(coverage), "detail": detail}

    req_refusals = [f"REFUSED:{s.code}:{rid}" for rid, s in sorted(states.items()) if s.state == "REFUSED"]
    all_refusals = sorted(set(refusals + req_refusals))
    if all_refusals:
        standing = "REFUSED"
    elif all(t["state"] == "PASS" for t in term_states.values()):
        standing = "ALIVE"
    else:
        standing = "BLOCKED"

    remaining = tuple(
        {"id": rid, "term": next(r.term for r in reqs if r.id == rid), **s.as_dict()}
        for rid, s in sorted(states.items())
        if s.state != "PASS"
    )
    global_typed = [
        {
            "refusal": r,
            "code": code_of(r),
            "failure_class": FAILURE_CLASS.get(code_of(r), (None, None))[0],
            "broken_term": FAILURE_CLASS.get(code_of(r), (None, None))[1],
        }
        for r in sorted(set(refusals))
    ]
    next_observations = {
        "repos": sorted(p["repository"] for p in inputs.pins["repos"].values()),
        "locators": sorted({next(r.evidence_locator for r in reqs if r.id == item["id"]) for item in remaining}),
        "cascade": sorted(impacts),
    }
    packets_path = release_dir / "out/packets.json"
    receipt: dict[str, Any] = {
        "schema": SCHEMA_RECEIPT,
        "release": release_dir.name,
        "crown_sha": crown_sha,
        "root_repository": root_repo,
        "evaluated_at": observations.get("observed_at"),
        "observations_digest": digest(observations),
        "observation_authority": observations.get("authority"),
        "previous_receipt_digest": previous_digest,
        "genesis": previous is None,
        "standing": standing,
        "theorem": "RELEASE = C AND A AND R AND X AND F AND M",
        "terms": term_states,
        "requirements": {rid: s.as_dict() for rid, s in sorted(states.items())},
        "refusals": all_refusals,
        "global_refusals": global_typed,
        "remaining": list(remaining),
        "heads": heads,
        "next_observations": next_observations,
        "input_digests": inputs.input_digests,
        "packets_digest": sha256_bytes(packets_path.read_bytes()) if packets_path.is_file() else None,
        "berthier_digest": sha256_bytes((release_dir / "berthier.json").read_bytes())
        if (release_dir / "berthier.json").is_file()
        else None,
        "authority": "NONE",
    }
    receipt["receipt_digest"] = receipt_digest_of(receipt)
    return Verdict(
        standing,
        {t: v["state"] for t, v in term_states.items()},
        tuple(all_refusals),
        remaining,
        receipt,
    )
