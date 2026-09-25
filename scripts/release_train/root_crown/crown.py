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
    MODES,
    SCHEMA_RECEIPT,
    SCHEMA_RECEIPT_V2,
    SCHEMA_RECEIPTS,
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
    """v1 and v2 receipts: the digest recomputes over every field but itself."""
    return (
        isinstance(receipt, dict)
        and receipt.get("schema", SCHEMA_RECEIPT) in SCHEMA_RECEIPTS
        and receipt.get("receipt_digest") == receipt_digest_of(receipt)
    )


def _contained(label: str, fn: Any, *args: Any) -> tuple[Any, str | None]:
    """RFC §39: an evaluator crash is a typed REFUSED VERIFIER_CRASHED, never an escape."""
    try:
        return fn(*args), None
    except Exception as exc:  # noqa: BLE001 — containment is the point
        return None, f"{label}:{type(exc).__name__}:{exc}"


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
    mode: str = "PRE_TAG",
    policy_root: Path | None = None,
) -> Verdict:
    """Evaluate one release tree at ``crown_sha`` (the core receipt, schema v1).

    ``mode`` PRE_TAG binds the observed root head to crown_sha (``CROWN_SHA_SPLIT``);
    POST_TAG does not (after the tag, the observed head legitimately moves on and the
    tag binding is the post-tag evaluator supplied by ``posttag``).

    The terminality policy (``policy.py``) is admitted as a whole before any requirement is
    evaluated: a missing policy, a coverage gap, an ungrounded relaxation or acceptance drift
    is a global refusal even for requirements whose evaluator never consults the policy.
    ``policy_root`` overrides the committed policy directory (tests, mutants).
    """
    if mode not in MODES:
        raise ValueError(f"mode {mode!r} not in {MODES}")
    registry = EVALUATORS if evaluators is None else evaluators
    inputs = projector.load_inputs(release_dir)
    reqs = inputs.requirements
    refusals: list[str] = []
    refusals += validate_requirements(inputs.requirements_doc, inputs.pins, inputs.rfc_text, registry.keys())
    drift, crashed = _contained("projector.check", projector.check, release_dir)
    refusals += [f"REFUSED:VERIFIER_CRASHED:{crashed}"] if crashed else drift

    previous_digest = None
    if previous is not None:
        if not verify_receipt(previous) or previous.get("release") != release_dir.name:
            refusals.append("REFUSED:RECEIPT_CHAIN_BROKEN:previous receipt digest does not recompute")
        previous_digest = previous.get("receipt_digest")

    root_repo = inputs.pins["root_repository"]
    root_obs = observations.get("repos", {}).get(root_repo, {})
    if mode == "PRE_TAG" and root_obs.get("head_sha") and root_obs["head_sha"] != crown_sha:
        refusals.append(f"REFUSED:CROWN_SHA_SPLIT:observed={root_obs['head_sha']}:crown={crown_sha}")

    ctx = Context(
        root=root,
        release_dir=release_dir,
        observations=observations,
        crown_sha=crown_sha,
        inputs=inputs,
        **({} if policy_root is None else {"policy_root": policy_root}),
    )
    refusals += ctx.policy_refusals()
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
            result, crashed = _contained(req.id, fn, req, ctx)
            state = REFUSED("VERIFIER_CRASHED", crashed) if crashed else result
        if state.state in {"BLOCKED", "UNKNOWN"} and (not state.code or state.code not in FAILURE_CLASS):
            state = REFUSED("BLOCKED_WITHOUT_TYPE", f"{req.id}:{state.code}")
        if state.state == "PASS" and req.id in impacts:
            moved = impacts[req.id]
            new_heads = {heads.get(r) for r in moved}
            bound = state.binding
            # Survives a moved head only when its evaluated subject is the new head, or when
            # it is IN_TREE_DERIVED from the crown's own tree at crown_sha. A receipt (local,
            # remote or operator-local) is never exempted by the crown commit.
            in_tree = bound is not None and bound.kind == "IN_TREE_DERIVED" and state.subject_sha == crown_sha
            if state.subject_sha not in new_heads and not in_tree:
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


def _typed(refusal: str) -> dict[str, Any]:
    code = code_of(refusal)
    cls, term = FAILURE_CLASS.get(code, (None, None))
    return {"refusal": refusal, "code": code, "failure_class": cls, "broken_term": term}


def _worst(*standings: str) -> str:
    for s in ("REFUSED", "BLOCKED"):
        if s in standings:
            return s
    return "ALIVE"


def attest(
    release_dir: Path,
    observations: dict[str, Any] | None,
    previous: dict[str, Any] | None,
    crown_sha: str,
    *,
    root: Path = Path("."),
    requested_mode: str = "auto",
    head_sha: str | None = None,
    subject_dir: Path | None = None,
    hardening_dir: Path | None = None,
    tag_observation: dict[str, Any] | None = None,
    ancestry: set[str] | None = None,
    evaluators: dict[str, Evaluator] | None = None,
) -> Verdict:
    """Receipt schema v2: mode dispatch over PRE_TAG (the tagging crown) and POST_TAG.

    PRE_TAG: the v1 evaluation of ``crown_sha`` wrapped in the v2 envelope (the chain
    parent is ``previous``). POST_TAG: ``historical`` (exact replay of the tag-named
    receipt + hardened ceiling) and ``current`` (the attested head, post-tag tag binding,
    frozen payload) are reported separately; the chain parent is read from git
    (``hardening/receipts/chain.json``), ``previous`` is ignored. The overall standing is
    the worst of the sections; history is never refused because the head drifted.
    """
    from . import chain, posttag

    hardening = hardening_dir if hardening_dir is not None else release_dir / "hardening"
    record = posttag.load_record(hardening)
    tags = posttag.tag_sources(observations, tag_observation)
    mode, mode_blockers = posttag.select_mode(requested_mode, record, tags, head_sha or crown_sha)
    attested = head_sha or crown_sha
    historical: dict[str, Any] | None = None
    subject_refusals: list[str] = []
    subject_blockers: list[str] = list(mode_blockers)
    chain_refusals: list[str] = []
    chain_blockers: list[str] = []
    if mode == "PRE_TAG":
        verdict = evaluate(
            release_dir, observations or {}, previous, crown_sha, root=root, evaluators=evaluators, mode="PRE_TAG"
        )
        current = {
            "standing": verdict.standing,
            "refusals": list(verdict.refusals),
            "drift": {},
            "receipt": verdict.receipt,
        }
        parent_digest = verdict.receipt["previous_receipt_digest"]
        genesis = previous is None
    else:
        if record is not None:
            subject_refusals, blockers = posttag.verify_tag_subject(record, hardening, tags)
            subject_blockers += blockers
            historical = posttag.historical_standing(record, hardening, subject_dir, root)
        # Without a tag record there is no post-tag chain to read (TAG_UNRECORDED is the blocker).
        link = chain.parent_of(hardening, ancestry) if record is not None else chain.ChainResult(None)
        chain_refusals, chain_blockers = link.refusals, link.blockers
        current = posttag.current_conformance(
            release_dir,
            observations,
            link.parent,
            crown_sha,
            record,
            tags,
            root=root,
            evaluators=evaluators,
            hardening_dir=hardening,
        )
        parent_digest = link.parent_digest
        genesis = False
    core = current["receipt"]
    refusals = sorted(
        set(current["refusals"] + subject_refusals + chain_refusals + (historical["refusals"] if historical else []))
    )
    blockers = sorted(set(subject_blockers + chain_blockers + (historical["blockers"] if historical else [])))
    sections = [current["standing"], "BLOCKED" if blockers else "ALIVE", "REFUSED" if refusals else "ALIVE"]
    if historical is not None:
        sections.append(historical["standing"])
    elif mode == "POST_TAG":
        sections.append("BLOCKED")
    standing = _worst(*sections)
    remaining = list(core["remaining"]) + [
        {"id": f"{mode}:{code_of(b)}", "term": None, "state": "BLOCKED", "detail": b, "subject_sha": attested}
        | {k: v for k, v in _typed(b).items() if k in ("code", "failure_class", "broken_term")}
        for b in blockers
    ]
    receipt: dict[str, Any] = {
        "schema": SCHEMA_RECEIPT_V2,
        "release": release_dir.name,
        "mode": mode,
        "subject": posttag.subject_of(record, release_dir.name, crown_sha if mode == "PRE_TAG" else None),
        "attestation_head_sha": attested,
        "crown_sha": crown_sha if mode == "PRE_TAG" else (record or {}).get("subject", {}).get("commit_sha"),
        "root_repository": core["root_repository"],
        "evaluated_at": core["evaluated_at"],
        "observations_digest": core["observations_digest"],
        "observation_authority": core["observation_authority"],
        "previous_receipt_digest": parent_digest,
        "genesis": genesis,
        "standing": standing,
        "theorem": core["theorem"],
        "terms": core["terms"],
        "requirements": core["requirements"],
        "refusals": refusals,
        "global_refusals": [_typed(r) for r in refusals],
        "blockers": [_typed(b) for b in blockers],
        "remaining": remaining,
        "heads": core["heads"],
        "historical": historical,
        "current": {
            "standing": current["standing"],
            "refusals": current["refusals"],
            "drift": current["drift"],
            "core_receipt_digest": core["receipt_digest"],
            "core": core,
        },
        "authority": "NONE",
    }
    receipt["receipt_digest"] = receipt_digest_of(receipt)
    return Verdict(
        standing, {t: v["state"] for t, v in core["terms"].items()}, tuple(refusals), tuple(remaining), receipt
    )
